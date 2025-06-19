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
from bs4 import BeautifulSoup
import re
from plugins.kwik import extract_kwik_link
from plugins.direct_link import get_dl_link
from plugins.file import create_short_name, sanitize_filename
from config import DOWNLOAD_DIR
import os
import time
import asyncio
import requests
from plugins.file import get_caption, get_upload_method, get_thumbnail, random_string, remove_directory
from plugins.file import download_file
from pyrogram.enums import ParseMode
from helper.utils import format_upload_progress

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

@Client.on_callback_query(filters.regex(r"^inline_ep_"))
async def inline_show_quality(client, callback_query):
    try:
        data = callback_query.data.split("_", 3)
        session_id = data[2]
        ep_session = data[3]
        episode_number = data[4] if len(data) > 4 else "?"

        # Build URL and fetch download options
        play_url = f"https://animepahe.ru/play/{session_id}/{ep_session}"
        soup = BeautifulSoup(session.get(play_url).content, "html.parser")
        links = soup.select("#pickDownload a.dropdown-item")

        if not links:
            await callback_query.message.edit_text("❌ No download links found.")
            return

        # Make download buttons (quality + sub/dub)
        buttons = []
        for link in links:
            text = link.get_text(strip=True)
            href = link['href']
            label = re.sub(r"\s+", " ", text)  # clean whitespace
            buttons.append([
                InlineKeyboardButton(label, callback_data=f"inline_dl_{session_id}_{ep_session}_{episode_number}_{href}")
            ])

        await callback_query.message.edit_text(
            f"🎬 <b>Select a quality for Episode {episode_number}:</b>",
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode="html"
        )
    except Exception as e:
        await callback_query.message.edit_text("❌ Failed to load quality options.")
        logging.error(f"inline_show_quality error: {e}")

@Client.on_callback_query(filters.regex(r"^inline_dl_"))
async def inline_download_and_upload(client, callback_query):
    try:
        _, session_id, ep_session, ep_number, href = callback_query.data.split("_", 4)

        msg = await callback_query.message.edit_text("🔗 Generating direct download link...")
        user_id = callback_query.from_user.id

        # Extract direct link
        kwik = extract_kwik_link(href)
        direct_link = get_dl_link(kwik)

        # Filename setup
        title = episode_data.get(user_id, {}).get("title", "Anime")
        short = create_short_name(title)
        resolution = re.search(r"\d{3,4}p", href)
        resolution = resolution.group() if resolution else "Unknown"
        type_ = "Dub" if "eng" in href.lower() else "Sub"

        file_name = sanitize_filename(f"EP{ep_number} - {short} [{resolution}] [{type_}].mp4")
        rand = random_string(5)
        download_dir = os.path.join(DOWNLOAD_DIR, str(user_id), rand)
        os.makedirs(download_dir, exist_ok=True)
        path = os.path.join(download_dir, file_name)

        # Progress setup
        start = time.time()
        last_text = ""
        last_update = 0

        def progress_callback(current, total, speed, eta):
            nonlocal last_text, last_update
            now = time.time()
            if now - last_update >= 5 or current == total:
                text = format_upload_progress(
                    filename=file_name,
                    uploaded=current,
                    total=total,
                    speed=speed,
                    eta=eta,
                    mode="Downloading"
                )
                if text != last_text:
                    asyncio.run_coroutine_threadsafe(
                        callback_query.message.edit_text(text, parse_mode=ParseMode.HTML), asyncio.get_event_loop()
                    )
                    last_text = text
                    last_update = now

        # Start download in thread
        await asyncio.to_thread(download_file, direct_link, path, progress_callback)

        await callback_query.message.edit_text("✅ Download complete. Uploading...")

        # Upload logic
        thumb = None
        thumb_id = get_thumbnail(user_id)
        if thumb_id:
            thumb = await client.download_media(thumb_id)

        caption = get_caption(user_id) or file_name
        upload_method = get_upload_method(user_id)
        chat_id = callback_query.message.chat.id

        start_time = time.time()

        async def upload_progress(current, total):
            now = time.time()
            if now - upload_progress.last_update >= 5 or current == total:
                speed = current / (now - start_time + 1e-3)
                eta = (total - current) / speed if speed else 0
                text = format_upload_progress(
                    filename=file_name,
                    uploaded=current,
                    total=total,
                    speed=speed,
                    eta=eta,
                    mode=upload_method.capitalize()
                )
                if text != upload_progress.last_text:
                    try:
                        await callback_query.message.edit_text(text, parse_mode=ParseMode.HTML)
                        upload_progress.last_text = text
                    except:
                        pass
                upload_progress.last_update = now

        upload_progress.last_update = 0
        upload_progress.last_text = ""

        if upload_method == "document":
            await client.send_document(chat_id, document=path, caption=caption, thumb=thumb, progress=upload_progress)
        else:
            await client.send_video(chat_id, video=path, caption=caption, thumb=thumb, progress=upload_progress)

        await callback_query.message.edit_text("✅ <b>Upload Complete!</b>", parse_mode=ParseMode.HTML)

        if thumb and os.path.exists(thumb):
            os.remove(thumb)
        remove_directory(download_dir)

    except Exception as e:
        logging.error(f"inline_download_and_upload error: {e}")
        await callback_query.message.edit_text(f"❌ Error:\n<code>{str(e)}</code>", parse_mode="html")
