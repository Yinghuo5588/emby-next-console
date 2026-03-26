"""质量盘点 — 服务层"""
import logging
from datetime import datetime

from sqlalchemy import text, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.emby import emby
from app.db.session import get_session

logger = logging.getLogger("app.quality")

# ── 扫描状态（内存单例）─────────────────────────────
_scan_state: dict = {
    "running": False,
    "total": 0,
    "scanned": 0,
    "started_at": None,
    "finished_at": None,
    "error": None,
}


def get_scan_status() -> dict:
    return _scan_state.copy()


# ── 分类逻辑 ──────────────────────────────────────
def _classify(width: int | None, height: int | None, video_range: str | None) -> tuple[str, str]:
    """返回 (resolution, video_range)"""
    w = width or 0
    h = height or 0
    if w >= 3840 or h >= 2160:
        res = "4K"
    elif w >= 1920 or h >= 1080:
        res = "1080P"
    elif w >= 1280 or h >= 720:
        res = "720P"
    else:
        res = "SD"

    vr = (video_range or "").upper()
    if "DV" in vr or "DOVI" in vr:
        vr = "DV"
    elif "HDR" in vr:
        vr = "HDR10"
    else:
        vr = "SDR"
    return res, vr


def _extract_video_info(media_streams: list[dict]) -> tuple[int | None, int | None, str | None]:
    """从 MediaStreams 中提取视频流信息"""
    for s in media_streams or []:
        if s.get("Type") == "Video":
            return s.get("Width"), s.get("Height"), s.get("VideoRange")
    return None, None, None


def _build_poster_url(item_id: str) -> str:
    return f"/api/v1/manage/users/{item_id}/avatar"  # 用代理端点


# ── 扫描逻辑 ──────────────────────────────────────
async def scan_all_items() -> None:
    """异步扫描 Emby 全部媒体项，写入 quality_items 表"""
    global _scan_state
    _scan_state = {
        "running": True,
        "total": 0,
        "scanned": 0,
        "started_at": datetime.utcnow().isoformat(),
        "finished_at": None,
        "error": None,
    }

    try:
        page_size = 200
        start_index = 0
        first_page = True

        async for db in get_session():
            while True:
                resp = await emby.get("/Items", params={
                    "Recursive": "true",
                    "IncludeItemTypes": "Movie,Episode",
                    "Fields": "MediaStreams,Path",
                    "Limit": page_size,
                    "StartIndex": start_index,
                })
                resp.raise_for_status()
                data = resp.json()
                items = data.get("Items", [])
                total = data.get("TotalRecordCount", 0)

                if first_page:
                    _scan_state["total"] = total
                    first_page = False

                if not items:
                    break

                # 批量 upsert
                for item in items:
                    item_id = item.get("Id", "")
                    name = item.get("Name", "")
                    path = item.get("Path", "")
                    item_type = item.get("Type", "")
                    media_streams = item.get("MediaStreams", [])
                    width, height, vr_raw = _extract_video_info(media_streams)
                    resolution, video_range = _classify(width, height, vr_raw)

                    await db.execute(text("""
                        INSERT INTO quality_items (item_id, name, path, resolution, video_range, width, height, item_type, poster_url, is_ignored, scanned_at)
                        VALUES (:item_id, :name, :path, :resolution, :video_range, :width, :height, :item_type, :poster_url, false, now())
                        ON CONFLICT (item_id) DO UPDATE SET
                            name = EXCLUDED.name,
                            path = EXCLUDED.path,
                            resolution = EXCLUDED.resolution,
                            video_range = EXCLUDED.video_range,
                            width = EXCLUDED.width,
                            height = EXCLUDED.height,
                            item_type = EXCLUDED.item_type,
                            poster_url = EXCLUDED.poster_url,
                            scanned_at = now()
                    """), {
                        "item_id": item_id,
                        "name": name,
                        "path": path,
                        "resolution": resolution,
                        "video_range": video_range,
                        "width": width,
                        "height": height,
                        "item_type": item_type,
                        "poster_url": f"/api/v1/proxy/image/{item_id}/Primary",
                    })

                await db.commit()
                start_index += len(items)
                _scan_state["scanned"] = start_index

                if start_index >= total:
                    break

        _scan_state["running"] = False
        _scan_state["finished_at"] = datetime.utcnow().isoformat()
        logger.info(f"Quality scan done: {_scan_state['scanned']} items")

    except Exception as e:
        _scan_state["running"] = False
        _scan_state["error"] = str(e)
        _scan_state["finished_at"] = datetime.utcnow().isoformat()
        logger.error(f"Quality scan failed: {e}", exc_info=True)


# ── 查询逻辑 ──────────────────────────────────────
async def get_overview() -> dict:
    """聚合统计"""
    async for db in get_session():
        # 分辨率分布
        res_rows = (await db.execute(text(
            "SELECT resolution, COUNT(*) as cnt FROM quality_items WHERE is_ignored = false GROUP BY resolution"
        ))).all()
        resolution = {r[0]: r[1] for r in res_rows}

        # 动态范围分布
        vr_rows = (await db.execute(text(
            "SELECT video_range, COUNT(*) as cnt FROM quality_items WHERE is_ignored = false GROUP BY video_range"
        ))).all()
        video_range = {r[0]: r[1] for r in vr_rows}

        # 总数
        total = (await db.execute(text(
            "SELECT COUNT(*) FROM quality_items WHERE is_ignored = false"
        ))).scalar_one()

        return {
            "resolution": resolution,
            "video_range": video_range,
            "total": total,
            "scan": get_scan_status(),
        }


async def get_items(
    resolution: str | None = None,
    video_range: str | None = None,
    is_ignored: bool | None = None,
    sort: str = "name",
    page: int = 1,
    size: int = 25,
) -> dict:
    """分页列表"""
    conditions = ["is_ignored = :ignored"]
    params: dict = {"ignored": is_ignored if is_ignored is not None else False}

    if resolution:
        conditions.append("resolution = :resolution")
        params["resolution"] = resolution
    if video_range:
        conditions.append("video_range = :video_range")
        params["video_range"] = video_range

    where = " AND ".join(conditions)
    order_map = {
        "name": "name ASC",
        "resolution": "CASE resolution WHEN '4K' THEN 1 WHEN '1080P' THEN 2 WHEN '720P' THEN 3 ELSE 4 END ASC",
        "video_range": "CASE video_range WHEN 'DV' THEN 1 WHEN 'HDR10' THEN 2 ELSE 3 END ASC",
        "type": "item_type ASC, name ASC",
    }
    order = order_map.get(sort, "name ASC")

    params["limit"] = size
    params["offset"] = (page - 1) * size

    async for db in get_session():
        count_row = (await db.execute(text(f"SELECT COUNT(*) FROM quality_items WHERE {where}"), params)).scalar_one()
        rows = (await db.execute(
            text(f"SELECT item_id, name, path, resolution, video_range, width, height, item_type, poster_url, is_ignored FROM quality_items WHERE {where} ORDER BY {order} LIMIT :limit OFFSET :offset"),
            params,
        )).fetchall()

        items = [{
            "item_id": r[0], "name": r[1], "path": r[2], "resolution": r[3],
            "video_range": r[4], "width": r[5], "height": r[6],
            "item_type": r[7], "poster_url": r[8], "is_ignored": r[9],
        } for r in rows]

        return {"items": items, "total": count_row, "page": page, "size": size}


async def set_ignored(item_id: str, ignore: bool) -> None:
    async for db in get_session():
        await db.execute(
            text("UPDATE quality_items SET is_ignored = :ignored WHERE item_id = :item_id"),
            {"ignored": ignore, "item_id": item_id},
        )
        await db.commit()
