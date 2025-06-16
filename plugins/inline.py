from pyrogram import Client, filters
from pyrogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardMarkup, InlineKeyboardButton
import uuid
from plugins.headers import session  # ensure this is correct

@Client.on_inline_query()
async def inline_search(client: Client, inline_query: InlineQuery):
    query = inline_query.query.strip()
    if not query:
        await inline_query.answer([], cache_time=1)
        return

    try:
        url = f"https://animepahe.ru/api?m=search&q={query.replace(' ', '+')}"
        response = session.get(url).json()
        results = []

        for anime in response.get("data", [])[:10]:
            title = anime["title"]
            sid = anime["session"]
            desc = f"{anime['type']} | {anime['status']} | {anime['episodes']} eps"
            text = f"**{title}**\n{desc}"

            results.append(
                InlineQueryResultArticle(
                    id=str(uuid.uuid4()),
                    title=title,
                    description=desc,
                    input_message_content=InputTextMessageContent(text),
                    reply_markup=InlineKeyboardMarkup(
                        [[InlineKeyboardButton("▶ Show Episodes", callback_data=f"anime_{sid}")]]
                    )
                )
            )

        await inline_query.answer(results, cache_time=5, switch_pm_text="Tap to search", switch_pm_parameter="from_inline")

    except Exception as e:
        print("Inline error:", e)
        await inline_query.answer([], cache_time=1)
