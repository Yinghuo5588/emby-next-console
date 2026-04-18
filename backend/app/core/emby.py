"""
Emby API 适配器
支持 Emby / Jellyfin 双协议，统一请求入口。
"""
from __future__ import annotations

import logging
from typing import Any

import httpx

from app.core.settings import settings

logger = logging.getLogger("app.emby")


class EmbyAdapter:
    """Emby/Jellyfin REST API 适配器，基于 httpx 异步客户端。"""

    def __init__(self, host: str = "", api_key: str = "") -> None:
        self._host = (host or settings.EMBY_HOST).rstrip("/")
        self._api_key = api_key or settings.EMBY_API_KEY
        self._client: httpx.AsyncClient | None = None

    # ── 连接管理 ──────────────────────────────────────────────

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(15.0, connect=5.0),
                limits=httpx.Limits(max_connections=50, max_keepalive_connections=20),
            )
        return self._client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    # ── 内部方法 ──────────────────────────────────────────────

    def _build_url(self, path: str) -> str:
        if not path.startswith("/"):
            path = "/" + path
        if not path.startswith("/emby/"):
            path = "/emby" + path
        return f"{self._host}{path}"

    @staticmethod
    def _headers() -> dict[str, str]:
        return {"X-Emby-Token": settings.EMBY_API_KEY}

    async def _request(self, method: str, path: str, auth: bool = True, **kwargs: Any) -> httpx.Response:
        client = await self._get_client()
        url = self._build_url(path)
        kwargs.setdefault("headers", {})
        if auth:
            kwargs["headers"].update(self._headers())
        # 移除可能残留的 api_key params（改用 header 鉴权）
        params = kwargs.get("params")
        if params and "api_key" in params:
            del params["api_key"]
        return await client.request(method, url, **kwargs)

    # ── 便捷方法 ──────────────────────────────────────────────

    async def get(self, path: str, **kw: Any) -> httpx.Response:
        return await self._request("GET", path, **kw)

    async def post(self, path: str, **kw: Any) -> httpx.Response:
        return await self._request("POST", path, **kw)

    async def delete(self, path: str, **kw: Any) -> httpx.Response:
        return await self._request("DELETE", path, **kw)

    # ── 高层 API ─────────────────────────────────────────────

    async def get_users(self) -> list[dict]:
        """获取所有 Emby 用户"""
        resp = await self.get("/Users")
        resp.raise_for_status()
        return resp.json()

    async def get_user(self, user_id: str) -> dict:
        """获取单个用户详情"""
        resp = await self.get(f"/Users/{user_id}")
        resp.raise_for_status()
        return resp.json()

    async def get_sessions(self, active_only: bool = True) -> list[dict]:
        """获取当前播放会话"""
        params = {}
        if active_only:
            params["activeWithinSeconds"] = 600
        resp = await self.get("/Sessions", params=params)
        resp.raise_for_status()
        return resp.json()

    async def get_playing_sessions(self) -> list[dict]:
        """获取正在播放的会话（有 NowPlayingItem）"""
        sessions = await self.get_sessions()
        return [s for s in sessions if s.get("NowPlayingItem")]

    async def get_library_virtual_folders(self) -> list[dict]:
        """获取媒体库列表"""
        resp = await self.get("/Library/VirtualFolders")
        resp.raise_for_status()
        return resp.json()

    async def get_views(self) -> list[dict]:
        """获取媒体库视图列表"""
        resp = await self._request("GET", "/Library/VirtualFolders")
        resp.raise_for_status()
        data = resp.json()
        return data if isinstance(data, list) else data.get("Items", [])

    async def get_items(self, **params: Any) -> dict:
        """通用 Items 查询（分页、筛选等）"""
        resp = await self.get("/Items", params=params)
        resp.raise_for_status()
        return resp.json()

    async def get_item(self, item_id: str) -> dict:
        """获取单个媒体项目详情"""
        resp = await self.get(f"/Items/{item_id}")
        resp.raise_for_status()
        return resp.json()

    async def get_system_info(self) -> dict:
        """获取 Emby 系统信息"""
        resp = await self.get("/System/Info")
        resp.raise_for_status()
        return resp.json()

    async def get_activity_log(self, min_date: str = "", limit: int = 50) -> list[dict]:
        """获取活动日志"""
        params: dict[str, Any] = {"limit": limit}
        if min_date:
            params["minDate"] = min_date
        resp = await self.get("/System/ActivityLog/Entries", params=params)
        resp.raise_for_status()
        data = resp.json()
        return data.get("Items", data) if isinstance(data, dict) else data

    async def query_playback_stats(self, sql: str) -> list[dict]:
        """
        通过 playback_reporting 插件的 API 穿透查询。
        需要 Emby 安装了 playback_reporting 插件。
        """
        resp = await self.post(
            "/user_usage_stats/submit_custom_query",
            json={"CustomQueryString": sql},
        )
        if resp.status_code != 200:
            logger.warning("playback stats API 返回 %d: %s", resp.status_code, resp.text[:200])
            return []
        data = resp.json()
        if isinstance(data, str):
            import json
            data = json.loads(data)
        if isinstance(data, dict):
            columns = data.get("colums") or data.get("columns") or []
            results = data.get("results") or []
            rows = []
            for row in results:
                if isinstance(row, list):
                    row_dict = {}
                    for i, col in enumerate(columns):
                        val = row[i] if i < len(row) else None
                        if isinstance(val, str) and val.isdigit():
                            val = int(val)
                        row_dict[col] = val
                    rows.append(row_dict)
            return rows
        return data if isinstance(data, list) else [data]

    async def health_check(self) -> tuple[bool, str]:
        """检查 Emby 连接状态"""
        try:
            resp = await self.get("/System/Info/Public")
            if resp.status_code == 200:
                info = resp.json()
                return True, info.get("ServerName", "OK")
            return False, f"HTTP {resp.status_code}"
        except Exception as e:
            return False, str(e)

    async def auth_with_password(self, username: str, password: str) -> dict | None:
        """Emby 用户名密码登录认证"""
        try:
            client = await self._get_client()
            url = self._build_url("/Users/AuthenticateByName")
            headers = {
                "X-Emby-Authorization": (
                    'MediaBrowser Client="Emby Next Console",'
                    'Device="Web",DeviceId="emby-next-console",'
                    'Version="1.0.0"'
                ),
            }
            resp = await client.post(
                url,
                json={"Username": username, "Pw": password},
                headers=headers,
            )
            if not resp.is_success:
                body = await resp.aread()
                logger.warning(f"Emby auth failed: {resp.status_code} body={body.decode('utf-8', errors='replace')}")
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.warning(f"Portal login failed for {username}: {e}")
            return None

    def get_user_image_url(self, user_id: str) -> str:
        """获取用户头像 URL"""
        return f"{self._host}/emby/Users/{user_id}/Images/Primary"



    # ── 风控执法 ────────────────────────────────────────────────

    async def delete_device(self, device_id: str) -> bool:
        """删除设备凭证（设备需重新登录）"""
        try:
            resp = await self.delete("/Devices", params={"Id": device_id})
            return resp.status_code in (200, 204)
        except Exception as e:
            logger.error("删除设备 %s 失败: %s", device_id, e)
            return False

    async def send_session_message(self, session_id: str, text: str, header: str = "", timeout_ms: int = 3000) -> bool:
        """向指定会话发送弹窗消息（参数走 query params）"""
        try:
            params = {"Text": text}
            if header:
                params["Header"] = header
            if timeout_ms:
                params["TimeoutMs"] = timeout_ms
            resp = await self.post(f"/Sessions/{session_id}/Message", params=params)
            return resp.status_code in (200, 204)
        except Exception as e:
            logger.error("发送消息到会话 %s 失败: %s", session_id, e)
            return False
        except Exception as e:
            logger.error("发送消息到会话 %s 失败: %s", session_id, e)
            return False

    async def kick_session(self, session_id: str, reason: str = "管理员强制中止播放") -> bool:
        """踢出播放会话（仅停止播放，对302无效）"""
        try:
            resp = await self.post(f"/Sessions/{session_id}/Playing/Stop", json={})
            return resp.status_code in (200, 204)
        except Exception as e:
            logger.error("踢出会话 %s 失败: %s", session_id, e)
            return False

    async def force_kick(self, session_id: str, device_id: str = "") -> dict:
        """
        强制踢出：先停止播放，再删除设备凭证。
        对 302 播放有效（删设备后客户端无法获取新链接）。
        """
        result = {"stopped": False, "device_deleted": False}
        try:
            resp = await self.post(f"/Sessions/{session_id}/Playing/Stop", json={})
            result["stopped"] = resp.status_code in (200, 204)
        except Exception as e:
            logger.error("停止播放 %s 失败: %s", session_id, e)

        if device_id:
            result["device_deleted"] = await self.delete_device(device_id)

        return result

    async def ban_user(self, user_id: str) -> bool:
        """禁用用户"""
        try:
            resp = await self.get(f"/Users/{user_id}")
            if resp.status_code != 200:
                return False
            policy = resp.json().get("Policy", {})
            policy["IsDisabled"] = True
            resp2 = await self.post(f"/Users/{user_id}/Policy", json=policy)
            return resp2.status_code in (200, 204)
        except Exception as e:
            logger.error("封禁用户 %s 失败: %s", user_id, e)
            return False

    async def unban_user(self, user_id: str) -> bool:
        """启用用户"""
        try:
            resp = await self.get(f"/Users/{user_id}")
            if resp.status_code != 200:
                return False
            policy = resp.json().get("Policy", {})
            policy["IsDisabled"] = False
            resp2 = await self.post(f"/Users/{user_id}/Policy", json=policy)
            return resp2.status_code in (200, 204)
        except Exception as e:
            logger.error("解封用户 %s 失败: %s", user_id, e)
            return False

    async def get_devices(self) -> list[dict]:
        """获取设备列表"""
        try:
            resp = await self.get("/Devices")
            resp.raise_for_status()
            data = resp.json()
            return data.get("Items", []) if isinstance(data, dict) else data
        except Exception:
            return []

# ── 全局单例 ──────────────────────────────────────────────────

emby = EmbyAdapter()
