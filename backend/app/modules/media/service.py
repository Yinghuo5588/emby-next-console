from app.core.emby import emby
from app.core.tmdb import tmdb
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text


class MediaService:
    def __init__(self, db: AsyncSession | None = None):
        self.db = db

    async def get_libraries(self) -> list[dict]:
        """获取 Emby 媒体库列表"""
        try:
            views = await emby.get_views()
            return [
                {"id": v.get("Id"), "name": v.get("Name"), "type": v.get("CollectionType")}
                for v in views
            ]
        except Exception:
            return []

    async def find_missing_episodes(self) -> list[dict]:
        """查找缺集的剧集系列"""
        if not self.db:
            return []

        # 从本地数据库查询：哪些剧集有部分集但不是全集
        # 使用 playback_sessions 中的数据推断
        query = text("""
            SELECT 
                series_name,
                COUNT(DISTINCT season_number) as seasons,
                COUNT(DISTINCT episode_number) as episodes_found
            FROM playback_sessions
            WHERE series_name IS NOT NULL 
              AND season_number IS NOT NULL
            GROUP BY series_name
            ORDER BY episodes_found DESC
            LIMIT 50
        """)
        try:
            result = await self.db.execute(query)
            rows = result.fetchall()
            # 返回有缺集可能的结果（集数少于正常值）
            missing = []
            for row in rows:
                if row.episodes_found < 10:  # 简单启发式
                    missing.append({
                        "series_name": row.series_name,
                        "seasons": row.seasons,
                        "episodes_found": row.episodes_found,
                    })
            return missing
        except Exception:
            return []

    async def find_duplicates(self) -> list[dict]:
        """检测重复媒体（同名不同版本）"""
        try:
            response = await emby.get_items(
                include_item_types="Movie",
                fields="Path,MediaSources",
                limit=500,
            )
            items = response.get("Items", [])
            # 按名称分组找重复
            name_map: dict[str, list] = {}
            for item in items:
                name = item.get("Name", "")
                if name not in name_map:
                    name_map[name] = []
                name_map[name].append(item)

            duplicates = []
            for name, items_list in name_map.items():
                if len(items_list) > 1:
                    duplicates.append({
                        "name": name,
                        "count": len(items_list),
                        "items": [
                            {
                                "id": i.get("Id"),
                                "path": i.get("Path", ""),
                                "size_mb": round(
                                    sum(
                                        s.get("Size", 0)
                                        for s in i.get("MediaSources", [])
                                    )
                                    / 1024 / 1024,
                                    1,
                                ),
                            }
                            for i in items_list
                        ],
                    })
            return sorted(duplicates, key=lambda x: x["count"], reverse=True)[:50]
        except Exception:
            return []

    async def search_tmdb(self, query: str, type: str = "movie", page: int = 1) -> dict:
        """搜索 TMDB"""
        if type == "movie":
            data = await tmdb.search_movie(query, page)
        else:
            data = await tmdb.search_tv(query, page)

        results = []
        for item in data.get("results", [])[:20]:
            results.append({
                "tmdb_id": item.get("id"),
                "title": item.get("title") or item.get("name"),
                "overview": (item.get("overview") or "")[:200],
                "poster": tmdb.poster_url(item.get("poster_path")),
                "backdrop": tmdb.backdrop_url(item.get("backdrop_path")),
                "release_date": item.get("release_date") or item.get("first_air_date"),
                "vote_average": item.get("vote_average"),
            })

        return {
            "results": results,
            "page": data.get("page", 1),
            "total_pages": data.get("total_pages", 1),
        }

    async def get_upcoming(self, type: str = "movie", page: int = 1) -> dict:
        """获取即将上映"""
        if type == "movie":
            data = await tmdb.upcoming_movies(page)
        else:
            data = await tmdb.on_the_air(page)

        results = []
        for item in data.get("results", [])[:20]:
            results.append({
                "tmdb_id": item.get("id"),
                "title": item.get("title") or item.get("name"),
                "overview": (item.get("overview") or "")[:200],
                "poster": tmdb.poster_url(item.get("poster_path")),
                "backdrop": tmdb.backdrop_url(item.get("backdrop_path")),
                "release_date": item.get("release_date") or item.get("first_air_date"),
                "vote_average": item.get("vote_average"),
            })

        return {"results": results, "page": data.get("page", 1)}

    async def get_tmdb_detail(self, tmdb_id: int, type: str = "movie") -> dict:
        """获取 TMDB 详情"""
        if type == "movie":
            data = await tmdb.get_movie(tmdb_id)
        else:
            data = await tmdb.get_tv(tmdb_id)

        return {
            "tmdb_id": data.get("id"),
            "title": data.get("title") or data.get("name"),
            "overview": data.get("overview"),
            "poster": tmdb.poster_url(data.get("poster_path"), "w500"),
            "backdrop": tmdb.backdrop_url(data.get("backdrop_path")),
            "genres": [g.get("name") for g in data.get("genres", [])],
            "release_date": data.get("release_date") or data.get("first_air_date"),
            "vote_average": data.get("vote_average"),
            "runtime": data.get("runtime"),
            "seasons": [
                {"number": s.get("season_number"), "name": s.get("name"), "episodes": s.get("episode_count")}
                for s in data.get("seasons", [])
            ] if type == "tv" else None,
        }