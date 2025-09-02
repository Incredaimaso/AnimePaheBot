# ---------- Callback Handlers ----------
# This Bot Made By [RAHAT](https://t.me/r4h4t_69)
# Anyone Can Modify As They Like
# Just don't remove the credit ❤️

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from plugins.queue import add_to_queue, remove_from_queue
from plugins.kwik import extract_kwik_link
from plugins.direct_link import get_dl_link
from plugins.headers import session
from plugins.file import (
    create_short_name, sanitize_filename, download_file,
    get_caption, get_thumbnail, get_upload_method, random_string
)
from helper.database import save_upload_method, get_filename_format
from helper.utils import format_upload_progress
from config import DOWNLOAD_DIR
from bs4 import BeautifulSoup
import re
import asyncio
import time
import logging
import os
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# --- Anime details (list episodes) ---
@Client.on_callback_query(filters.regex(r"^anime_"))
async def anime_details(client, callback_query):
    session_id = callback_query.data.split("anime_")[1]

    ep_url = f"https://animepahe.ru/api?m=release&id={session_id}&sort=episode_asc&page=1"
    try:
        res = session.get(ep_url).json()
    except Exception as e:
        await callback_query.message.edit_text("❌ Failed to fetch episodes.")
        logger.error(f"anime_details error: {e}")
        return

    episodes = res.get("data", [])
    if not episodes:
        await callback_query.message.edit_text("❌ No episodes found.")
        return

    buttons = [
        [InlineKeyboardButton(
            f"Episode {ep['episode']}",
            callback_data=f"ep_{session_id}_{ep['session']}_{ep['episode']}"
        )]
        for ep in episodes
    ]

    await callback_query.message.edit_text(
        "📺 <b>Select an episode:</b>",
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode="html"
    )


# --- Episode handler (show qualities) ---
@Client.on_callback_query(filters.regex(r"^ep_"))
async def fetch_download_links(client, callback_query):
    _, session_id, ep_session, ep_number = callback_query.data.split("_", 3)

    url = f"https://animepahe.ru/play/{session_id}/{ep_session}"
    try:
        soup = BeautifulSoup(session.get(url).content, "html.parser")
    except Exception as e:
        await callback_query.message.edit_text("❌ Failed to fetch download links.")
        logger.error(f"fetch_download_links error: {e}")
        return

    links = soup.select("#pickDownload a.dropdown-item")
    if not links:
        await callback_query.message.edit_text("❌ No download links found.")
        return

    buttons = [
        [InlineKeyboardButton(
            link.get_text(strip=True),
            callback_data=f"dl_{session_id}_{ep_session}_{ep_number}_{link['href']}"
        )]
        for link in links
    ]

    await callback_query.message.edit_text(
        f"🎬 <b>Select quality for Episode {ep_number}:</b>",
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode="html"
    )


# --- Download + upload handler ---
@Client.on_callback_query(filters.regex(r"^dl_"))
async def download_and_upload(client, callback_query):
    try:
        _, session_id, ep_session, ep_number, href = callback_query.data.split("_", 4)
    except ValueError:
        await callback_query.message.edit_text("❌ Invalid callback data.")
        return

    msg = await callback_query.message.edit_text("🔗 Generating direct download link...")
    user_id = callback_query.from_user.id

    try:
        kwik = extract_kwik_link(href)
        direct_link = get_dl_link(kwik)
    except Exception as e:
        await msg.edit_text(f"❌ Failed to generate direct link.\n<code>{str(e)}</code>", parse_mode="html")
        return

    # --- File naming ---
    resolution = re.search(r"\d{3,4}p", href)
    resolution = resolution.group() if resolution else "Unknown"
    type_ = "Dub" if "eng" in href.lower() else "Sub"

    short = create_short_name("Anime")  # fallback name
    format_template = get_filename_format(user_id) or "{title}_EP{episode_number}_{resolution}_{type}"
    try:
        file_name = format_template.format(
            episode_number=ep_number,
            title=short,
            resolution=resolution,
            type=type_
        )
    except KeyError:
        file_name = f"EP{ep_number}_{short}_{resolution}_{type_}"
    file_name = sanitize_filename(file_name + ".mp4")

    rand = random_string(5)
    download_dir = os.path.join(DOWNLOAD_DIR, str(user_id), rand)
    os.makedirs(download_dir, exist_ok=True)
    path = os.path.join(download_dir, file_name)

    # --- Download with progress ---
    start = time.time()
    async def progress_callback(current, total):
        now = time.time()
        if now - progress_callback.last_update >= 5 or current == total:
            speed = current / (now - start + 1e-3)
            eta = (total - current) / speed if speed else 0
            text = format_upload_progress(
                filename=file_name,
                uploaded=current,
                total=total,
                speed=speed,
                eta=eta,
                mode="Downloading"
            )
            try:
                await msg.edit_text(text, parse_mode="html")
            except:
                pass
            progress_callback.last_update = now
    progress_callback.last_update = 0

    try:
        await asyncio.to_thread(download_file, direct_link, path, lambda c, t, *_: asyncio.run(progress_callback(c, t)))
    except Exception as e:
        await msg.edit_text(f"❌ Download failed:\n<code>{str(e)}</code>", parse_mode="html")
        return

    await msg.edit_text("✅ Download complete. Uploading...")

    # --- Thumbnail ---
    thumb = None
    thumb_id = get_thumbnail(user_id)
    if thumb_id:
        thumb = await client.download_media(thumb_id)

    # --- Upload ---
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
            try:
                await msg.edit_text(text, parse_mode="html")
            except:
                pass
            upload_progress.last_update = now
    upload_progress.last_update = 0

    try:
        if upload_method == "document":
            await client.send_document(chat_id, document=path, caption=caption, thumb=thumb, progress=upload_progress)
        else:
            await client.send_video(chat_id, video=path, caption=caption, thumb=thumb, progress=upload_progress)
    except Exception as e:
        await msg.edit_text(f"❌ Upload failed:\n<code>{str(e)}</code>", parse_mode="html")
        return

    await msg.edit_text("✅ <b>Upload complete!</b>", parse_mode="html")

    if thumb and os.path.exists(thumb):
        os.remove(thumb)
    if os.path.exists(download_dir):
        os.rmdir(download_dir)
