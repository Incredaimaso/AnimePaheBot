import logging
import requests
from pyrogram import Client
from pyrogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent
from uuid import uuid4
from plugins.headers import session

logger = logging.getLogger(__name__)

@Client.on_inline_query()
async def inline_search(client, inline_query: InlineQuery):
    query = inline_query.query.strip()
    logger.info(f"Inline query received: {query}")

    if not query:
        return

    try:
        url = f"https://animepahe.ru/api?m=search&q={query.replace(' ', '+')}"
        res = session.get(url, timeout=15)

        if res.status_code != 200:
            logger.error(f"AnimePahe returned status code {res.status_code}")
            return

        if not res.content or res.text.strip() == "":
            logger.error("Empty response received from AnimePahe")
            return

        data = res.json()

        results = []
        for item in data.get("data", [])[:10]:
            title = item["title"]
            session_id = item["session"]

            results.append(
                InlineQueryResultArticle(
                    title=title,
                    description="Tap to get details",
                    input_message_content=InputTextMessageContent(
                        message_text=f"/anime {title}"  # or f"anime_{session_id}"
                    ),
                    id=str(uuid4())
                )
            )

        if results:
            await inline_query.answer(results, cache_time=0, is_personal=True)
        else:
            logger.warning("No anime found for query.")

    except Exception as e:
        logger.error(f"Error in inline_search: {e}")
