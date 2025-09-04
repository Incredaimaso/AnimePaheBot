import math
import time

def humanbytes(size):
    # Format bytes to human-readable
    if not size:
        return "0 B"
    power = 2**10
    n = 0
    power_labels = ['B', 'KB', 'MB', 'GB', 'TB']
    while size >= power and n < len(power_labels) - 1:
        size /= power
        n += 1
    return f"{size:.2f} {power_labels[n]}"

def time_formatter(seconds):
    return time.strftime("%M:%S", time.gmtime(seconds))

def progress_bar(progress, total, length=20):
    percent = progress / total
    filled = int(length * percent)
    bar = "▰" * filled + "▱" * (length - filled)
    return f"[{bar}]"

def format_upload_progress(filename, uploaded, total, speed, eta, mode):
    bar = progress_bar(uploaded, total)
    percent = round((uploaded / total) * 100, 2)

    return (
        f"📤 Uploading as {mode} {'📄' if mode == 'Document' else 'Video'}...\n"
        f"<code>{filename}</code>\n\n"
        f"<code>{bar}</code>\n"
        f"╭━━━━❰ᴘʀᴏɢʀᴇss ʙᴀʀ❱━➣\n"
        f"┣⪼ 🗃️ Sɪᴢᴇ: <code>{humanbytes(uploaded)} | {humanbytes(total)}</code>\n"
        f"┣⪼ ⏳️ Dᴏɴᴇ : <code>{percent}%</code>\n"
        f"┣⪼ 🚀 Sᴩᴇᴇᴅ: {humanbytes(speed)}/s\n"
        f"┣⪼ ⏰️ Eᴛᴀ: {time_formatter(eta)}\n"
        f"╰━━━━━━━━━━━━━━━➣"
    )

import time
from pyrogram.types import Message

# Progress callback
async def progress_callback(current, total, client, message: Message, filename: str, mode: str, start_time: float):
    try:
        elapsed_time = time.time() - start_time
        speed = current / elapsed_time if elapsed_time > 0 else 0
        eta = (total - current) / speed if speed > 0 else 0

        progress_text = format_upload_progress(
            filename=filename,
            uploaded=current,
            total=total,
            speed=speed,
            eta=eta,
            mode=mode.capitalize()
        )
        await message.edit_text(progress_text)
    except Exception:
        pass
