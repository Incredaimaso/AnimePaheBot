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
