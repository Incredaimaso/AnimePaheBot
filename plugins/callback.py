#..........This Bot Made By [RAHAT](https://t.me/r4h4t_69)..........#
#..........Anyone Can Modify This As He Likes..........#
#..........Just one requests do not remove my credit..........#

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from plugins.queue import add_to_queue, remove_from_queue
from plugins.kwik import extract_kwik_link
from plugins.direct_link import get_dl_link
from plugins.headers import*
from plugins.file import*
from plugins.commands import user_queries
from helper.database import*
from helper.utils import*
from config import DOWNLOAD_DIR
from bs4 import BeautifulSoup
import re
import asyncio
import time

episode_data = {}
episode_urls = {}

@Client.on_callback_query(filters.regex(r"^anime_"))
def anime_details(client, callback_query):
    session_id = callback_query.data.split("anime_")[1]

    # Retrieve the query stored earlier
    query = user_queries.get(callback_query.from_user.id, "")
    search_url = f"https://animepahe.ru/api?m=search&q={query.replace(' ', '+')}"
    try:
        response = session.get(search_url).json()
    except Exception:
        callback_query.message.reply_text("Failed to fetch anime details. Try again later.")
        return

    
    anime = next(anime for anime in response['data'] if anime['session'] == session_id)
    title = anime['title']
    anime_type = anime['type']
    episodes = anime['episodes']
    status = anime['status']
    season = anime['season']
    year = anime['year']
    score = anime['score']
    poster_url = anime['poster']
    anime_link = f"https://animepahe.ru/anime/{session_id}"

    message_text = (
        f"**Title**: {title}\n"
        f"**Type**: {anime_type}\n"
        f"**Episodes**: {episodes}\n"
        f"**Status**: {status}\n"
        f"**Season**: {season}\n"
        f"**Year**: {year}\n"
        f"**Score**: {score}\n"
        f"[Anime Link]({anime_link})\n\n"
        f"**Bot Made By**\n"
        f"    **[✪ 𝙋𝙞𝙧𝙖𝙨](https://telegram.dog/piras_official)**"
    )

    # Store the session_id for episodes
    episode_data[callback_query.from_user.id] = {
        "session_id": session_id,
        "poster": poster_url,
        "title": title
    }

    episode_button = InlineKeyboardMarkup([
        [InlineKeyboardButton("Episodes", callback_data="episodes")]
    ])

    if callback_query.message:
        callback_query.message.reply_photo(
            photo=poster_url,
            caption=message_text,
            reply_markup=episode_button
        )
    else:
        client.send_photo(
            chat_id=callback_query.from_user.id,
            photo=poster_url,
            caption=message_text,
            reply_markup=episode_button
        )


# Callback for episode list with pagination (send buttons once)
@Client.on_callback_query(filters.regex(r"^episodes$"))
def episode_list(client, callback_query, page=1):
    session_data = episode_data.get(callback_query.from_user.id)

    if not session_data:
        callback_query.message.reply_text("Session ID not found.")
        return

    session_id = session_data['session_id']
    episodes_url = f"https://animepahe.ru/api?m=release&id={session_id}&sort=episode_asc&page={page}"
    response = session.get(episodes_url).json()

    # Store the total number of pages
    last_page = int(response["last_page"])
    episodes = response['data']

    # Update the current page for the user
    episode_data[callback_query.from_user.id]['current_page'] = page
    episode_data[callback_query.from_user.id]['last_page'] = last_page

    # Store episode data for each user
    episode_data[callback_query.from_user.id]['episodes'] = {ep['episode']: ep['session'] for ep in episodes}

    episode_buttons = [
        [InlineKeyboardButton(f"Episode {ep['episode']}", callback_data=f"ep_{ep['episode']}")]
        for ep in episodes
    ]


    # Add navigation buttons for pagination
    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton("<", callback_data=f"page_{page - 1}"))
    if page < last_page:
        nav_buttons.append(InlineKeyboardButton(">", callback_data=f"page_{page + 1}"))

    if nav_buttons:
        episode_buttons.append(nav_buttons)

    reply_markup = InlineKeyboardMarkup(episode_buttons)

    # If it's the first time, send a message, otherwise edit the existing one
    if callback_query.message.reply_markup is None:
        callback_query.message.reply_text(f"Page {page}/{last_page}: Select an episode:", reply_markup=reply_markup)
    else:
        callback_query.message.edit_reply_markup(reply_markup)

# Callback to handle navigation between pages (edit buttons in place)
@Client.on_callback_query(filters.regex(r"^page_"))
def navigate_pages(client, callback_query):
    new_page = int(callback_query.data.split("_")[1])
    session_data = episode_data.get(callback_query.from_user.id)

    if not session_data:
        callback_query.message.reply_text("Session ID not found.")
        return

    current_page = session_data.get('current_page', 1)
    last_page = session_data.get('last_page', 1)

    # Check if the user is trying to go beyond the first or last page
    if new_page < 1:
        callback_query.answer("You're already on the first page.", show_alert=True)
    elif new_page > last_page:
        callback_query.answer("You're already on the last page.", show_alert=True)
    else:
        # Call the episode list function with the new page number, but edit the message
        episode_list(client, callback_query, page=new_page)


# Callback for episode link and fetching download links
@Client.on_callback_query(filters.regex(r"^ep_"))
def fetch_download_links(client, callback_query):
    episode_number = int(callback_query.data.split("_")[1])
    user_id = callback_query.from_user.id  # Unique per user
    
    session_data = episode_data.get(user_id)

    if not session_data or 'episodes' not in session_data:
        callback_query.message.reply_text("Episode not found.")
        return

    session_id = session_data['session_id']
    episodes = session_data['episodes']

    if episode_number not in episodes:
        callback_query.message.reply_text("Episode not found.")
        return

    # Store episode number for the user
    episode_data[user_id]['current_episode'] = episode_number  # Add this line

    episode_session = episodes[episode_number]
    episode_url = f"https://animepahe.ru/play/{session_id}/{episode_session}"

    # Send a request to the episode URL and parse the HTML for download links
    response = session.get(episode_url)
    soup = BeautifulSoup(response.content, "html.parser")

    # Extract all download links and their titles
    download_links = soup.select("#pickDownload a.dropdown-item")

    if not download_links:
        callback_query.message.reply_text("No download links found.")
        return

    # Create buttons for each download link
    download_buttons = [
        [InlineKeyboardButton(link.get_text(strip=True), callback_data=f"dl_{link['href']}")]
        for link in download_links
    ]
    reply_markup = InlineKeyboardMarkup(download_buttons)
    callback_query.message.reply_text("Select a download link:", reply_markup=reply_markup)

@Client.on_callback_query(filters.regex(r"set_method_"))
def change_upload_method(client, callback_query):
    user_id = callback_query.from_user.id
    data = callback_query.data.split("_")[2]  # Extract 'document' or 'video'
    
    # Update the selected method in the database
    save_upload_method(user_id, data)
    
    # Acknowledge the change
    callback_query.answer(f"Upload method set to {data.capitalize()}")
    
    # Update the buttons with the new selection
    document_status = "✅" if data == "document" else "❌"
    video_status = "✅" if data == "video" else "❌"
    
    buttons = [
        [
            InlineKeyboardButton(f"Document ({document_status})", callback_data="set_method_document"),
            InlineKeyboardButton(f"Video ({video_status})", callback_data="set_method_video")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(buttons)
    callback_query.message.edit_reply_markup(reply_markup)


@Client.on_callback_query(filters.regex(r"^dl_"))
async def download_and_upload_file(client, callback_query):
    download_url = callback_query.data.split("dl_")[1]
    kwik_link = extract_kwik_link(download_url)

    try:
        direct_link = get_dl_link(kwik_link)
    except Exception as e:
        callback_query.message.reply_text(f"Error generating download link: {str(e)}")
        return

    username = callback_query.from_user.username or "Unknown User"
    user_id = callback_query.from_user.id
    add_to_queue(user_id, username, direct_link)

    # Retrieve episode number and title
    episode_number = episode_data.get(user_id, {}).get('current_episode', 'Unknown')
    title = episode_data.get(user_id, {}).get('title', 'Unknown Title')

    # Get quality & type from button
    download_button_title = next(
        (button.text for row in callback_query.message.reply_markup.inline_keyboard
         for button in row if button.callback_data == f"dl_{download_url}"),
        "Unknown Source"
    )

    resolution = re.search(r"\b\d{3,4}p\b", download_button_title)
    resolution = resolution.group() if resolution else download_button_title
    type = "Dub" if 'eng' in download_button_title.lower() else "Sub"

    # === Filename generation ===
    short_name = create_short_name(title)
    format_template = get_filename_format(user_id)

    try:
        file_name = format_template.format(
            episode_number=episode_number,
            title=short_name,
            resolution=resolution,
            type=type
        )
    except KeyError as e:
        callback_query.message.reply_text(f"❌ Invalid placeholder in format: {str(e)}")
        return

    file_name = sanitize_filename(file_name + ".mp4")
    random_str = random_string(5)

    # File paths
    user_download_dir = os.path.join(DOWNLOAD_DIR, str(user_id), random_str)
    os.makedirs(user_download_dir, exist_ok=True)
    download_path = os.path.join(user_download_dir, file_name)

    dl_msg = await callback_query.message.reply_text(
        f"<b>Added to queue:</b>\n<pre>{file_name}</pre>\n<b>Downloading now...</b>"
    )

    try:
        loop = asyncio.get_running_loop()
        last_progress = {"text": "", "time": 0}

        def report_progress(current, total, speed, eta):
            progress_text = format_upload_progress(
                filename=file_name,
                uploaded=current,
                total=total,
                speed=speed,
                eta=eta,
                mode="Downloading"
            )

            if progress_text != last_progress["text"]:
                last_progress["text"] = progress_text
                coro = dl_msg.edit_text(progress_text)
                asyncio.run_coroutine_threadsafe(coro, loop)


        await asyncio.to_thread(download_file, direct_link, download_path, report_progress)

        await dl_msg.edit_text("<b>Episode downloaded, uploading...</b>")

        # Thumbnail logic
        user_thumbnail = get_thumbnail(user_id)
        poster_url = episode_data.get(user_id, {}).get("poster", None)

        if user_thumbnail:
            thumb_path = await client.download_media(user_thumbnail)
        elif poster_url:
            response = requests.get(poster_url, stream=True, timeout=25)
            thumb_path = os.path.join(user_download_dir, "thumb_file.jpg")
            with open(thumb_path, 'wb') as thumb_file:
                for chunk in response.iter_content(1024):
                    thumb_file.write(chunk)
        else:
            thumb_path = None

        if thumb_path and os.path.exists(thumb_path):
            thumb_to_send = thumb_path
        else:
             thumb_to_send = None

        # Final caption
        user_caption = get_caption(user_id)
        caption_to_use = user_caption if user_caption else file_name

        # Upload with progress
        chat_id = callback_query.message.chat.id
        start_time = time.time()

        async def progress(current, total):
            now = time.time()
            if now - progress.last_update >= 5 or current == total:
                speed = current / (now - start_time + 1e-3)
                eta = (total - current) / speed if speed > 0 else 0

                progress_text = format_upload_progress(
                    filename=file_name,
                    uploaded=current,
                    total=total,
                    speed=speed,
                    eta=eta,
                    mode=get_upload_method(user_id).capitalize()
                )

                if progress.last_text != progress_text:
                    try:
                        await dl_msg.edit_text(progress_text)
                        progress.last_text = progress_text
                    except:
                        pass

                progress.last_update = now

        progress.last_update = 0
        progress.last_text = ""


        upload_method = get_upload_method(user_id)

        if upload_method == "document":
            await client.send_document(
                chat_id=chat_id,
                document=download_path,
                thumb=thumb_to_send,
                caption=caption_to_use,
                progress=progress
            )
        else:
            await client.send_video(
                chat_id=chat_id,
                video=download_path,
                thumb=thumb_to_send,
                caption=caption_to_use,
                progress=progress
            )

        # Mark complete and clean up
        await dl_msg.edit_text("<b><pre>Episode Uploaded 🎉</pre></b>")
        remove_from_queue(user_id, direct_link)

        if thumb_path and os.path.exists(thumb_path):
            os.remove(thumb_path)
        if os.path.exists(user_download_dir):
            remove_directory(user_download_dir)
    except Exception as e:
       await callback_query.message.reply_text(f"❌ Error during download/upload:\n<code>{str(e)}</code>")


# Callback query handler for Help and Close buttons
@Client.on_callback_query()
def callback_query_handler(client, callback_query):
    if callback_query.data == "help":
        # Send the help message
        callback_query.message.edit_text(
            text="Here is how to use the bot:\n\n1. /anime <anime_name> - Search for an anime.\n2. /set_thumb - Set a custom thumbnail.\n3. /options - Set upload options (Document or Video).\n4. /queue - View active downloads.\n5. /set_caption - Set custom caption.\n6. /see_caption - See current custom caption.\n7. /del_caption - Delect current custom caption",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Close", callback_data="close")]])
        )
    
    elif callback_query.data == "close":
        # Close the panel by deleting the message
        callback_query.message.delete()
