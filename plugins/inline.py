from pyrogram import Client, filters
from pyrogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent
import uuid
from plugins.headers import session  # or however you defined session

@Client.on_inline_query()
async def inline_search(client, inline_query: InlineQuery):
    query = inline_query.query.strip()

    if not query:
        await inline_query.answer([], cache_time=1)
        return

    try:
        search_url = f"https://animepahe.ru/api?m=search&q={query.replace(' ', '+')}"
        response = session.get(search_url).json()

        results = []
        for anime in response.get("data", [])[:20]:
            title = anime["title"]
            session_id = anime["session"]
            caption = (
                f"**Title**: {title}\n"
                f"**Episodes**: {anime['episodes']}\n"
                f"**Season**: {anime['season']} | {anime['year']}\n"
                f"**Score**: {anime['score']}\n\n"
                f"Click below to view episodes."
            )

            # Create result card
            results.append(
                InlineQueryResultArticle(
                    title=title,
                    description=f"{anime['type']} | {anime['status']} | {anime['episodes']} eps",
                    input_message_content=InputTextMessageContent(
                        caption,
                        parse_mode="markdown"
                    ),
                    reply_markup=InlineKeyboardMarkup(
                        [[
                            InlineKeyboardButton("▶ Show Episodes", callback_data=f"anime_{session_id}")
                        ]]
                    ),
                    id=str(uuid.uuid4())
                )
            )

        await inline_query.answer(results, cache_time=5)

    except Exception as e:
        await inline_query.answer([], cache_time=1)
        print(f"[INLINE ERROR]: {e}")
