from __future__ import annotations
import httpx
from app.core.settings import settings


class EmbyUserService:
    def __init__(self):
        self.base = settings.EMBY_HOST.rstrip("/")
        self.api_key = settings.EMBY_API_KEY
        self.headers = {"X-Emby-Token": self.api_key, "Content-Type": "application/json"}

    async def create_emby_user(self, username: str, password: str | None = None) -> dict:
        """创建 Emby 用户"""
        async with httpx.AsyncClient() as client:
            # Step 1: 创建用户
            resp = await client.post(
                f"{self.base}/emby/Users/New",
                headers=self.headers,
                json={"Name": username},
            )
            resp.raise_for_status()
            user = resp.json()
            user_id = user["Id"]
            
            # Step 2: 设置密码
            if password:
                await client.post(
                    f"{self.base}/emby/Users/{user_id}/Password",
                    headers=self.headers,
                    json={"NewPw": password},
                )
            
            return user

    async def get_user_policy(self, user_id: str) -> dict:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{self.base}/emby/Users/{user_id}/Policy", headers=self.headers)
            resp.raise_for_status()
            return resp.json()

    async def update_user_policy(self, user_id: str, policy: dict):
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base}/emby/Users/{user_id}/Policy",
                headers=self.headers,
                json=policy,
            )
            resp.raise_for_status()

    async def get_user_configuration(self, user_id: str) -> dict:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{self.base}/emby/Users/{user_id}/Configuration", headers=self.headers)
            resp.raise_for_status()
            return resp.json()

    async def update_user_configuration(self, user_id: str, config: dict):
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base}/emby/Users/{user_id}/Configuration",
                headers=self.headers,
                json=config,
            )
            resp.raise_for_status()

    async def delete_emby_user(self, user_id: str):
        async with httpx.AsyncClient() as client:
            resp = await client.delete(f"{self.base}/emby/Users/{user_id}", headers=self.headers)
            resp.raise_for_status()

    async def force_logout(self, user_id: str):
        """强制下线用户所有会话"""
        async with httpx.AsyncClient() as client:
            # 获取用户会话
            resp = await client.get(f"{self.base}/emby/Sessions", headers=self.headers)
            sessions = resp.json()
            for session in sessions:
                if session.get("UserId") == user_id:
                    session_id = session.get("Id")
                    if session_id:
                        await client.post(
                            f"{self.base}/emby/Sessions/{session_id}/Playing/Stop",
                            headers=self.headers,
                        )
    
    async def get_user_sessions(self, user_id: str) -> list[dict]:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{self.base}/emby/Sessions", headers=self.headers)
            sessions = resp.json()
            return [s for s in sessions if s.get("UserId") == user_id]