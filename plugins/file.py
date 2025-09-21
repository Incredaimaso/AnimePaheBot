#..........This Bot Made By [RAHAT](https://t.me/r4h4t_69)..........#
#..........Anyone Can Modify This As He Likes..........#
#..........Just one requests do not remove my credit..........#

import requests
import os
import string
import random
import shutil
import re
from helper.database import*
from plugins.headers import session
import subprocess
import json
from config import LOG_CHANNEL
import time


def create_short_name(name):
    # Check if the name length is greater than 25
    if len(name) > 30:
        # Extract all capital letters from the name
        short_name = ''.join(word[0].upper() for word in name.split())					
        return short_name    
    return name
    
def get_media_details(path):
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-hide_banner",
                "-loglevel", "error",
                "-print_format", "json",
                "-show_format",
                "-show_streams",
                path,
            ],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            print(f"FFprobe error:\n{result.stderr}")
            return None, None, None

        media_info = json.loads(result.stdout)

        video_stream = next(
            (stream for stream in media_info.get("streams", []) if stream.get("codec_type") == "video"),
            None
        )

        # Safe parsing
        width = video_stream.get("width") if video_stream else None
        height = video_stream.get("height") if video_stream else None
        duration = media_info.get("format", {}).get("duration")

        # Force convert to safe numeric or None
        def safe_int(val):
            try:
                return int(float(val))
            except (TypeError, ValueError):
                return None

        return safe_int(width), safe_int(height), safe_int(duration)

    except Exception as e:
        print(f"FFprobe exception: {e}")
        return None, None, None

def download_file(url, download_path):
    try:
        with session.get(url, stream=True, verify=False) as r:  # use shared session, skip SSL verify
            r.raise_for_status()
            with open(download_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
        return download_path
    except Exception as e:
        raise RuntimeError(f"Download failed for {url}: {e}")


def sanitize_filename(file_name):
    # Remove invalid characters from the file name
    file_name = re.sub(r'[<>:"/\\|?*]', '', file_name)
    return file_name
    
        
'''def send_and_delete_file(client, chat_id, file_path, thumbnail=None, caption="", user_id=None):
    upload_method = get_upload_method(user_id)  # Retrieve user's upload method
    
    try:
        if upload_method == "document":
            # Send as document
            client.send_document(
                chat_id,
                file_path,
                thumb=thumbnail if thumbnail else None,
                caption=caption
            )
        else:
            # Send as video
            client.send_video(
                chat_id,
                file_path,
                #thumb=thumbnail if thumbnail else None,
                thumb=None,
                caption=caption
            )
        
        os.remove(file_path)  # Delete the file after sending
        
    except Exception as e:
        client.send_message(chat_id, f"Error: {str(e)}")'''


from helper.utils import format_upload_progress
import time
import os

def send_and_delete_file(client, chat_id, file_path, thumbnail=None, caption="", user_id=None, progress_msg=None):
    upload_method = get_upload_method(user_id)  # Retrieve user's upload method
    forwarding_channel = LOG_CHANNEL  # Channel to forward the file

    try:
        user_info = client.get_users(user_id)
        user_details = f"Downloaded by: @{user_info.username if user_info.username else 'Unknown'} (ID: {user_id})"
        caption_with_info = f"{caption}\n\n{user_details}"

        start_time = time.time()
        last_update = 0  # prevent spamming

        # --- Progress callback ---
        def progress(current, total):
            nonlocal last_update
            now = time.time()
            diff = now - start_time
            speed = current / diff if diff > 0 else 0
            eta = int((total - current) / speed) if speed > 0 else 0

            if progress_msg and (now - last_update >= 10 or current == total):  # update every 10s
                last_update = now
                try:
                    progress_text = format_upload_progress(
                        os.path.basename(file_path),
                        current,
                        total,
                        speed,
                        eta,
                        "Document" if upload_method == "document" else "Video"
                    )
                    progress_msg.edit_text(progress_text)
                except Exception:
                    pass

        # --- Upload file ---
        if upload_method == "document":
            sent_message = client.send_document(
                chat_id,
                file_path,
                thumb=thumbnail if thumbnail else None,
                caption=caption or os.path.basename(file_path),
                progress=progress,
                progress_args=()
            )
        else:
            # Extract media info safely
            details = get_media_details(file_path)
            width = height = duration = None
            if details:
                w, h, d = details

                try:
                    width = int(w) if w not in [None, "", "N/A"] else None
                except Exception:
                    width = None

                try:
                    height = int(h) if h not in [None, "", "N/A"] else None
                except Exception:
                    height = None

                try:
                    duration = int(float(d)) if d not in [None, "", "N/A"] else None
                except Exception:
                    duration = None

            sent_message = client.send_video(
                chat_id,
                file_path,
                duration=duration,
                width=width,
                height=height,
                supports_streaming=True,
                has_spoiler=True,
                thumb=thumbnail if thumbnail else None,
                caption=caption or os.path.basename(file_path),
                progress=progress,
                progress_args=()
            )

        # --- Forward to log channel ---
        client.copy_message(
            chat_id=forwarding_channel,
            from_chat_id=chat_id,
            message_id=sent_message.id,
            caption=caption_with_info
        )

        # --- Cleanup ---
        if os.path.exists(file_path):
            os.remove(file_path)
        if thumbnail and os.path.exists(thumbnail):
            os.remove(thumbnail)

        if progress_msg:
            progress_msg.edit_text(f"✅ Upload complete:\n<code>{os.path.basename(file_path)}</code>")

    except Exception as e:
        client.send_message(chat_id, f"❌ Upload Error: {str(e)}")
        

def remove_directory(directory_path):
    if not os.path.exists(directory_path):
        raise FileNotFoundError(f"The directory '{directory_path}' does not exist.")
    
    try:
        shutil.rmtree(directory_path)
        #print(f"Directory '{directory_path}' has been removed successfully.")
    except PermissionError as e:
        print(f"Permission denied: {e}")
    except Exception as e:
        print(f"An error occurred while removing the directory: {e}")

def random_string(length):
    if length < 1:
        raise ValueError("Length must be a positive integer.")
    
    # Define the characters to choose from (letters and digits)
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))


