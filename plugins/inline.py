# plugins/inline.py
from pyrogram import Client, filters
from pyrogram.types import InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardMarkup, InlineKeyboardButton
from plugins.headers import session
from uuid import uuid4
import logging

# Store queries by user_id
user_queries = {}

@Client.on_inline_query()
async def inline_search(client, inline_query):
    query = inline_query.query.strip()
    logging.info(f"Inline query received: {query}")
    
    if not query:
        return await inline_query.answer([], cache_time=1)

    user_id = inline_query.from_user.id
    user_queries[user_id] = query  # store search term

    try:
        url = f"https://animepahe.ru/api?m=search&q={query.replace(' ', '+')}"
        res = session.get(url).json()
        results = []

        for anime in res.get("data", []):
            session_id = anime["session"]
            title = anime["title"]
            episodes = anime.get("episodes", "N/A")
            type_ = anime.get("type", "Unknown")

            # Each result has a message + inline button
            results.append(
                InlineQueryResultArticle(
                    title=title,
                    description=f"{type_} • Episodes: {episodes}",
                    input_message_content=InputTextMessageContent(
                        f"📺 {title}\n\nClick the button below to view episodes."
                    ),
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("Show Episodes", callback_data=f"anime_{session_id}")
                    ]]),
                    id=str(uuid4())
                )
            )

        await inline_query.answer(results, cache_time=3)

    except Exception as e:
        logging.error(f"Error in inline_search: {e}")
        await inline_query.answer([], switch_pm_text="❌ Failed to fetch results", cache_time=3)
