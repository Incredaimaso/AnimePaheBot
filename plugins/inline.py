from urllib import request
from pyrogram import Client, filters
from pyrogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardMarkup, InlineKeyboardButton
import uuid
from plugins.headers import session  # ensure this is correct
from plugins.commands import user_queries
import requests
import logging
logger = logging.getLogger(__name__)

@Client.on_inline_query()
async def inline_search(client, inline_query):
    query = inline_query.query.strip()

    if not query:
        return

    logger.info(f"Inline query received: {query}")

    try:
        from plugins.commands import user_queries
        user_queries[inline_query.from_user.id] = query

        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (compatible; Bot/1.0)"
        })

        url = f"https://animepahe.ru/api?m=search&q={query.replace(' ', '+')}"
        logger.debug(f"Fetching: {url}")
        res = session.get(url)
        data = res.json().get("data", [])

        if not data:
            logger.warning(f"No results found for query: {query}")
            return

        # Your InlineQueryResultArticle logic...
    except Exception as e:
        logger.exception(f"Error in inline_search: {e}")
