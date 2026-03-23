"""
媒体代理 — 参考 emby-pulse 实现
- /api/v1/proxy/image/{item_id}/{img_type} — 封面直出（支持剧集ID转换）
- /api/v1/proxy/smart_image  — 智能封面（Emby → 再搜 → TMDB兜底）
- /api/v1/proxy/user_image/{user_id} — 用户头像
"""
import re
import urllib.parse
import logging

import httpx
from fastapi import APIRouter, Query, Response

from app.core.emby import emby
from app.core.settings import settings

logger = logging.getLogger("app.proxy")
router = APIRouter(prefix="/proxy", tags=["proxy"])

# 缓存：item_id → resolved_id 或 TMDB URL
smart_image_cache: dict[str, str] = {}


# ═══════════════════════════════════════════════════════════
# 剧集 ID 智能转换（参考 emby-pulse get_real_image_id_robust）
# ═══════════════════════════════════════════════════════════

def _extract_season_number(name: str) -> int | None:
    """从名称提取季号: '唐朝诡事录 - 第 2 季' -> 2"""
    m = re.search(r'第\s*(\d+)\s*季', name)
    if m:
        return int(m.group(1))
    m2 = re.search(r'S0*(\d+)', name, re.I)
    if m2:
        return int(m2.group(1))
    return None


async def _get_real_image_id(item_id: str) -> str:
    """
    智能 ID 转换：把单集 ID 转成剧集/季 ID
    参考 emby-pulse get_real_image_id_robust，三层兜底
    失败返回原始 item_id（不是 None）
    """
    # ── 第1层：逐个查询 Fields ──
    try:
        resp = await emby.get(f"/Items/{item_id}", params={"Fields": "SeriesId,ParentId,SeasonId"})
        if resp.status_code == 200:
            data = resp.json()
            item_type = data.get("Type")

            if item_type == "Episode":
                # 先试季
                if data.get("SeasonId"):
                    s_resp = await emby.get(f"/Items/{data['SeasonId']}")
                    if s_resp.status_code == 200 and s_resp.json().get("ImageTags", {}).get("Primary"):
                        return data["SeasonId"]
                # 再试剧集
                if data.get("SeriesId"):
                    return data["SeriesId"]
                # 最后试父级
                if data.get("ParentId"):
                    return data["ParentId"]

            elif item_type == "Season":
                if data.get("SeriesId"):
                    return data["SeriesId"]

            elif item_type == "Series":
                # 已经是剧集，直接返回
                return item_id

            # 兜底：有 SeriesId 就用
            if data.get("SeriesId"):
                return data["SeriesId"]
    except Exception:
        pass

    # ── 第2层：查祖先 ──
    try:
        resp = await emby.get(f"/Items/{item_id}/Ancestors")
        if resp.status_code == 200:
            for ancestor in resp.json():
                if ancestor.get("Type") == "Series":
                    return ancestor["Id"]
                if ancestor.get("Type") == "Season":
                    return ancestor["Id"]
    except Exception:
        pass

    # ── 第3层：Recursive 查询兜底 ──
    try:
        resp = await emby.get("/Items", params={"Ids": item_id, "Fields": "SeriesId", "Recursive": "true"})
        if resp.status_code == 200:
            items = resp.json().get("Items", [])
            if items and items[0].get("SeriesId"):
                return items[0]["SeriesId"]
    except Exception:
        pass

    # 失败返回原始 ID
    return item_id


# ═══════════════════════════════════════════════════════════
# 直出封面（兼容 emby-pulse 路径格式）
# ═══════════════════════════════════════════════════════════

@router.get("/image/{item_id}/{img_type}")
async def proxy_image(item_id: str, img_type: str):
    """直出封面，支持剧集ID智能转换"""
    target_id = await _get_real_image_id(item_id) if img_type.lower() == "primary" else item_id

    params = {"maxHeight": 600, "maxWidth": 400, "quality": 90}

    try:
        resp = await emby.get(f"/Items/{target_id}/Images/{img_type}", params=params)
        if resp.status_code == 200 and len(resp.content) > 100:
            return Response(
                content=resp.content,
                media_type=resp.headers.get("Content-Type", "image/jpeg"),
                headers={"Cache-Control": "public, max-age=3600"},
            )

        # 如果转换后还是 404，用原始 ID 再试
        if resp.status_code == 404 and target_id != item_id:
            resp2 = await emby.get(f"/Items/{item_id}/Images/{img_type}", params=params)
            if resp2.status_code == 200 and len(resp2.content) > 100:
                return Response(
                    content=resp2.content,
                    media_type=resp2.headers.get("Content-Type", "image/jpeg"),
                    headers={"Cache-Control": "public, max-age=3600"},
                )
    except Exception:
        pass

    return Response(status_code=404)


# ═══════════════════════════════════════════════════════════
# 智能封面（Emby → 内库再搜 → TMDB 三重兜底）
# ═══════════════════════════════════════════════════════════

@router.get("/smart_image")
async def smart_image(
    item_id: str,
    type: str = Query("Primary"),
    name: str = Query(""),
):
    """
    三重防御封面获取：
    1. Emby 原生（带剧集 ID 转换）
    2. Emby 内库搜索兜底
    3. TMDB 终极兜底
    """
    img_type = type

    # 检查缓存
    cached = smart_image_cache.get(item_id)
    if cached:
        if cached.startswith("http"):
            # 缓存的是 TMDB URL
            try:
                async with httpx.AsyncClient(timeout=8) as client:
                    resp = await client.get(cached)
                    if resp.status_code == 200:
                        return Response(content=resp.content, media_type="image/jpeg",
                                        headers={"Cache-Control": "public, max-age=86400"})
            except Exception:
                pass
        else:
            # 缓存的是 Emby item ID
            item_id = cached

    # 图片参数（与 emby-pulse 一致）
    if img_type.lower() == "backdrop":
        params = {"maxWidth": 1920, "quality": 80}
    else:
        params = {"maxHeight": 800, "maxWidth": 600, "quality": 90}

    # ── 第1级：Emby 原生（带剧集 ID 转换）──
    target_id = await _get_real_image_id(item_id) if img_type.lower() == "primary" else item_id
    logger.info(f"[smart_image] item_id={item_id} target_id={target_id} type={img_type} name={name or ''}")

    try:
        resp = await emby.get(f"/Items/{target_id}/Images/{img_type}", params=params)
        logger.info(f"[smart_image] Emby L1: status={resp.status_code} size={len(resp.content)}")
        if resp.status_code == 200 and len(resp.content) > 100:
            return Response(
                content=resp.content,
                media_type=resp.headers.get("Content-Type", "image/jpeg"),
                headers={"Cache-Control": "public, max-age=86400"},
            )
    except Exception:
        pass

    # ── 第2级：Emby 内库搜索兜底 ──
    # 优先从 name 参数取（前端传的），再从 Emby 获取
    clean_name = name.split(" - ")[0].strip() if name else ""
    if not clean_name:
        try:
            resp = await emby.get(f"/Items/{item_id}")
            if resp.status_code == 200:
                clean_name = resp.json().get("Name", "")
        except Exception:
            pass

    if clean_name:
        try:
            s_resp = await emby.get("/Items", params={
                "SearchTerm": clean_name,
                "IncludeItemTypes": "Movie,Series,Episode",
                "Recursive": "true",
            })
            if s_resp.status_code == 200:
                items = s_resp.json().get("Items", [])
                if items:
                    new_id = items[0]["Id"]
                    if items[0].get("Type") in ("Episode", "Season", "Series"):
                        new_id = await _get_real_image_id(new_id)
                    smart_image_cache[item_id] = new_id

                    n_resp = await emby.get(f"/Items/{new_id}/Images/{img_type}", params=params)
                    if n_resp.status_code == 200 and len(n_resp.content) > 100:
                        return Response(
                            content=n_resp.content,
                            media_type=n_resp.headers.get("Content-Type", "image/jpeg"),
                            headers={"Cache-Control": "public, max-age=86400"},
                        )
        except Exception:
            pass

    # ── 第3级：TMDB 终极兜底 ──
    tmdb_key = settings.TMDB_API_KEY
    season_num = _extract_season_number(clean_name) if clean_name else None

    if clean_name and tmdb_key:
        try:
            async with httpx.AsyncClient(timeout=8) as client:
                tmdb_url = f"https://api.themoviedb.org/3/search/multi?api_key={tmdb_key}&language=zh-CN&query={urllib.parse.quote(clean_name)}"
                t_resp = await client.get(tmdb_url)

                if t_resp.status_code == 200:
                    results = t_resp.json().get("results", [])
                    for res in results:
                        # 剧集 + 有季号 → 查季海报
                        if res.get("media_type") == "tv" and season_num is not None and img_type.lower() == "primary":
                            tv_id = res["id"]
                            s_url = f"https://api.themoviedb.org/3/tv/{tv_id}/season/{season_num}?api_key={tmdb_key}&language=zh-CN"
                            try:
                                s_resp = await client.get(s_url)
                                if s_resp.status_code == 200:
                                    s_data = s_resp.json()
                                    if s_data.get("poster_path"):
                                        final_url = f"https://image.tmdb.org/t/p/w500{s_data['poster_path']}"
                                        smart_image_cache[item_id] = final_url
                                        img_resp = await client.get(final_url)
                                        if img_resp.status_code == 200:
                                            return Response(
                                                content=img_resp.content,
                                                media_type="image/jpeg",
                                                headers={"Cache-Control": "public, max-age=86400"},
                                            )
                            except Exception:
                                pass

                        # 电影/剧集直接拿海报
                        if res.get("media_type") in ("movie", "tv"):
                            if img_type.lower() == "backdrop":
                                img_path = res.get("backdrop_path")
                            else:
                                img_path = res.get("poster_path")
                            if img_path:
                                tmdb_img_url = f"https://image.tmdb.org/t/p/w500{img_path}"
                                smart_image_cache[item_id] = tmdb_img_url
                                img_resp = await client.get(tmdb_img_url)
                                if img_resp.status_code == 200:
                                    return Response(
                                        content=img_resp.content,
                                        media_type="image/jpeg",
                                        headers={"Cache-Control": "public, max-age=86400"},
                                    )
                            break
        except Exception:
            pass

    # ── 占位图（1x1 透明 PNG）──
    placeholder = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
    return Response(content=placeholder, media_type="image/png")


# ═══════════════════════════════════════════════════════════
# 用户头像（参考 emby-pulse）
# ═══════════════════════════════════════════════════════════

@router.get("/user_image/{user_id}")
async def user_image_path(user_id: str):
    """用户头像（路径格式）"""
    return await _get_user_image(user_id)


@router.get("/user_image")
async def user_image_query(user_id: str = Query("")):
    """用户头像（query格式）"""
    return await _get_user_image(user_id)


async def _get_user_image(user_id: str):
    """用户头像代理：Emby → SVG 占位符兜底，始终返回 200"""
    if not user_id:
        return Response(status_code=400)

    logger.info(f"[user_image] 请求 user_id={user_id}")

    # Emby 原生头像（与 emby-pulse 参数一致）
    try:
        resp = await emby.get(f"/Users/{user_id}/Images/Primary", params={
            "width": 200, "height": 200, "mode": "Crop", "quality": 90,
        })
        logger.info(f"[user_image] Emby 响应: status={resp.status_code} size={len(resp.content)}")
        if resp.status_code == 200 and len(resp.content) > 100:
            return Response(
                content=resp.content,
                media_type=resp.headers.get("Content-Type", "image/jpeg"),
                headers={"Cache-Control": "public, max-age=3600"},
            )
    except Exception as e:
        logger.error(f"[user_image] Emby 异常: {e}")

    # SVG 占位符兜底（始终返回 200，避免前端缓存 404）
    try:
        resp = await emby.get(f"/Users/{user_id}")
        if resp.status_code == 200:
            username = resp.json().get("Name", user_id[:6])
        else:
            username = user_id[:6]
    except Exception:
        username = user_id[:6]

    initial = (username[0] if username else "?").upper()
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200" viewBox="0 0 200 200">
      <rect width="200" height="200" rx="100" fill="#3b82f6"/>
      <text x="100" y="100" dy=".35em" text-anchor="middle" fill="white"
        font-size="80" font-family="system-ui,sans-serif" font-weight="700">{initial}</text>
    </svg>'''
    logger.info(f"[user_image] SVG fallback username={username}")
    return Response(content=svg, media_type="image/svg+xml",
                    headers={"Cache-Control": "public, max-age=3600"})
