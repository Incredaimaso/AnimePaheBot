# ---------- Callback Handler ----------
# This Bot Made By [RAHAT](https://t.me/r4h4t_69)
# Anyone Can Modify As They Like
# Just don't remove the credit ❤️

import logging
from uuid import uuid4
from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ParseMode
from plugins.headers import session

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# In-memory callback storage
CALLBACK_CACHE = {}  # {short_key: (prefix, real_value)}

def store_callback_data(prefix: str, real_value: str) -> str:
    """Store real data and return a safe short callback key."""
    key = str(uuid4())[:8]
    CALLBACK_CACHE[key] = (prefix, real_value)
    return f"{prefix}_{key}"

def resolve_callback_data(data: str):
    """Resolve short callback key back to real data."""
    try:
        prefix, key = data.split("_", 1)
        return CALLBACK_CACHE.get(key, (prefix, None))
    except Exception:
        return None, None


# --- Handle anime selection (from inline query) ---
@Client.on_callback_query(filters.regex(r"^anime_"))
async def anime_callback(client: Client, callback_query: CallbackQuery):
    try:
        _, anime_id = resolve_callback_data(callback_query.data)

        if not anime_id:
            await callback_query.answer("⚠️ Session expired. Try again.", show_alert=True)
            return

        url = f"https://animepahe.ru/api?m=release&id={anime_id}&sort=episode_asc&page=1"
        res = session.get(url).json()

        episodes = res.get("data", [])
        if not episodes:
            await callback_query.answer("❌ No episodes found.", show_alert=True)
            return

        buttons = []
        for ep in episodes[:10]:
            ep_num = ep.get("episode")
            safe_cb = store_callback_data("episode", f"{anime_id}_{ep_num}")
            buttons.append([InlineKeyboardButton(f"Episode {ep_num}", callback_data=safe_cb)])

        nav_buttons = [
            InlineKeyboardButton("⏪ Prev", callback_data=store_callback_data("page", f"{anime_id}_1")),
            InlineKeyboardButton("Next ⏩", callback_data=store_callback_data("page", f"{anime_id}_2"))
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
        _, payload = resolve_callback_data(callback_query.data)

        if not payload:
            await callback_query.answer("⚠️ Session expired. Try again.", show_alert=True)
            return

        anime_id, ep_num = payload.split("_")

        # Fetch release list again to resolve fresh session ID
        url = f"https://animepahe.ru/api?m=release&id={anime_id}&sort=episode_asc&page=1"
        res = session.get(url).json()
        episodes = res.get("data", [])

        ep = next((x for x in episodes if str(x.get("episode")) == ep_num), None)
        if not ep:
            await callback_query.answer("❌ Episode not found.", show_alert=True)
            return

        ep_session = ep.get("session")
        url = f"https://animepahe.ru/api?m=embed&id={ep_session}"
        embed_res = session.get(url).json()

        embed_url = embed_res.get("data", {}).get("url")
        if not embed_url:
            await callback_query.answer("❌ Stream link not found.", show_alert=True)
            return

        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("▶️ Watch Now", url=embed_url)]
        ])

        await callback_query.message.edit_text(
            f"<b>Episode {ep_num} Stream</b>\n\n<a href='{embed_url}'>Click here to watch</a>",
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
        _, payload = resolve_callback_data(callback_query.data)

        if not payload:
            await callback_query.answer("⚠️ Session expired. Try again.", show_alert=True)
            return

        anime_id, page = payload.split("_")
        page = int(page)

        url = f"https://animepahe.ru/api?m=release&id={anime_id}&sort=episode_asc&page={page}"
        res = session.get(url).json()

        episodes = res.get("data", [])
        if not episodes:
            await callback_query.answer("❌ No more episodes.", show_alert=True)
            return

        buttons = []
        for ep in episodes[:10]:
            ep_num = ep.get("episode")
            safe_cb = store_callback_data("episode", f"{anime_id}_{ep_num}")
            buttons.append([InlineKeyboardButton(f"Episode {ep_num}", callback_data=safe_cb)])

        nav = []
        if page > 1:
            nav.append(InlineKeyboardButton("⏪ Prev", callback_data=store_callback_data("page", f"{anime_id}_{page-1}")))
        nav.append(InlineKeyboardButton("Next ⏩", callback_data=store_callback_data("page", f"{anime_id}_{page+1}")))

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
