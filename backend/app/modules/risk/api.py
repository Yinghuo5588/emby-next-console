"""
风控管控 API — 客户端管控 + 并发管控 + 策略配置 + 黑名单 + 事件 + 执法日志
"""
from __future__ import annotations

import fnmatch
import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select

from app.core.dependencies import get_current_admin
from app.core.emby import emby
from app.db.models.risk import RiskActionLog, RiskEvent, RiskViolation
from app.db.models.system import SystemSetting
from app.db.session import AsyncSessionDep
from app.modules.users import service as users_service
from app.shared.responses import ApiResponse

router = APIRouter(prefix="/risk", tags=["risk"])

BLACKLIST_KEY = "client_blacklist"
POLICY_KEY = "risk_policy"
logger = logging.getLogger("app.risk")

# ── 默认策略 ──────────────────────────────────────────────

DEFAULT_POLICY: dict = {
    "client_policy": {
        "mode": "blacklist",         # blacklist / whitelist
        "fuzzy_match": False,        # 是否通配符匹配
        "action": "force_kick",      # message / stop / force_kick / ban
        "escalation": False,         # 复发加重
        "escalation_steps": ["message", "stop", "force_kick", "ban"],
        "ban_hours": 24,
        # 弹窗模板（支持 {client} {device_name} {user_name} {ban_hours} {title} 变量）
        "msg_message": "当前客户端「{client}」不在允许列表中，请更换客户端。",
        "msg_stop": "当前客户端「{client}」已被管理员禁用，播放已停止。",
        "msg_force_kick": "当前客户端「{client}」已被管理员禁用，请更换受支持客户端后重新登录。",
        "msg_ban": "您的账户已被临时封禁{ban_hours}小时，请联系管理员。",
    },
    "concurrent_policy": {
        "default_max": 2,            # 全局默认并发数
        "action": "warn",            # warn / kick_newest / kick_all
        "kick_order": "newest",      # newest / oldest
    },
}


# ── Schemas ──────────────────────────────────────────────

class BlacklistRequest(BaseModel):
    name: str


class RiskEventActionRequest(BaseModel):
    action: str  # resolve / ignore


class KickRequest(BaseModel):
    session_id: str
    device_id: str = ""
    level: str = "soft"  # soft=仅停止, hard=停止+删设备(对302有效)


class BanRequest(BaseModel):
    user_id: str
    reason: str | None = None


class PolicyUpdateRequest(BaseModel):
    client_policy: dict | None = None
    concurrent_policy: dict | None = None


# ── Internal helpers ─────────────────────────────────────

async def _get_setting(db, key: str, default: Any = None) -> Any:
    stmt = select(SystemSetting).where(SystemSetting.setting_key == key)
    result = await db.execute(stmt)
    setting = result.scalar_one_or_none()
    return setting.value_json if setting else default


async def _set_setting(db, key: str, value: Any, group: str = "risk", desc: str = "") -> None:
    stmt = select(SystemSetting).where(SystemSetting.setting_key == key)
    result = await db.execute(stmt)
    setting = result.scalar_one_or_none()
    now = datetime.now(timezone.utc)
    if setting:
        setting.value_json = value
        setting.updated_at = now
    else:
        db.add(SystemSetting(
            setting_key=key, setting_group=group,
            value_json=value, description=desc, updated_at=now,
        ))
    await db.commit()


async def _get_policy(db) -> dict:
    saved = await _get_setting(db, POLICY_KEY, {})
    # 合并默认值（新字段自动补齐）
    merged = {}
    for section, defaults in DEFAULT_POLICY.items():
        merged[section] = {**defaults, **saved.get(section, {})}
    return merged


async def _get_blacklist(db) -> list[str]:
    items = await _get_setting(db, BLACKLIST_KEY, [])
    return [str(x).strip().lower() for x in items if str(x).strip()]


async def _set_blacklist(db, items: list[str]) -> list[str]:
    normalized = sorted({x.strip().lower() for x in items if x and x.strip()})
    await _set_setting(db, BLACKLIST_KEY, normalized, group="risk", desc="客户端名单（小写去重）")
    return normalized


def _match_client(client_name: str, entries: list[str], fuzzy: bool) -> bool:
    """匹配客户端名称（精确或通配符）"""
    cn = client_name.lower()
    for entry in entries:
        if cn == entry:
            return True
        if fuzzy and fnmatch.fnmatch(cn, entry):
            return True
    return False


# ── 违规记录管理 ──────────────────────────────────────────

async def _get_or_create_violation(
    db, user_id: str, device_id: str, client: str, violation_type: str
) -> RiskViolation:
    """获取或创建违规记录"""
    stmt = (
        select(RiskViolation)
        .where(
            RiskViolation.user_id == user_id,
            RiskViolation.device_id == device_id,
            RiskViolation.violation_type == violation_type,
        )
        .order_by(RiskViolation.last_violation_at.desc())
        .limit(1)
    )
    existing = (await db.execute(stmt)).scalar_one_or_none()
    now = datetime.now(timezone.utc)

    # 如果记录存在且未过期（24小时内），累加次数
    if existing and existing.last_violation_at and (now - existing.last_violation_at).total_seconds() < 86400:
        existing.violation_count += 1
        existing.last_violation_at = now
        existing.client_name = client
        return existing

    # 新记录或已过期
    v = RiskViolation(
        user_id=user_id,
        device_id=device_id or "",
        client_name=client,
        violation_type=violation_type,
        violation_count=1,
        last_action=None,
        last_violation_at=now,
        locked_until=None,
    )
    db.add(v)
    return v


async def _resolve_escalation(violation: RiskViolation, cp: dict) -> str:
    """根据违规次数 + 策略配置决定执行什么动作"""
    if not cp.get("escalation"):
        return cp.get("action", "force_kick")

    steps = cp.get("escalation_steps", ["message", "stop", "force_kick", "ban"])
    if not steps:
        return cp.get("action", "force_kick")

    # 违规次数从 1 开始，映射到步骤
    idx = min(violation.violation_count - 1, len(steps) - 1)
    idx = max(idx, 0)
    return steps[idx]


async def _log_action(db, action: str, target: str, reason: str | None = None):
    db.add(RiskActionLog(action=action, target=target, reason=reason))
    await db.commit()


async def _upsert_risk_event(
    db,
    *,
    event_type: str,
    title: str,
    description: str | None,
    severity: str = "medium",
    context_json: dict[str, Any] | None = None,
) -> RiskEvent:
    existing_stmt = (
        select(RiskEvent)
        .where(
            RiskEvent.status == "open",
            RiskEvent.event_type == event_type,
            RiskEvent.title == title,
        )
        .order_by(RiskEvent.detected_at.desc())
        .limit(1)
    )
    existing = (await db.execute(existing_stmt)).scalar_one_or_none()
    if existing:
        existing.description = description
        existing.severity = severity
        existing.context_json = context_json
        return existing

    event = RiskEvent(
        user_id=None,
        rule_id=None,
        event_type=event_type,
        severity=severity,
        status="open",
        title=title,
        description=description,
        context_json=context_json,
        detected_at=datetime.now(timezone.utc),
    )
    db.add(event)
    return event


async def _record_scan_events(db, blocked: list[dict], violations: list[dict]):
    for item in blocked:
        await _upsert_risk_event(
            db,
            event_type="client_blocked",
            severity="high",
            title=f"违规客户端拦截：{item.get('user_name') or '未知用户'}",
            description=f"客户端 {item.get('client') or '-'} 播放《{item.get('title') or '未知内容'}》已被拦截，设备已下线。",
            context_json=item,
        )
    for item in violations:
        await _upsert_risk_event(
            db,
            event_type="concurrent_exceeded",
            severity="medium",
            title=f"并发越界：{item.get('user_name') or item.get('user_id') or '未知用户'}",
            description=f"当前并发 {item.get('current', 0)} / 限额 {item.get('max', 0)}",
            context_json=item,
        )
    await db.commit()


async def _execute_client_action(db, session_id: str, device_id: str, user_id: str, action: str, user_name: str, client: str, cp: dict = None):
    """根据策略执行客户端管控动作，支持自定义弹窗内容"""
    if cp is None:
        cp = {}

    # 变量替换
    vars_map = {
        "{client}": client or "未知",
        "{device_name}": "",
        "{user_name}": user_name or "未知用户",
        "{ban_hours}": str(cp.get("ban_hours", 24)),
        "{title}": "",
    }

    def _fmt(template: str) -> str:
        result = template
        for k, v in vars_map.items():
            result = result.replace(k, v)
        return result

    if action == "message":
        text = _fmt(cp.get("msg_message", "当前客户端「{client}」不在允许列表中，请更换客户端。"))
        await emby.send_session_message(session_id, text=text, header="客户端管控", timeout_ms=5000)

    elif action == "stop":
        text = _fmt(cp.get("msg_stop", "当前客户端「{client}」已被管理员禁用，播放已停止。"))
        await emby.send_session_message(session_id, text=text, header="客户端管控", timeout_ms=5000)
        await emby.kick_session(session_id)

    elif action == "force_kick":
        text = _fmt(cp.get("msg_force_kick", "当前客户端「{client}」已被管理员禁用，请更换受支持客户端后重新登录。"))
        await emby.send_session_message(session_id, text=text, header="客户端管控", timeout_ms=5000)
        await emby.force_kick(session_id, device_id)

    elif action == "ban":
        text = _fmt(cp.get("msg_ban", "您的账户已被临时封禁{ban_hours}小时，请联系管理员。"))
        await emby.send_session_message(session_id, text=text, header="账户管控", timeout_ms=5000)
        await emby.force_kick(session_id, device_id)
        if user_id:
            await emby.ban_user(user_id)

    logger.info(f"客户端管控: {user_name}({client}) → {action}")


async def _scan_logic(db) -> dict[str, Any]:
    """核心扫描：策略驱动的客户端管控 + 并发越界检测"""
    policy = await _get_policy(db)
    cp = policy["client_policy"]
    pp = policy["concurrent_policy"]

    blacklist = set(await _get_blacklist(db))
    is_whitelist = cp.get("mode") == "whitelist"
    fuzzy = cp.get("fuzzy_match", False)
    base_action = cp.get("action", "force_kick")
    escalation = cp.get("escalation", False)
    default_max = int(pp.get("default_max", 2) or 2)
    concurrent_action = pp.get("action", "warn")

    sessions = await emby.get_sessions(active_only=True)
    await users_service._reload_meta()

    blocked: list[dict[str, Any]] = []
    violations: list[dict[str, Any]] = []
    concurrent_map: dict[str, list[dict[str, Any]]] = {}

    logger.info(
        f"扫描开始: {len(sessions)}个会话, "
        f"模式={'白名单' if is_whitelist else '黑名单'}, "
        f"名单={len(blacklist)}个, 动作={base_action}, "
        f"并发策略={concurrent_action}"
    )

    for s in sessions:
        session_id = s.get("Id", "")
        user_id = s.get("UserId", "")
        user_name = s.get("UserName", "")
        client = (s.get("Client") or s.get("AppName") or "").strip()
        device_id = s.get("DeviceId", "")
        device_name = s.get("DeviceName", "")
        now_playing = s.get("NowPlayingItem") or {}
        title = now_playing.get("Name", "")

        # 并发统计
        if now_playing and user_id:
            concurrent_map.setdefault(user_id, []).append({
                "session_id": session_id,
                "user_id": user_id,
                "user_name": user_name,
                "client": client,
                "device_id": device_id,
                "device_name": device_name,
                "title": title,
            })

        # 客户端管控
        if not now_playing or not client:
            continue

        matched = _match_client(client, list(blacklist), fuzzy)

        # 黑名单模式：匹配到 = 违规；白名单模式：没匹配到 = 违规
        is_violation = matched if not is_whitelist else not matched

        if is_violation:
            # VIP 豁免客户端管控
            meta = users_service._meta_cache.get(user_id, {})
            if meta.get("is_vip"):
                continue

            # 查/建违规记录
            violation = await _get_or_create_violation(db, user_id, device_id, client, "client_blocked")

            # 检查是否在封禁期内
            if violation.locked_until and violation.locked_until > datetime.now(timezone.utc):
                logger.info(f"跳过: {user_name} 仍在封禁期内(至{violation.locked_until.isoformat()})")
                continue

            # 递进决策
            action = await _resolve_escalation(violation, cp)

            logger.warning(f"客户端违规#{violation.violation_count}: {user_name} 使用 {client} (device={device_id}) → {action}")
            await _execute_client_action(db, session_id, device_id, user_id, action, user_name, client, cp)

            # 更新违规记录
            violation.last_action = action
            if action == "ban":
                ban_hours = int(cp.get("ban_hours", 24) or 24)
                violation.locked_until = datetime.now(timezone.utc) + __import__("datetime").timedelta(hours=ban_hours)

            blocked.append({
                "session_id": session_id,
                "user_id": user_id,
                "user_name": user_name,
                "client": client,
                "device_id": device_id,
                "device_name": device_name,
                "title": title,
                "action": action,
                "violation_count": violation.violation_count,
            })

    # 并发越界检测
    meta_cache = users_service._meta_cache
    for user_id, items in concurrent_map.items():
        current = len(items)
        meta = meta_cache.get(user_id, {})
        max_c = int(meta.get("max_concurrent", default_max) or default_max)
        if current > max_c:
            violations.append({
                "user_id": user_id,
                "user_name": items[0].get("user_name", ""),
                "current": current,
                "max": max_c,
                "sessions": items,
            })

    # 并发超限自动处理
    if concurrent_action != "warn":
        kicked = []
        for v in violations:
            sessions_list = v["sessions"]
            excess = v["current"] - v["max"]
            if concurrent_action == "kick_newest":
                # 踢掉最后加入的会话
                to_kick = sessions_list[-excess:]
            elif concurrent_action == "kick_all":
                to_kick = sessions_list[excess:]
            else:
                to_kick = []
            for sk in to_kick:
                await emby.kick_session(sk["session_id"])
                kicked.append(sk["session_id"])
            if to_kick:
                logger.info(f"并发超限自动踢出: {v['user_name']} 踢掉 {len(to_kick)} 个会话")
        if kicked:
            await _log_action(db, "concurrent_kick", ",".join(kicked), f"并发超限自动踢出{len(kicked)}个会话")

    if blocked or violations:
        await _record_scan_events(db, blocked, violations)

    logger.info(f"扫描完成: 拦截{len(blocked)}个违规, {len(violations)}个越界, 总会话{len(sessions)}")

    return {
        "blocked": blocked,
        "violations": violations,
        "total_sessions": len(sessions),
        "blacklist_count": len(blacklist),
    }


# ── API endpoints ────────────────────────────────────────

@router.get("/summary")
async def summary(db: AsyncSessionDep, _: dict = Depends(get_current_admin)):
    open_count = await db.scalar(select(func.count()).select_from(RiskEvent).where(RiskEvent.status == "open")) or 0
    high_count = await db.scalar(
        select(func.count()).select_from(RiskEvent).where(RiskEvent.status == "open", RiskEvent.severity == "high")
    ) or 0
    recent = (await db.execute(select(RiskEvent).order_by(RiskEvent.detected_at.desc()).limit(5))).scalars().all()
    return ApiResponse.ok(data={
        "open_count": int(open_count),
        "high_count": int(high_count),
        "recent_events": [
            {
                "event_id": str(ev.id),
                "user_id": "",
                "event_type": ev.event_type,
                "severity": ev.severity,
                "status": ev.status,
                "title": ev.title,
                "description": ev.description,
                "detected_at": ev.detected_at,
            }
            for ev in recent
        ],
    })


@router.get("/events")
async def events(
    db: AsyncSessionDep,
    _: dict = Depends(get_current_admin),
    page: int = 1,
    page_size: int = 20,
    status: str | None = None,
    severity: str | None = None,
):
    page = max(page, 1)
    page_size = min(max(page_size, 1), 100)
    stmt = select(RiskEvent)
    count_stmt = select(func.count()).select_from(RiskEvent)
    if status:
        stmt = stmt.where(RiskEvent.status == status)
        count_stmt = count_stmt.where(RiskEvent.status == status)
    if severity:
        stmt = stmt.where(RiskEvent.severity == severity)
        count_stmt = count_stmt.where(RiskEvent.severity == severity)
    total = await db.scalar(count_stmt) or 0
    items = (await db.execute(
        stmt.order_by(RiskEvent.detected_at.desc()).offset((page - 1) * page_size).limit(page_size)
    )).scalars().all()
    return ApiResponse.ok(data={
        "items": [
            {
                "event_id": str(ev.id),
                "user_id": "",
                "event_type": ev.event_type,
                "severity": ev.severity,
                "status": ev.status,
                "title": ev.title,
                "description": ev.description,
                "detected_at": ev.detected_at,
            }
            for ev in items
        ],
        "total": int(total),
    })


@router.post("/events/{event_id}/action")
async def event_action(event_id: str, body: RiskEventActionRequest, db: AsyncSessionDep, _: dict = Depends(get_current_admin)):
    ev = await db.get(RiskEvent, int(event_id))
    if not ev:
        return ApiResponse.error("事件不存在")
    if body.action not in {"resolve", "ignore"}:
        return ApiResponse.error("不支持的操作")
    ev.status = "resolved" if body.action == "resolve" else "ignored"
    ev.resolved_at = datetime.now(timezone.utc)
    await db.commit()
    return ApiResponse.ok(message="操作成功")


@router.get("/logs")
async def logs(db: AsyncSessionDep, _: dict = Depends(get_current_admin), page: int = 1, page_size: int = 20):
    page = max(page, 1)
    page_size = min(max(page_size, 1), 100)
    total = await db.scalar(select(func.count()).select_from(RiskActionLog)) or 0
    rows = (await db.execute(
        select(RiskActionLog).order_by(RiskActionLog.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    )).scalars().all()
    return ApiResponse.ok(data={
        "items": [
            {"id": row.id, "action": row.action, "target": row.target, "reason": row.reason, "created_at": row.created_at}
            for row in rows
        ],
        "total": int(total),
    })


@router.post("/kick")
async def kick(body: KickRequest, db: AsyncSessionDep, _: dict = Depends(get_current_admin)):
    if body.level == "hard":
        result = await emby.force_kick(body.session_id, body.device_id)
        ok = result["stopped"] or result["device_deleted"]
        reason = f"强制踢出(停止={result['stopped']},删设备={result['device_deleted']})"
    else:
        ok = await emby.kick_session(body.session_id)
        reason = "停止播放"
    if ok:
        await _log_action(db, "kick", body.session_id, reason)
    return ApiResponse.ok(data={"success": ok, "level": body.level})


@router.post("/ban")
async def ban(body: BanRequest, db: AsyncSessionDep, _: dict = Depends(get_current_admin)):
    ok = await emby.ban_user(body.user_id)
    if ok:
        await _log_action(db, "ban", body.user_id, body.reason or "管理员封禁")
    return ApiResponse.ok(data={"success": ok})


@router.post("/unban")
async def unban(body: BanRequest, db: AsyncSessionDep, _: dict = Depends(get_current_admin)):
    ok = await emby.unban_user(body.user_id)
    if ok:
        await _log_action(db, "unban", body.user_id, body.reason or "管理员解封")
    return ApiResponse.ok(data={"success": ok})


@router.get("/blacklist")
async def list_blacklist(db: AsyncSessionDep, _: dict = Depends(get_current_admin)):
    return ApiResponse.ok(data=await _get_blacklist(db))


@router.post("/blacklist")
async def add_blacklist(body: BlacklistRequest, db: AsyncSessionDep, _: dict = Depends(get_current_admin)):
    items = await _get_blacklist(db)
    items.append(body.name)
    items = await _set_blacklist(db, items)
    return ApiResponse.ok(data=items, message=f"已加入黑名单: {body.name}")


@router.delete("/blacklist/{name}")
async def remove_blacklist(name: str, db: AsyncSessionDep, _: dict = Depends(get_current_admin)):
    items = [x for x in await _get_blacklist(db) if x != name.strip().lower()]
    items = await _set_blacklist(db, items)
    return ApiResponse.ok(data=items, message=f"已移除: {name}")


@router.get("/device-clients")
async def device_clients(_: dict = Depends(get_current_admin)):
    """获取历史设备中的所有客户端名称（去重）"""
    devices = await emby.get_devices()
    names = set()
    for d in devices:
        app = str(d.get("AppName") or "").strip()
        if app:
            names.add(app)
    return ApiResponse.ok(data=sorted(names))


@router.post("/sweep")
async def sweep(db: AsyncSessionDep, _: dict = Depends(get_current_admin)):
    blacklist = set(await _get_blacklist(db))
    if not blacklist:
        return ApiResponse.ok(data={"deleted": [], "deleted_count": 0, "total_devices": 0}, message="黑名单为空")

    devices = await emby.get_devices()
    if not devices:
        return ApiResponse.ok(data={"deleted": [], "deleted_count": 0, "total_devices": 0}, message="获取设备列表失败或无设备")

    deleted = []
    skipped = []
    for d in devices:
        app_name = str(d.get("AppName") or "").strip().lower()
        device_id = str(d.get("Id") or "")
        if not device_id or not app_name:
            continue
        if app_name in blacklist:
            ok = await emby.delete_device(device_id)
            if ok:
                deleted.append({"device_id": device_id, "app_name": app_name, "user": d.get("LastUserName", "")})
                await _log_action(db, "device_sweep", device_id, f"删除黑名单客户端 {app_name}")
            else:
                skipped.append({"device_id": device_id, "app_name": app_name, "reason": "删除失败"})

    return ApiResponse.ok(data={
        "deleted": deleted,
        "deleted_count": len(deleted),
        "skipped": skipped,
        "total_devices": len(devices),
    })


@router.post("/scan")
async def scan(db: AsyncSessionDep, _: dict = Depends(get_current_admin)):
    return ApiResponse.ok(data=await _scan_logic(db))


@router.get("/status")
async def concurrent_status(db: AsyncSessionDep, _: dict = Depends(get_current_admin)):
    sessions = await emby.get_sessions(active_only=True)
    await users_service._reload_meta()
    policy = await _get_policy(db)
    default_max = int(policy["concurrent_policy"].get("default_max", 2) or 2)
    grouped: dict[str, list[dict[str, Any]]] = {}
    for s in sessions:
        if not s.get("NowPlayingItem"):
            continue
        uid = str(s.get("UserId") or "")
        grouped.setdefault(uid, []).append({
            "session_id": s.get("Id", ""),
            "client": s.get("Client", ""),
            "device_name": s.get("DeviceName", ""),
            "title": (s.get("NowPlayingItem") or {}).get("Name", ""),
            "user_name": s.get("UserName", ""),
        })
    rows = []
    for uid, items in grouped.items():
        meta = users_service._meta_cache.get(uid, {})
        max_c = int(meta.get("max_concurrent", default_max) or default_max)
        rows.append({
            "user_id": uid,
            "user_name": items[0].get("user_name", "") if items else "",
            "current": len(items),
            "max": max_c,
            "exceeded": len(items) > max_c,
            "sessions": items,
        })
    rows.sort(key=lambda x: (not x["exceeded"], -x["current"]))
    return ApiResponse.ok(data=rows)


# ── 策略配置 ────────────────────────────────────────────

@router.get("/policy")
async def get_policy(db: AsyncSessionDep, _: dict = Depends(get_current_admin)):
    """获取管控策略配置"""
    policy = await _get_policy(db)
    return ApiResponse.ok(data=policy)


@router.put("/policy")
async def update_policy(
    body: PolicyUpdateRequest,
    db: AsyncSessionDep,
    _: dict = Depends(get_current_admin),
):
    """更新管控策略配置"""
    policy = await _get_policy(db)
    if body.client_policy is not None:
        policy["client_policy"].update(body.client_policy)
    if body.concurrent_policy is not None:
        policy["concurrent_policy"].update(body.concurrent_policy)
    await _set_setting(db, POLICY_KEY, policy, group="risk", desc="风控管控策略配置")
    logger.info(f"策略已更新: {policy}")
    return ApiResponse.ok(data=policy, message="策略已保存")


@router.get("/violations")
async def violations_list(
    db: AsyncSessionDep,
    _: dict = Depends(get_current_admin),
    user_id: str | None = None,
    page: int = 1,
    page_size: int = 50,
):
    """查看违规记录"""
    page = max(page, 1)
    page_size = min(max(page_size, 1), 200)
    stmt = select(RiskViolation)
    count_stmt = select(func.count()).select_from(RiskViolation)
    if user_id:
        stmt = stmt.where(RiskViolation.user_id == user_id)
        count_stmt = count_stmt.where(RiskViolation.user_id == user_id)
    total = await db.scalar(count_stmt) or 0
    rows = (await db.execute(
        stmt.order_by(RiskViolation.last_violation_at.desc()).offset((page - 1) * page_size).limit(page_size)
    )).scalars().all()
    # 批量查用户名
    unique_uids = list({r.user_id for r in rows if r.user_id})
    uid_name_map: dict[str, str] = {}
    if unique_uids:
        try:
            all_emby_users = await emby.get_users()
            for u in (all_emby_users or []):
                uid = u.get("Id", "")
                if uid in unique_uids:
                    uid_name_map[uid] = u.get("Name", uid)
        except Exception:
            pass
    return ApiResponse.ok(data={
        "items": [
            {
                "id": r.id, "user_id": r.user_id,
                "user_name": uid_name_map.get(r.user_id, r.user_id),
                "device_id": r.device_id,
                "client_name": r.client_name, "violation_type": r.violation_type,
                "violation_count": r.violation_count, "last_action": r.last_action,
                "last_violation_at": r.last_violation_at, "locked_until": r.locked_until,
            } for r in rows
        ],
        "total": int(total),
    })


@router.delete("/violations/{violation_id}")
async def violations_reset(violation_id: int, db: AsyncSessionDep, _: dict = Depends(get_current_admin)):
    """清除单条违规记录"""
    v = await db.get(RiskViolation, violation_id)
    if not v:
        return ApiResponse.error("记录不存在")
    await db.delete(v)
    await db.commit()
    return ApiResponse.ok(message="已清除")
