import httpx
from app.core.settings import settings

class TMDBClient:
    BASE = "https://api.themoviedb.org/3"

    def __init__(self, api_key: str = ""):
        self.api_key = api_key or getattr(settings, "TMDB_API_KEY", "")
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if not self._client:
            self._client = httpx.AsyncClient(timeout=10)
        return self._client

    async def _get(self, path: str, params: dict | None = None) -> dict:
        client = await self._get_client()
        p = {"api_key": self.api_key, "language": "zh-CN", **(params or {})}
        resp = await client.get(f"{self.BASE}{path}", params=p)
        resp.raise_for_status()
        return resp.json()

    async def search_movie(self, query: str, page: int = 1) -> dict:
        return await self._get("/search/movie", {"query": query, "page": page})

    async def search_tv(self, query: str, page: int = 1) -> dict:
        return await self._get("/search/tv", {"query": query, "page": page})

    async def get_movie(self, tmdb_id: int) -> dict:
        return await self._get(f"/movie/{tmdb_id}")

    async def get_tv(self, tmdb_id: int) -> dict:
        return await self._get(f"/tv/{tmdb_id}")

    async def get_tv_season(self, tmdb_id: int, season_number: int) -> dict:
        return await self._get(f"/tv/{tmdb_id}/season/{season_number}")

    async def upcoming_movies(self, page: int = 1) -> dict:
        return await self._get("/movie/upcoming", {"page": page})

    async def on_the_air(self, page: int = 1) -> dict:
        return await self._get("/tv/on_the_air", {"page": page})

    def poster_url(self, path: str | None, size: str = "w300") -> str | None:
        if not path:
            return None
        return f"https://image.tmdb.org/t/p/{size}{path}"

    def backdrop_url(self, path: str | None, size: str = "w780") -> str | None:
        if not path:
            return None
        return f"https://image.tmdb.org/t/p/{size}{path}"

    async def close(self):
        if self._client:
            await self._client.aclose()

tmdb = TMDBClient()