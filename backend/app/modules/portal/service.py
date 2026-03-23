"""
Portal 用户服务 — 参考 Emby Pulse 的 user_details 实现
"""
import logging
import re
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models.user import User, UserProfile
from app.core.emby import emby
from app.core.emby_data import data as emby_data
from app.core.security import create_access_token

logger = logging.getLogger("app.portal")


async def _query_user_playback(sql: str, user_id: str) -> list[dict]:
    """查询指定用户的 Playback Reporting 数据"""
    safe_sql = sql.replace("{user_filter}", f"UserId = '{user_id}'")
    try:
        return await emby.query_playback_stats(safe_sql)
    except Exception as e:
        logger.warning("Portal playback query failed: %s", e)
        return []


def _clean_name(name: str, item_type: str = "") -> str:
    if not name:
        return "未知内容"
    name = str(name)
    if str(item_type) != "Episode":
        return name.split(" - ")[0]
    parts = [p.strip() for p in name.split(" - ")]
    series = parts[0]
    cn_map = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9, "十": 10}
    for part in parts[1:]:
        m = re.search(r"(?:S|Season\s*)0*(\d+)", part, re.I)
        if m:
            return f"{series} - 第{int(m.group(1))}季"
        m = re.search(r"第\s*([一二三四五六七八九十\d]+)\s*季", part)
        if m:
            num = cn_map.get(m.group(1), int(m.group(1)) if m.group(1).isdigit() else 1)
            return f"{series} - 第{num}季"
    return series


class PortalService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def login(self, username: str, password: str) -> dict:
        """通过 Emby 认证，返回 JWT token"""
        auth_result = await emby.auth_with_password(username, password)
        if not auth_result:
            raise ValueError("用户名或密码错误")

        emby_user_id = auth_result.get("User", {}).get("Id")
        if not emby_user_id:
            emby_name = auth_result.get("User", {}).get("Name", "?")
            logger.warning(f"Emby auth ok but no User.Id for {username}, name={emby_name}")
            raise ValueError("Emby 认证失败：未获取到用户 ID")

        logger.info(f"Emby auth success: {username} -> {emby_user_id}")

        # 同步本地用户
        result = await self.db.execute(
            select(User).where(User.emby_user_id == emby_user_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            try:
                user = User(emby_user_id=emby_user_id, username=username, role="user")
                self.db.add(user)
                await self.db.commit()
                await self.db.refresh(user)
            except Exception as e:
                await self.db.rollback()
                logger.error(f"Failed to create local user: {e}")
                raise ValueError(f"创建本地用户失败: {e}")

        token = create_access_token(
            subject=emby_user_id,
            expires_delta=timedelta(days=7),
            type="portal",
        )

        return {
            "token": token,
            "user": {
                "emby_user_id": emby_user_id,
                "username": username,
                "is_admin": user.role == "admin",
            },
        }

    async def get_me(self, emby_user_id: str) -> dict:
        """获取用户信息（合并本地 + Emby）"""
        result = await self.db.execute(
            select(User).where(User.emby_user_id == emby_user_id)
        )
        user = result.scalar_one_or_none()

        emby_user = await emby.get_user(emby_user_id)

        # 获取 profile
        profile = None
        if user:
            p_res = await self.db.execute(
                select(UserProfile).where(UserProfile.user_id == user.id)
            )
            profile = p_res.scalar_one_or_none()

        return {
            "emby_user_id": emby_user_id,
            "username": user.username if user else (emby_user or {}).get("Name", ""),
            "display_name": (emby_user or {}).get("Name", ""),
            "is_admin": user.role == "admin" if user else False,
            "is_vip": profile.is_vip if profile else False,
            "max_concurrent": profile.max_concurrent if profile else 2,
            "avatar": emby.get_user_image_url(emby_user_id) if emby_user else None,
        }

    async def get_stats(self, emby_user_id: str) -> dict:
        """获取用户观看统计（参考 Emby Pulse user_details）"""
        uf = f"UserId = '{emby_user_id}'"

        # 概览
        overview = {"total_plays": 0, "total_duration": 0, "total_duration_hours": 0}
        try:
            rows = await emby.query_playback_stats(
                f"SELECT COUNT(*) as plays, SUM(PlayDuration) as dur FROM PlaybackActivity WHERE {uf}"
            )
            if rows:
                overview["total_plays"] = rows[0].get("plays", 0)
                overview["total_duration"] = rows[0].get("dur", 0) or 0
                overview["total_duration_hours"] = round(overview["total_duration"] / 3600, 1)
        except Exception:
            pass

        # 活跃会话
        try:
            sessions = await emby.get_sessions(active_only=False)
            user_sessions = [s for s in sessions if s.get("UserId") == emby_user_id and s.get("NowPlayingItem")]
            overview["active_sessions"] = len(user_sessions)
        except Exception:
            overview["active_sessions"] = 0

        # 趋势（最近 30 天每日）
        trend = []
        try:
            rows = await emby.query_playback_stats(
                f"SELECT DATE(DateCreated) as date, COUNT(*) as play_count, "
                f"SUM(PlayDuration) as dur FROM PlaybackActivity "
                f"WHERE {uf} AND DateCreated >= date('now', '-30 days') "
                f"GROUP BY DATE(DateCreated) ORDER BY date ASC"
            )
            trend = [dict(r) for r in rows] if rows else []
        except Exception:
            pass

        # 热门媒体 Top 10
        top_media = []
        try:
            rows = await emby.query_playback_stats(
                f"SELECT ItemName, ItemId, ItemType, COUNT(*) as play_count, "
                f"SUM(PlayDuration) as total_duration "
                f"FROM PlaybackActivity WHERE {uf} "
                f"GROUP BY ItemName ORDER BY play_count DESC LIMIT 10"
            )
            if rows:
                for r in rows:
                    r["clean_name"] = _clean_name(r.get("ItemName", ""), r.get("ItemType", ""))
                    iid = r.get("ItemId")
                    if iid:
                        r["poster_url"] = f"/api/v1/proxy/smart_image?item_id={iid}&type=Primary"
                top_media = [dict(r) for r in rows]
        except Exception:
            pass

        # 最近观看
        recent = []
        try:
            rows = await emby.query_playback_stats(
                f"SELECT DateCreated, ItemName, ItemId, ItemType, PlayDuration, "
                f"COALESCE(ClientName, DeviceName) as device "
                f"FROM PlaybackActivity WHERE {uf} "
                f"ORDER BY DateCreated DESC LIMIT 20"
            )
            if rows:
                for r in rows:
                    r["clean_name"] = _clean_name(r.get("ItemName", ""), r.get("ItemType", ""))
                    iid = r.get("ItemId")
                    if iid:
                        r["poster_url"] = f"/api/v1/proxy/smart_image?item_id={iid}&type=Primary"
                recent = [dict(r) for r in rows]
        except Exception:
            pass

        # 设备分布
        devices = []
        try:
            rows = await emby.query_playback_stats(
                f"SELECT COALESCE(ClientName, '未知') as device, COUNT(*) as count "
                f"FROM PlaybackActivity WHERE {uf} "
                f"GROUP BY ClientName ORDER BY count DESC LIMIT 10"
            )
            devices = [dict(r) for r in rows] if rows else []
        except Exception:
            pass

        # 生物钟热力图（24h x 7d）
        clock = [[0] * 7 for _ in range(24)]
        try:
            rows = await emby.query_playback_stats(
                f"SELECT DateCreated FROM PlaybackActivity WHERE {uf} AND DateCreated >= date('now', '-90 days')"
            )
            for r in rows:
                dc = r.get("DateCreated")
                if dc:
                    m = re.search(r"(\d{4})-(\d{2})-(\d{2})[T\s](\d{2})", str(dc))
                    if m:
                        hour = int(m.group(4))
                        try:
                            dt = datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))
                            dow = dt.weekday()
                        except ValueError:
                            continue
                        if 0 <= hour < 24 and 0 <= dow < 7:
                            clock[hour][dow] += 1
        except Exception:
            pass

        return {
            "overview": overview,
            "trend": trend,
            "top_media": top_media,
            "recent": recent,
            "devices": devices,
            "clock": clock,
        }

    async def get_badges(self, emby_user_id: str) -> list[dict]:
        """趣味成就徽章"""
        uf = f"UserId = '{emby_user_id}'"
        try:
            rows = await emby.query_playback_stats(
                f"SELECT DateCreated, PlayDuration, COALESCE(ClientName, DeviceName) as client, "
                f"ItemId, ItemName, ItemType FROM PlaybackActivity WHERE {uf}"
            )
        except Exception:
            return []

        if not rows:
            return []

        night_c = weekend_c = fish_c = morning_c = 0
        dur_total = 0
        devices = set()
        items: dict[str, dict] = {}
        movies = eps = 0

        for r in rows:
            dur = r.get("PlayDuration") or 0
            dur_total += dur
            client = r.get("client")
            if client:
                devices.add(client)
            iid = r.get("ItemId")
            if iid:
                items.setdefault(iid, {"name": r.get("ItemName"), "c": 0})
                items[iid]["c"] += 1
            it = r.get("ItemType")
            if it == "Movie":
                movies += 1
            elif it == "Episode":
                eps += 1

            dc = r.get("DateCreated")
            if dc:
                m = re.search(r"(\d{4})-(\d{2})-(\d{2})[T\s](\d{2})", str(dc))
                if m:
                    hour = int(m.group(4))
                    try:
                        dt = datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))
                    except ValueError:
                        continue
                    wd = dt.weekday()
                    if 2 <= hour <= 5:
                        night_c += 1
                    if wd in (5, 6):
                        weekend_c += 1
                    if 0 <= wd <= 4 and 9 <= hour <= 17:
                        fish_c += 1
                    if 5 <= hour <= 8:
                        morning_c += 1

        badges = []
        if night_c >= 2:
            badges.append({"id": "night", "name": "深夜修仙", "icon": "fa-moon", "color": "text-indigo-500", "bg": "bg-indigo-100", "desc": "深夜是灵魂最自由的时刻"})
        if weekend_c >= 5:
            badges.append({"id": "weekend", "name": "周末狂欢", "icon": "fa-champagne-glasses", "color": "text-pink-500", "bg": "bg-pink-100", "desc": "工作日唯唯诺诺，周末重拳出击"})
        if dur_total > 180000:
            badges.append({"id": "liver", "name": "核心肝帝", "icon": "fa-fire", "color": "text-red-500", "bg": "bg-red-100", "desc": "阅片无数，肝度爆表"})
        if fish_c >= 5:
            badges.append({"id": "fish", "name": "带薪观影", "icon": "fa-fish", "color": "text-cyan-500", "bg": "bg-cyan-100", "desc": "工作是老板的，快乐是自己的"})
        if morning_c >= 2:
            badges.append({"id": "morning", "name": "晨练追剧", "icon": "fa-sun", "color": "text-amber-500", "bg": "bg-amber-100", "desc": "比你优秀的人，连看片都比你早"})
        if len(devices) >= 2:
            badges.append({"id": "device", "name": "全平台制霸", "icon": "fa-gamepad", "color": "text-emerald-500", "bg": "bg-emerald-100", "desc": "手机、平板、电视，哪里都能看"})

        if items:
            loyal = max(items.values(), key=lambda x: x["c"])
            if loyal["c"] >= 3:
                safe = str(loyal.get("name") or "未知").split(" - ")[0][:10]
                badges.append({"id": "loyal", "name": "N刷狂魔", "icon": "fa-repeat", "color": "text-teal-500", "bg": "bg-teal-100", "desc": f"对《{safe}》爱得深沉"})

        total = movies + eps
        if total > 10:
            if movies / total > 0.6:
                badges.append({"id": "movie_lover", "name": "电影鉴赏家", "icon": "fa-film", "color": "text-blue-500", "bg": "bg-blue-100", "desc": "沉浸在两小时的艺术光影世界"})
            elif eps / total > 0.6:
                badges.append({"id": "tv_lover", "name": "追剧狂魔", "icon": "fa-tv", "color": "text-purple-500", "bg": "bg-purple-100", "desc": "一集接一集，根本停不下来"})

        return badges

    async def update_profile(self, emby_user_id: str, **kwargs):
        """更新用户资料"""
        result = await self.db.execute(
            select(User).where(User.emby_user_id == emby_user_id)
        )
        user = result.scalar_one_or_none()
        if user:
            profile_result = await self.db.execute(
                select(UserProfile).where(UserProfile.user_id == user.id)
            )
            profile = profile_result.scalar_one_or_none()

            if not profile:
                profile = UserProfile(user_id=user.id)
                self.db.add(profile)

            if kwargs.get("display_name"):
                user.display_name = kwargs["display_name"]
            if kwargs.get("avatar_url"):
                profile.avatar_url = kwargs["avatar_url"]

            await self.db.commit()
