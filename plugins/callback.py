#..........This Bot Made By [RAHAT](https://t.me/r4h4t_69)..........#
#..........Anyone Can Modify This As He Likes..........#
#..........Just one requests do not remove my credit..........#

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from plugins.queue import add_to_queue, remove_from_queue
from plugins.direct_link import get_dl_link
from plugins.headers import *
from plugins.file import *
from plugins.commands import user_queries
from helper.database import *
from config import DOWNLOAD_DIR
from bs4 import BeautifulSoup
import requests
import os, re, logging

episode_data = {}
logger = logging.getLogger(__name__)

from uuid import uuid4

# In-memory callback storage
CALLBACK_CACHE = {}  # {short_key: (prefix, real_value)}

def store_callback_data(prefix: str, real_value: str) -> str:
    """Store real data and return a safe short callback key."""
    key = str(uuid4())[:8]
    CALLBACK_CACHE[key] = (prefix, real_value)
    return f"{prefix}_{key}"

def resolve_callback_data(data: str):
    """Resolve short callback key back to real data."""
    try:
        prefix, key = data.split("_", 1)
        return CALLBACK_CACHE.get(key, (prefix, None))
    except Exception:
        return None, None

# ================= Anime details ================= #
@Client.on_callback_query(filters.regex(r"^anime_"))
def anime_details(client, callback_query: CallbackQuery):
    try:
        session_id = callback_query.data.split("anime_")[1]
        query = user_queries.get(callback_query.message.chat.id, "")
        search_url = f"https://animepahe.si/api?m=search&q={query.replace(' ', '+')}"
        response = session.get(search_url).json()

        anime = next((a for a in response['data'] if a['session'] == session_id), None)
        if not anime:
            callback_query.message.reply_text("Anime not found, try again.")
            return

        title = anime['title']
        poster_url = anime['poster']
        anime_link = f"https://animepahe.si/anime/{session_id}"

        message_text = (
            f"**Title**: {title}\n"
            f"**Type**: {anime['type']}\n"
            f"**Episodes**: {anime['episodes']}\n"
            f"**Status**: {anime['status']}\n"
            f"**Season**: {anime['season']}\n"
            f"**Year**: {anime['year']}\n"
            f"**Score**: {anime['score']}\n"
            f"[Anime Link]({anime_link})\n\n"
            f"**Bot Made By**\n"
            f"    **[Dot](Piras_Official.t.me)**"
        )

        # Save session data
        episode_data[callback_query.message.chat.id] = {
            "session_id": session_id,
            "poster": poster_url,
            "title": title
        }

        episode_button = InlineKeyboardMarkup(
            [[InlineKeyboardButton("Episodes", callback_data="episodes")]]
        )
        client.send_photo(
            chat_id=callback_query.message.chat.id,
            photo=poster_url,
            caption=message_text,
            reply_markup=episode_button
        )
    except Exception as e:
        logger.error(f"anime_details error: {e}")
        callback_query.message.reply_text("Something went wrong fetching anime details.")


# ================= Episode list with pagination ================= #
@Client.on_callback_query(filters.regex(r"^episodes$"))
def episode_list(client, callback_query: CallbackQuery, page=1):
    session_data = episode_data.get(callback_query.message.chat.id)
    if not session_data:
        callback_query.message.reply_text("Session expired. Please search again.")
        return

    session_id = session_data['session_id']
    episodes_url = f"https://animepahe.si/api?m=release&id={session_id}&sort=episode_asc&page={page}"
    response = session.get(episodes_url).json()

    episodes = response.get('data', [])
    last_page = int(response.get("last_page", 1))

    episode_data[callback_query.message.chat.id].update({
        'current_page': page,
        'last_page': last_page,
        'episodes': {ep['episode']: ep['session'] for ep in episodes}
    })

    episode_buttons = [
        [InlineKeyboardButton(f"Episode {ep['episode']}", callback_data=f"ep_{ep['episode']}")]
        for ep in episodes
    ]

    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton("<", callback_data=f"page_{page - 1}"))
    if page < last_page:
        nav_buttons.append(InlineKeyboardButton(">", callback_data=f"page_{page + 1}"))
    if nav_buttons:
        episode_buttons.append(nav_buttons)

    reply_markup = InlineKeyboardMarkup(episode_buttons)

    if callback_query.message.reply_markup is None:
        callback_query.message.reply_text(f"Page {page}/{last_page}: Select an episode:", reply_markup=reply_markup)
    else:
        callback_query.message.edit_reply_markup(reply_markup)


@Client.on_callback_query(filters.regex(r"^page_"))
def navigate_pages(client, callback_query: CallbackQuery):
    new_page = int(callback_query.data.split("_")[1])
    session_data = episode_data.get(callback_query.message.chat.id)

    if not session_data:
        callback_query.message.reply_text("Session expired. Please search again.")
        return

    last_page = session_data.get('last_page', 1)

    if new_page < 1:
        callback_query.answer("You're already on the first page.", show_alert=True)
    elif new_page > last_page:
        callback_query.answer("You're already on the last page.", show_alert=True)
    else:
        episode_list(client, callback_query, page=new_page)


# ================= Episode download links ================= #
@Client.on_callback_query(filters.regex(r"^ep_"))
def fetch_download_links(client, callback_query: CallbackQuery):
    episode_number = int(callback_query.data.split("_")[1])
    user_id = callback_query.message.chat.id
    session_data = episode_data.get(user_id)

    if not session_data or 'episodes' not in session_data:
        callback_query.message.reply_text("Session expired. Please search again.")
        return

    episodes = session_data['episodes']
    if episode_number not in episodes:
        callback_query.message.reply_text("Episode not found.")
        return

    episode_session = episodes[episode_number]
    episode_data[user_id]['current_episode'] = episode_number

    url = f"https://animepahe.si/play/{session_data['session_id']}/{episode_session}"
    response = session.get(url)
    soup = BeautifulSoup(response.content, "html.parser")

    download_links = soup.select("#pickDownload a.dropdown-item")
    if not download_links:
        callback_query.message.reply_text("No download links found.")
        return

    download_buttons = [
        [InlineKeyboardButton(link.get_text(strip=True), callback_data=f"dl_{link['href']}")]
        for link in download_links
    ]
    reply_markup = InlineKeyboardMarkup(download_buttons)
    callback_query.message.reply_text("Select a download link:", reply_markup=reply_markup)

# ================= Upload Method ================= #
@Client.on_callback_query(filters.regex(r"set_method_"))
def change_upload_method(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    data = callback_query.data.split("_")[2]

    save_upload_method(user_id, data)
    callback_query.answer(f"Upload method set to {data.capitalize()}")

    buttons = [
        [
            InlineKeyboardButton(f"Document ({'✅' if data == 'document' else '❌'})", callback_data="set_method_document"),
            InlineKeyboardButton(f"Video ({'✅' if data == 'video' else '❌'})", callback_data="set_method_video")
        ]
    ]
    callback_query.message.edit_reply_markup(InlineKeyboardMarkup(buttons))


from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Track cancel requests per user
cancel_flags = {}

# ================= Download + Upload ================= #
def can_pin(message):
    return message.chat.type in ["group", "supergroup"]

@Client.on_callback_query(filters.regex(r"^dl_"))
def download_and_upload_file(client, callback_query: CallbackQuery):
    download_url = callback_query.data.split("dl_")[1]
    user_id = callback_query.from_user.id
    chat_id = callback_query.message.chat.id
    username = callback_query.from_user.username or "Unknown User"

    try:
        direct_link = get_dl_link(download_url)
    except Exception as e:
        callback_query.message.reply_text(f"Error generating download link: {str(e)}")
        return

    add_to_queue(user_id, username, direct_link)

    episode_number = episode_data.get(user_id, {}).get('current_episode', 'Unknown')
    title = episode_data.get(user_id, {}).get('title', 'Unknown Title')

    # Extract source/resolution
    download_button_title = next(
        (b.text for row in callback_query.message.reply_markup.inline_keyboard for b in row if b.callback_data == f"dl_{download_url}"),
        "Unknown Source"
    )
    resolution = re.search(r"\b\d{3,4}p\b", download_button_title)
    resolution = resolution.group() if resolution else download_button_title
    dtype = "Dub" if 'eng' in download_button_title.lower() else "Sub"

    short_name = create_short_name(title)
    file_name = f"[{dtype}] [{short_name}] [EP {episode_number}] [{resolution}].mp4"
    filename = sanitize_filename(file_name)
    random_str = random_string(5)

    user_download_dir = os.path.join(DOWNLOAD_DIR, str(user_id), random_str)
    os.makedirs(user_download_dir, exist_ok=True)
    download_path = os.path.join(user_download_dir, filename)

    # Initial progress message
    progress_msg = client.send_message(
        chat_id,
        f"📥 Added to queue:\n<code>{filename}</code>\n<b>Downloading now...</b>",
    )

    # ✅ Pin only in groups
    if can_pin(callback_query.message):
        try:
            client.pin_chat_message(chat_id, progress_msg.id, disable_notification=True)
        except Exception as e:
            logger.warning(f"Pin failed: {e}")

    try:
        # Download
        download_file(direct_link, download_path)
        progress_msg.edit_text("<b>Episode downloaded, uploading...</b>")

        # Prepare thumbnail
        thumb_path = None
        poster_url = episode_data.get(user_id, {}).get("poster")
        user_thumb = get_thumbnail(user_id)

        if user_thumb:
            thumb_path = client.download_media(user_thumb)
        elif poster_url:
            resp = requests.get(poster_url, stream=True)
            thumb_path = os.path.join(user_download_dir, "thumb_file.jpg")
            with open(thumb_path, "wb") as f:
                for chunk in resp.iter_content(1024):
                    f.write(chunk)

        # Caption
        caption = get_caption(user_id) or filename

        # Upload with progress
        send_and_delete_file(
            client,
            chat_id,
            download_path,
            thumb_path,
            caption,
            user_id,
            progress_msg  # ✅ Pass progress message
        )

        remove_from_queue(user_id, direct_link)
        progress_msg.edit_text("<b>✅ Episode Uploaded 🎉</b>")

        # ✅ Unpin only in groups
        if can_pin(callback_query.message):
            try:
                client.unpin_chat_message(chat_id, progress_msg.id)
            except Exception as e:
                logger.warning(f"Unpin failed: {e}")

        # Cleanup
        if thumb_path and os.path.exists(thumb_path):
            os.remove(thumb_path)
        if os.path.exists(user_download_dir):
            remove_directory(user_download_dir)

    except Exception as e:
        logger.error(f"Download/Upload error: {e}")
        progress_msg.edit_text(f"❌ Error: {str(e)}")


# ================= Cancel Handler ================= #
@Client.on_callback_query(filters.regex(r"^cancel_"))
def cancel_upload(client, callback_query: CallbackQuery):
    user_id = int(callback_query.data.split("_")[1])
    cancel_flags[user_id] = True
    callback_query.answer("❌ Upload canceled!", show_alert=True)


# ================= Help / Close ================= #
@Client.on_callback_query()
def callback_query_handler(client, callback_query: CallbackQuery):
    if callback_query.data == "help":
        callback_query.message.edit_text(
            text="Here is how to use the bot:\n\n1. /anime <anime_name> - Search\n2. /set_thumb - Set custom thumbnail\n3. /options - Upload mode\n4. /queue - Active downloads\n5. /set_caption - Custom caption\n6. /see_caption - View caption\n7. /del_caption - Delete caption",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Close", callback_data="close")]])
        )
    elif callback_query.data == "close":
        callback_query.message.delete()
