# ---------- Inline Search Handler ----------
# This Bot Made By [RAHAT](https://t.me/r4h4t_69)
# Anyone Can Modify As They Like
# Just don't remove the credit ❤️

from pyrogram import Client
from pyrogram.types import (
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from pyrogram.enums import ParseMode
from plugins.headers import session
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# --- Inline query: search anime ---
@Client.on_inline_query()
async def inline_search(client: Client, inline_query: InlineQuery):
    query = inline_query.query.strip()

    if not query:
        await inline_query.answer(
            results=[],
            switch_pm_text="Type anime name to search 🔎",
            switch_pm_parameter="start",
            cache_time=0
        )
        return

    api_url = f"https://animepahe.ru/api?m=search&q={query}&l=8"
    try:
        res = session.get(api_url).json()
    except Exception as e:
        logger.error(f"inline_search error: {e}")
        await inline_query.answer([], cache_time=0, is_personal=True)
        return

    results = []
    for anime in res.get("data", []):
        title = anime.get("title") or "Unknown"
        poster = anime.get("poster")
        session_id = anime.get("session")

        desc = anime.get("type", "Anime")
        if anime.get("episodes"):
            desc += f" • {anime['episodes']} eps"
        if anime.get("season") and anime.get("year"):
            desc += f" • {anime['season']} {anime['year']}"

        buttons = InlineKeyboardMarkup([[
            InlineKeyboardButton("📺 Show Episodes", callback_data=f"anime_{session_id}")
        ]])

        results.append(
            InlineQueryResultArticle(
                title=title,
                description=desc,
                thumb_url=poster,
                input_message_content=InputTextMessageContent(
                    f"<b>{title}</b>\n\nTap below to view episodes ⬇️",
                    parse_mode=ParseMode.HTML
                ),
                reply_markup=buttons
            )
        )

    await inline_query.answer(results=results, cache_time=0, is_personal=True)
