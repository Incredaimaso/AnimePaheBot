# ---------- Inline Handler ----------
# This Bot Made By [RAHAT](https://t.me/r4h4t_69)
# Anyone Can Modify As They Like
# Just don't remove the credit ❤️

import logging
from pyrogram import Client, filters
from pyrogram.types import (
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from pyrogram.enums import ParseMode
from plugins.headers import session
from plugins.callback import store_callback_data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@Client.on_inline_query()
async def inline_search(client: Client, inline_query: InlineQuery):
    """Handle inline queries and return anime search results."""
    try:
        query = inline_query.query.strip()

        if not query:
            await inline_query.answer(
                results=[],
                switch_pm_text="🔍 Type an anime name to search",
                switch_pm_parameter="start",
                cache_time=3
            )
            return

        url = f"https://animepahe.si/api?m=search&q={query}"
        res = session.get(url).json()

        data = res.get("data", [])
        if not data:
            await inline_query.answer(
                results=[],
                switch_pm_text="❌ No results found",
                switch_pm_parameter="not_found",
                cache_time=3
            )
            return

        results = []
        for anime in data[:25]:  # Limit to 25 results
            title = anime.get("title", "Unknown")
            season = anime.get("season", "N/A")
            year = anime.get("year", "N/A")
            episodes = anime.get("episodes", "N/A")
            poster = anime.get("poster") or ""

            session_id = anime.get("session")
            if not session_id:
                continue

            # Store safe callback data
            safe_cb = store_callback_data("anime", session_id)

            results.append(
                InlineQueryResultArticle(
                    title=title,
                    description=f"📅 {season} {year} | 🎬 {episodes} eps",
                    thumb_url=poster,
                    input_message_content=InputTextMessageContent(
                        message_text=f"<b>{title}</b>\n\nSelect an option below 👇",
                        parse_mode=ParseMode.HTML,
                        disable_web_page_preview=True
                    ),
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [InlineKeyboardButton("📺 View Episodes", callback_data=safe_cb)]
                        ]
                    )
                )
            )

        await inline_query.answer(results=results, cache_time=3)

    except Exception as e:
        logger.error(f"inline_search error: {e}")
        try:
            await inline_query.answer(
                results=[],
                switch_pm_text="⚠️ Error occurred",
                switch_pm_parameter="error",
                cache_time=3
            )
        except Exception:
            pass
