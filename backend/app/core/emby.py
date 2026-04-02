"""
Emby API ééå¨
æ¯æ Emby / Jellyfin ååè®®ï¼ç»ä¸è¯·æ±å¥å£ã
"""
from __future__ import annotations

import logging
from typing import Any

import httpx

from app.core.settings import settings

logger = logging.getLogger("app.emby")


class EmbyAdapter:
    """Emby/Jellyfin REST API ééå¨ï¼åºäº httpx å¼æ­¥å®¢æ·ç«¯ã"""

    def __init__(self, host: str = "", api_key: str = "") -> None:
        self._host = (host or settings.EMBY_HOST).rstrip("/")
        self._api_key = api_key or settings.EMBY_API_KEY
        self._client: httpx.AsyncClient | None = None

    # ââ è¿æ¥ç®¡ç ââââââââââââââââââââââââââââââââââââââââââââââ

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

    # ââ åé¨æ¹æ³ ââââââââââââââââââââââââââââââââââââââââââââââ

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
        # ç§»é¤å¯è½æ®çç api_key paramsï¼æ¹ç¨ header é´æï¼
        params = kwargs.get("params")
        if params and "api_key" in params:
            del params["api_key"]
        return await client.request(method, url, **kwargs)

    # ââ ä¾¿æ·æ¹æ³ ââââââââââââââââââââââââââââââââââââââââââââââ

    async def get(self, path: str, **kw: Any) -> httpx.Response:
        return await self._request("GET", path, **kw)

    async def post(self, path: str, **kw: Any) -> httpx.Response:
        return await self._request("POST", path, **kw)

    async def delete(self, path: str, **kw: Any) -> httpx.Response:
        return await self._request("DELETE", path, **kw)

    # ââ é«å± API âââââââââââââââââââââââââââââââââââââââââââââ

    async def get_users(self) -> list[dict]:
        """è·åææ Emby ç¨æ·"""
        resp = await self.get("/Users")
        resp.raise_for_status()
        return resp.json()

    async def get_user(self, user_id: str) -> dict:
        """è·ååä¸ªç¨æ·è¯¦æ"""
        resp = await self.get(f"/Users/{user_id}")
        resp.raise_for_status()
        return resp.json()

    async def get_sessions(self, active_only: bool = True) -> list[dict]:
        """è·åå½åæ­æ¾ä¼è¯"""
        params = {}
        if active_only:
            params["activeWithinSeconds"] = 600
        resp = await self.get("/Sessions", params=params)
        resp.raise_for_status()
        return resp.json()

    async def get_playing_sessions(self) -> list[dict]:
        """è·åæ­£å¨æ­æ¾çä¼è¯ï¼æ NowPlayingItemï¼"""
        sessions = await self.get_sessions()
        return [s for s in sessions if s.get("NowPlayingItem")]

    async def get_library_virtual_folders(self) -> list[dict]:
        """è·ååªä½åºåè¡¨"""
        resp = await self.get("/Library/VirtualFolders")
        resp.raise_for_status()
        return resp.json()

    async def get_views(self) -> list[dict]:
        """è·ååªä½åºè§å¾åè¡¨"""
        resp = await self._request("GET", "/Library/VirtualFolders")
        resp.raise_for_status()
        data = resp.json()
        return data if isinstance(data, list) else data.get("Items", [])

    async def get_items(self, **params: Any) -> dict:
        """éç¨ Items æ¥è¯¢ï¼åé¡µãç­éç­ï¼"""
        resp = await self.get("/Items", params=params)
        resp.raise_for_status()
        return resp.json()

    async def get_item(self, item_id: str) -> dict:
        """è·ååä¸ªåªä½é¡¹ç®è¯¦æ"""
        resp = await self.get(f"/Items/{item_id}")
        resp.raise_for_status()
        return resp.json()

    async def get_system_info(self) -> dict:
        """è·å Emby ç³»ç»ä¿¡æ¯"""
        resp = await self.get("/System/Info")
        resp.raise_for_status()
        return resp.json()

    async def get_activity_log(self, min_date: str = "", limit: int = 50) -> list[dict]:
        """è·åæ´»å¨æ¥å¿"""
        params: dict[str, Any] = {"limit": limit}
        if min_date:
            params["minDate"] = min_date
        resp = await self.get("/System/ActivityLog/Entries", params=params)
        resp.raise_for_status()
        data = resp.json()
        return data.get("Items", data) if isinstance(data, dict) else data

    async def query_playback_stats(self, sql: str) -> list[dict]:
        """
        éè¿ playback_reporting æä»¶ç API ç©¿éæ¥è¯¢ã
        éè¦ Emby å®è£äº playback_reporting æä»¶ã
        """
        resp = await self.post(
            "/user_usage_stats/submit_custom_query",
            json={"CustomQueryString": sql},
        )
        if resp.status_code != 200:
            logger.warning("playback stats API è¿å %d: %s", resp.status_code, resp.text[:200])
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
        """æ£æ¥ Emby è¿æ¥ç¶æ"""
        try:
            resp = await self.get("/System/Info/Public")
            if resp.status_code == 200:
                info = resp.json()
                return True, info.get("ServerName", "OK")
            return False, f"HTTP {resp.status_code}"
        except Exception as e:
            return False, str(e)

    async def auth_with_password(self, username: str, password: str) -> dict | None:
        """Emby ç¨æ·åå¯ç ç»å½è®¤è¯"""
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
        """è·åç¨æ·å¤´å URL"""
        return f"{self._host}/emby/Users/{user_id}/Images/Primary"

    async def upload_user_avatar(self, user_id: str, image_bytes: bytes, content_type: str = "image/jpeg") -> bool:
        """上传用户头像到 Emby"""
        import base64
        try:
            client = await self._get_client()
            headers = {"X-Emby-Token": self._api_key}
            # 1. 删除旧头像
            del_url = self._build_url(f"/Users/{user_id}/Images/Primary")
            await client.delete(del_url, headers=headers)
            # 2. 上传新头像（Base64 编码，Content-Type 为实际图片类型）
            upload_url = self._build_url(f"/Users/{user_id}/Images/Primary")
            b64_data = base64.b64encode(image_bytes)
            headers["Content-Type"] = content_type
            resp = await client.post(upload_url, headers=headers, content=b64_data)
            if resp.status_code not in (200, 204):
                logger.error("上传头像 %s 失败: %d %s", user_id, resp.status_code, resp.text[:200])
            return resp.status_code in (200, 204)
        except Exception as e:
            logger.error("上传头像 %s 失败: %s", user_id, e)
            return False

    async def delete_user_avatar(self, user_id: str) -> bool:
        """删除用户头像"""
        try:
            resp = await self.delete(f"/Users/{user_id}/Images/Primary")
            return resp.status_code in (200, 204, 404)
        except Exception as e:
            logger.error("删除头像 %s 失败: %s", user_id, e)
            return False



    # ââ é£æ§æ§æ³ ââââââââââââââââââââââââââââââââââââââââââââââââ

    async def delete_device(self, device_id: str) -> bool:
        """å é¤è®¾å¤å­è¯ï¼è®¾å¤ééæ°ç»å½ï¼"""
        try:
            resp = await self.delete("/Devices", params={"Id": device_id})
            return resp.status_code in (200, 204)
        except Exception as e:
            logger.error("å é¤è®¾å¤ %s å¤±è´¥: %s", device_id, e)
            return False

    async def send_session_message(self, session_id: str, text: str, header: str = "", timeout_ms: int = 3000) -> bool:
        """åæå®ä¼è¯åéå¼¹çªæ¶æ¯ï¼åæ°èµ° query paramsï¼"""
        try:
            params = {"Text": text}
            if header:
                params["Header"] = header
            if timeout_ms:
                params["TimeoutMs"] = timeout_ms
            resp = await self.post(f"/Sessions/{session_id}/Message", params=params)
            return resp.status_code in (200, 204)
        except Exception as e:
            logger.error("åéæ¶æ¯å°ä¼è¯ %s å¤±è´¥: %s", session_id, e)
            return False
        except Exception as e:
            logger.error("åéæ¶æ¯å°ä¼è¯ %s å¤±è´¥: %s", session_id, e)
            return False

    async def kick_session(self, session_id: str, reason: str = "ç®¡çåå¼ºå¶ä¸­æ­¢æ­æ¾") -> bool:
        """è¸¢åºæ­æ¾ä¼è¯ï¼ä»åæ­¢æ­æ¾ï¼å¯¹302æ æï¼"""
        try:
            resp = await self.post(f"/Sessions/{session_id}/Playing/Stop", json={})
            return resp.status_code in (200, 204)
        except Exception as e:
            logger.error("è¸¢åºä¼è¯ %s å¤±è´¥: %s", session_id, e)
            return False

    async def force_kick(self, session_id: str, device_id: str = "") -> dict:
        """
        å¼ºå¶è¸¢åºï¼ååæ­¢æ­æ¾ï¼åå é¤è®¾å¤å­è¯ã
        å¯¹ 302 æ­æ¾ææï¼å è®¾å¤åå®¢æ·ç«¯æ æ³è·åæ°é¾æ¥ï¼ã
        """
        result = {"stopped": False, "device_deleted": False}
        try:
            resp = await self.post(f"/Sessions/{session_id}/Playing/Stop", json={})
            result["stopped"] = resp.status_code in (200, 204)
        except Exception as e:
            logger.error("åæ­¢æ­æ¾ %s å¤±è´¥: %s", session_id, e)

        if device_id:
            result["device_deleted"] = await self.delete_device(device_id)

        return result

    async def ban_user(self, user_id: str) -> bool:
        """ç¦ç¨ç¨æ·"""
        try:
            resp = await self.get(f"/Users/{user_id}")
            if resp.status_code != 200:
                return False
            policy = resp.json().get("Policy", {})
            policy["IsDisabled"] = True
            resp2 = await self.post(f"/Users/{user_id}/Policy", json=policy)
            return resp2.status_code in (200, 204)
        except Exception as e:
            logger.error("å°ç¦ç¨æ· %s å¤±è´¥: %s", user_id, e)
            return False

    async def unban_user(self, user_id: str) -> bool:
        """å¯ç¨ç¨æ·"""
        try:
            resp = await self.get(f"/Users/{user_id}")
            if resp.status_code != 200:
                return False
            policy = resp.json().get("Policy", {})
            policy["IsDisabled"] = False
            resp2 = await self.post(f"/Users/{user_id}/Policy", json=policy)
            return resp2.status_code in (200, 204)
        except Exception as e:
            logger.error("è§£å°ç¨æ· %s å¤±è´¥: %s", user_id, e)
            return False

    async def get_devices(self) -> list[dict]:
        """è·åè®¾å¤åè¡¨"""
        try:
            resp = await self.get("/Devices")
            resp.raise_for_status()
            data = resp.json()
            return data.get("Items", []) if isinstance(data, dict) else data
        except Exception:
            return []

# ââ å¨å±åä¾ ââââââââââââââââââââââââââââââââââââââââââââââââââ

emby = EmbyAdapter()
