# ---------- Callback Handler ----------
# This Bot Made By [RAHAT](https://t.me/r4h4t_69)
# Anyone Can Modify As They Like
# Just don't remove the credit ❤️

from pyrogram import Client, filters
from pyrogram.types import (
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from pyrogram.enums import ParseMode
from plugins.headers import session
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# --- Handle anime selection (from inline query) ---
@Client.on_callback_query(filters.regex(r"^anime_"))
async def anime_callback(client: Client, callback_query: CallbackQuery):
    try:
        session_id = callback_query.data.split("_", 1)[1]

        # Fetch anime details from API
        url = f"https://animepahe.ru/api?m=release&id={session_id}&sort=episode_asc&page=1"
        res = session.get(url).json()

        episodes = res.get("data", [])
        if not episodes:
            await callback_query.answer("❌ No episodes found.", show_alert=True)
            return

        buttons = []
        for ep in episodes[:10]:  # first 10 episodes only
            ep_num = ep.get("episode")
            ep_id = ep.get("session")
            buttons.append([
                InlineKeyboardButton(f"Episode {ep_num}", callback_data=f"episode_{ep_id}")
            ])

        nav_buttons = [
            InlineKeyboardButton("⏪ Prev", callback_data=f"page_prev_{session_id}_1"),
            InlineKeyboardButton("Next ⏩", callback_data=f"page_next_{session_id}_2")
        ]

        buttons.append(nav_buttons)

        await callback_query.message.edit_text(
            "<b>📺 Episodes List</b>\n\nSelect an episode below:",
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode=ParseMode.HTML
        )

    except Exception as e:
        logger.error(f"anime_callback error: {e}")
        await callback_query.answer("⚠️ Something went wrong.", show_alert=True)


# --- Handle episode selection ---
@Client.on_callback_query(filters.regex(r"^episode_"))
async def episode_callback(client: Client, callback_query: CallbackQuery):
    try:
        ep_id = callback_query.data.split("_", 1)[1]

        url = f"https://animepahe.ru/api?m=embed&id={ep_id}"
        res = session.get(url).json()

        embed_url = res.get("data", {}).get("url")
        if not embed_url:
            await callback_query.answer("❌ Stream link not found.", show_alert=True)
            return

        buttons = InlineKeyboardMarkup([[
            InlineKeyboardButton("▶️ Watch Now", url=embed_url)
        ]])

        await callback_query.message.edit_text(
            f"<b>Episode Stream</b>\n\n<a href='{embed_url}'>Click here to watch</a>",
            reply_markup=buttons,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )

    except Exception as e:
        logger.error(f"episode_callback error: {e}")
        await callback_query.answer("⚠️ Something went wrong.", show_alert=True)


# --- Handle pagination (Prev / Next buttons) ---
@Client.on_callback_query(filters.regex(r"^page_"))
async def pagination_callback(client: Client, callback_query: CallbackQuery):
    try:
        parts = callback_query.data.split("_")
        action, session_id, page = parts[1], parts[2], int(parts[3])

        url = f"https://animepahe.ru/api?m=release&id={session_id}&sort=episode_asc&page={page}"
        res = session.get(url).json()

        episodes = res.get("data", [])
        if not episodes:
            await callback_query.answer("❌ No more episodes.", show_alert=True)
            return

        buttons = []
        for ep in episodes[:10]:
            ep_num = ep.get("episode")
            ep_id = ep.get("session")
            buttons.append([
                InlineKeyboardButton(f"Episode {ep_num}", callback_data=f"episode_{ep_id}")
            ])

        nav = []
        if page > 1:
            nav.append(InlineKeyboardButton("⏪ Prev", callback_data=f"page_prev_{session_id}_{page-1}"))
        nav.append(InlineKeyboardButton("Next ⏩", callback_data=f"page_next_{session_id}_{page+1}"))

        if nav:
            buttons.append(nav)

        await callback_query.message.edit_text(
            "<b>📺 Episodes List</b>\n\nSelect an episode below:",
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode=ParseMode.HTML
        )

    except Exception as e:
        logger.error(f"pagination_callback error: {e}")
        await callback_query.answer("⚠️ Something went wrong.", show_alert=True)
