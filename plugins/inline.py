from pyrogram import Client, filters
from pyrogram.types import (
    InlineQuery, 
    InlineQueryResultArticle, 
    InputTextMessageContent, 
    InlineKeyboardMarkup, 
    InlineKeyboardButton
)
from plugins.headers import session
from uuid import uuid4
import logging

user_queries = {}

@Client.on_inline_query()
async def inline_search(client, inline_query: InlineQuery):
    query = inline_query.query.strip()

    if not query:
        await inline_query.answer([], cache_time=0)
        return

    user_queries[inline_query.from_user.id] = query

    try:
        url = f"https://animepahe.ru/api?m=search&q={query.replace(' ', '+')}"
        res = session.get(url).json()

        results = []
        for anime in res.get("data", []):
            session_id = anime["session"]
            title = anime["title"]
            poster = anime["poster"]
            year = anime["year"]
            type_ = anime["type"]

            message_text = (
                f"📺 {title}\n\n"
                f"Click the button below to view episodes."
            )

            results.append(
                InlineQueryResultArticle(
                    id=str(uuid4()),
                    title=title,
                    description=f"{type_} - {year}",
                    thumb_url=poster,
                    input_message_content=InputTextMessageContent(
                        message_text  # NO parse_mode here
                    ),
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("📂 Show Episodes", callback_data=f"anime_inline_{session_id}")]
                    ])
                )
            )

        await inline_query.answer(results, cache_time=0)

    except Exception as e:
        logging.error(f"Error in inline_search: {e}")
        await inline_query.answer([], cache_time=0)

@Client.on_callback_query(filters.regex(r"^anime_inline_"))
async def inline_show_episodes(client, callback_query):
    session_id = callback_query.data.split("anime_inline_")[1]
    user_id = callback_query.from_user.id

    try:
        ep_url = f"https://animepahe.ru/api?m=release&id={session_id}&sort=episode_asc&page=1"
        res = session.get(ep_url).json()
        episodes = res.get("data", [])
        
        buttons = []
        for ep in episodes:
            ep_num = ep["episode"]
            ep_session = ep["session"]
            buttons.append([
                InlineKeyboardButton(f"Episode {ep_num}", callback_data=f"inline_ep_{session_id}_{ep_session}_{ep_num}")
            ])

        await callback_query.message.edit_text(
            f"📺 <b>Select an episode below:</b>",
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode="html"
        )
    except Exception as e:
        await callback_query.message.edit_text("❌ Failed to fetch episodes.")
        logging.error(f"Inline episode fetch error: {e}")
