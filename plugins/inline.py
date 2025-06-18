from pyrogram import Client
from pyrogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent
from plugins.headers import session
from plugins.commands import user_queries
from uuid import uuid4
import logging

logger = logging.getLogger(__name__)

@Client.on_inline_query()
async def inline_search(client, inline_query: InlineQuery):
    query = inline_query.query.strip()
    logger.info(f"Inline query received: {query}")

    if not query:
        return

    try:
        url = f"https://animepahe.ru/api?m=search&q={query.replace(' ', '+')}"
        response = session.get(url, timeout=10)

        if response.status_code != 200 or not response.content.strip():
            logger.error(f"AnimePahe API error: {response.status_code} or empty body")
            return

        data = response.json()

        user_queries[inline_query.from_user.id] = query  # Store for callback use

        results = []
        for anime in data.get("data", [])[:10]:
            title = anime["title"]
            session_id = anime["session"]

            results.append(
                InlineQueryResultArticle(
                    title=title,
                    description="Tap to get details",
                    input_message_content=InputTextMessageContent(
                        message_text=f"anime_{session_id}"
                    ),
                    id=str(uuid4())
                )
            )

        await inline_query.answer(results, cache_time=0, is_personal=True)

    except Exception as e:
        logger.error(f"Error in inline_search: {e}")
