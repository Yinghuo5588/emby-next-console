"""
媒体代理 — 解决跨域+封面/头像回退
- /api/v1/proxy/smart_image → 媒体封面（Emby → TMDB 回退）
- /api/v1/proxy/user_image  → 用户头像（Emby → dicebear 回退）
"""
import urllib.parse

import httpx
from fastapi import APIRouter, Query, Response

from app.core.emby import emby
from app.core.settings import settings

router = APIRouter(prefix="/proxy", tags=["proxy"])

# ── 缓存 ───────────────────────────────────────────────────
_cache: dict[str, str | bytes] = {}
_cache_meta: dict[str, dict] = {}


# ── smart_image: 媒体封面 ─────────────────────────────────

@router.get("/smart_image")
async def smart_image(
    item_id: str,
    type: str = Query("Primary"),
    name: str = Query(""),
    year: str = Query(""),
):
    """智能封面代理：Emby → TMDB 回退"""
    cache_key = f"img:{item_id}:{type}"
    if cache_key in _cache:
        data = _cache[cache_key]
        meta = _cache_meta.get(cache_key, {})
        return Response(content=data, media_type=meta.get("type", "image/jpeg"))

    # 1) Emby 原生
    try:
        resp = await emby.get(f"/Items/{item_id}/Images/{type}", params={"quality": 90})
        if resp.status_code == 200 and len(resp.content) > 100:
            content = resp.content
            ctype = resp.headers.get("content-type", "image/jpeg")
            _cache[cache_key] = content
            _cache_meta[cache_key] = {"type": ctype}
            return Response(content=content, media_type=ctype)
        # Emby 返回 404 或空内容 → 继续走 TMDB 回退
    except Exception:
        pass

    # 2) TMDB 回退 — 先从 Emby 拿名称，再搜
    tmdb_key = settings.TMDB_API_KEY
    if tmdb_key:
        # 从 Emby 获取 item 名称
        if not name:
            try:
                resp = await emby.get(f"/Items/{item_id}")
                if resp.status_code == 200:
                    data = resp.json()
                    name = data.get("Name", "")
            except Exception:
                pass

        if name:
            try:
                tmdb_url = await _tmdb_poster(name, tmdb_key, type)
                if tmdb_url:
                    async with httpx.AsyncClient(timeout=8) as client:
                        resp = await client.get(tmdb_url)
                        if resp.status_code == 200:
                            content = resp.content
                            ctype = resp.headers.get("content-type", "image/jpeg")
                            _cache[cache_key] = content
                            _cache_meta[cache_key] = {"type": ctype}
                            return Response(content=content, media_type=ctype)
            except Exception:
                pass

    # 3) 占位图（1x1 透明 PNG）
    placeholder = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
    return Response(content=placeholder, media_type="image/png")


async def _tmdb_poster(name: str, api_key: str, img_type: str) -> str | None:
    """通过 TMDB 搜索获取海报"""
    # 清理剧集名称（去掉 S01E01 之类的）
    clean = name.split(" - ")[0].strip()
    import re
    clean = re.sub(r"\s*[Ss]\d+.*", "", clean).strip()

    base = "https://api.themoviedb.org/3"
    params = {"api_key": api_key, "query": clean, "language": "zh-CN"}

    async with httpx.AsyncClient(timeout=8) as client:
        # 先搜电影
        try:
            r = await client.get(f"{base}/search/movie", params=params)
            if r.status_code == 200:
                results = r.json().get("results", [])
                if results:
                    path = results[0].get("poster_path")
                    if path:
                        return f"https://image.tmdb.org/t/p/w500{path}"
        except Exception:
            pass

        # 再搜剧集
        try:
            r = await client.get(f"{base}/search/tv", params=params)
            if r.status_code == 200:
                results = r.json().get("results", [])
                if results:
                    path = results[0].get("poster_path")
                    if path:
                        return f"https://image.tmdb.org/t/p/w500{path}"
        except Exception:
            pass

    return None


# ── user_image: 用户头像 ──────────────────────────────────

@router.get("/user_image")
async def user_image(user_id: str):
    """用户头像代理：Emby → dicebear 回退"""
    cache_key = f"avatar:{user_id}"
    if cache_key in _cache:
        data = _cache[cache_key]
        meta = _cache_meta.get(cache_key, {})
        return Response(content=data, media_type=meta.get("type", "image/jpeg"))

    # 1) Emby 原生
    try:
        resp = await emby.get(f"/Users/{user_id}/Images/Primary", params={"quality": 90})
        if resp.status_code == 200 and len(resp.content) > 100:
            content = resp.content
            ctype = resp.headers.get("content-type", "image/jpeg")
            _cache[cache_key] = content
            _cache_meta[cache_key] = {"type": ctype}
            return Response(content=content, media_type=ctype)
    except Exception:
        pass

    # 2) dicebear 回退
    try:
        # 获取用户名
        resp = await emby.get(f"/Users/{user_id}")
        resp.raise_for_status()
        username = resp.json().get("Name", user_id[:6])
    except Exception:
        username = user_id[:6]

    seed = urllib.parse.quote(username)
    dicebear_url = f"https://api.dicebear.com/9.x/notionists/png?seed={seed}&size=128"

    try:
        async with httpx.AsyncClient(timeout=8) as client:
            resp = await client.get(dicebear_url)
            if resp.status_code == 200:
                content = resp.content
                ctype = resp.headers.get("content-type", "image/png")
                _cache[cache_key] = content
                _cache_meta[cache_key] = {"type": ctype}
                return Response(content=content, media_type=ctype)
    except Exception:
        pass

    # 3) 占位图
    placeholder = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
    return Response(content=placeholder, media_type="image/png")
