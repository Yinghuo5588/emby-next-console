from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.poster import PosterTemplate, GeneratedPoster
from app.core.emby import emby


class PosterService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_templates(self) -> list[dict]:
        stmt = select(PosterTemplate).order_by(PosterTemplate.id)
        result = await self.db.execute(stmt)
        return [self._template_to_dict(t) for t in result.scalars().all()]

    async def create_template(self, data: dict) -> dict:
        tpl = PosterTemplate(
            name=data["name"],
            description=data.get("description"),
            layout=data.get("layout", "vertical"),
            background_color=data.get("background_color", "#1a1a2e"),
            text_color=data.get("text_color", "#ffffff"),
            accent_color=data.get("accent_color", "#e94560"),
            columns=data.get("columns", 3),
            show_rating=data.get("show_rating", True),
            show_year=data.get("show_year", True),
            show_genres=data.get("show_genres", False),
            cover_text=data.get("cover_text"),
        )
        self.db.add(tpl)
        await self.db.commit()
        await self.db.refresh(tpl)
        return self._template_to_dict(tpl)

    async def generate_poster(self, data: dict) -> dict:
        template_id = data.get("template_id")
        item_ids = data.get("item_ids", [])
        title = data.get("title", "Emby 合集")

        # 获取模板样式
        template = None
        if template_id:
            stmt = select(PosterTemplate).where(PosterTemplate.id == template_id)
            result = await self.db.execute(stmt)
            template = result.scalar_one_or_none()

        bg = template.background_color if template else "#1a1a2e"
        text_color = template.text_color if template else "#ffffff"
        accent = template.accent_color if template else "#e94560"
        columns = template.columns if template else 3
        show_rating = template.show_rating if template else True
        show_year = template.show_year if template else True

        # 获取媒体信息
        items = []
        for iid in item_ids[:20]:
            try:
                item_data = await emby.get_item(iid)
                items.append(item_data)
            except Exception:
                continue

        if not items:
            try:
                items = await emby.get_items(sort_by="DateCreated", sort_order="Descending", limit=12)
            except Exception:
                items = []

        html = self._build_html(title, items, bg, text_color, accent, columns, show_rating, show_year)

        poster = GeneratedPoster(
            template_id=template_id,
            title=title,
            item_ids=item_ids,
            html_content=html,
            status="generated",
        )
        self.db.add(poster)
        await self.db.commit()
        await self.db.refresh(poster)
        return self._poster_to_dict(poster)

    async def list_generated(self, page: int = 1, page_size: int = 20) -> dict:
        stmt = select(GeneratedPoster).order_by(GeneratedPoster.id.desc())
        count_stmt = select(func.count()).select_from(GeneratedPoster)
        total = (await self.db.execute(count_stmt)).scalar() or 0
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(stmt)
        return {"items": [self._poster_to_dict(p) for p in result.scalars().all()], "total": total}

    async def get_poster(self, poster_id: int) -> dict | None:
        stmt = select(GeneratedPoster).where(GeneratedPoster.id == poster_id)
        result = await self.db.execute(stmt)
        p = result.scalar_one_or_none()
        return self._poster_to_dict(p) if p else None

    def _build_html(self, title, items, bg, text_color, accent, columns, show_rating, show_year):
        cards_html = ""
        for item in items[:columns * 4]:
            name = item.get("Name", "未知")
            rating = item.get("CommunityRating")
            year = item.get("ProductionYear")
            img_url = f"/Items/{item.get('Id')}/Images/Primary?maxWidth=300" if item.get("Id") else ""

            meta_parts = []
            if show_year and year:
                meta_parts.append(str(year))
            if show_rating and rating:
                meta_parts.append(f"⭐ {rating:.1f}")
            meta_text = " · ".join(meta_parts)

            cards_html += f"""
            <div class="card">
                <img src="{img_url}" alt="{name}" onerror="this.style.display='none'" />
                <div class="card-info">
                    <div class="card-name">{name}</div>
                    {"<div class='card-meta'>" + meta_text + "</div>" if meta_text else ""}
                </div>
            </div>"""

        return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ background:{bg}; color:{text_color}; font-family:-apple-system,sans-serif; padding:24px; }}
.header {{ text-align:center; margin-bottom:24px; }}
.header h1 {{ font-size:28px; margin-bottom:8px; }}
.header .accent {{ color:{accent}; }}
.grid {{ display:grid; grid-template-columns:repeat({columns}, 1fr); gap:16px; }}
.card {{ background:rgba(255,255,255,0.06); border-radius:12px; overflow:hidden; }}
.card img {{ width:100%; aspect-ratio:2/3; object-fit:cover; }}
.card-info {{ padding:10px 12px; }}
.card-name {{ font-size:14px; font-weight:600; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
.card-meta {{ font-size:12px; color:rgba(255,255,255,0.6); margin-top:4px; }}
.footer {{ text-align:center; margin-top:24px; font-size:12px; color:rgba(255,255,255,0.4); }}
</style></head>
<body>
<div class="header"><h1 class="accent">{title}</h1></div>
<div class="grid">{cards_html}</div>
<div class="footer">Generated by Emby Next Console</div>
</body></html>"""

    def _template_to_dict(self, t: PosterTemplate) -> dict:
        return {
            "id": t.id, "name": t.name, "description": t.description,
            "layout": t.layout, "background_color": t.background_color,
            "text_color": t.text_color, "accent_color": t.accent_color,
            "columns": t.columns, "show_rating": t.show_rating,
            "show_year": t.show_year, "show_genres": t.show_genres,
            "cover_text": t.cover_text,
        }

    def _poster_to_dict(self, p: GeneratedPoster) -> dict:
        return {
            "id": p.id, "template_id": p.template_id, "title": p.title,
            "item_ids": p.item_ids, "status": p.status,
        }
