# plugins/update.py
# Update Bot from Git Repository
# Credits: Xen & Incredaimaso ❤️

import os
import asyncio
import logging
from pyrogram import Client, filters
from subprocess import run as srun, PIPE
from config import ADMIN

# Setup logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Configure your repo/branch
UPSTREAM_REPO = "https://github.com/Incredaimaso/AnimePaheBot"
UPSTREAM_BRANCH = "main"


def run_cmd(cmd: str):
    """Run shell command and return (success, output)."""
    result = srun(cmd, shell=True, stdout=PIPE, stderr=PIPE, text=True)
    return result.returncode == 0, result.stdout.strip() or result.stderr.strip()


@Client.on_message(filters.command("update") & filters.user(ADMIN))
async def update_repo(client, message):
    if not UPSTREAM_REPO:
        await message.reply_text("⚠️ UPSTREAM_REPO is not set in update.py")
        return

    m = await message.reply_text("🔄 Checking for updates...")

    # Ensure .git exists
    if not os.path.exists(".git"):
        run_cmd("git init -q")
        run_cmd('git config --global user.email "bot@example.com"')
        run_cmd('git config --global user.name "AnimeBot"')
        run_cmd(f"git remote add origin {UPSTREAM_REPO}")

    # Fetch updates
    success, fetch_output = run_cmd(f"git fetch origin {UPSTREAM_BRANCH} -q")
    if not success:
        await m.edit(f"❌ Update failed while fetching:\n<code>{fetch_output}</code>")
        return

    # Compare local vs remote
    success, diff_output = run_cmd(f"git diff --stat HEAD..origin/{UPSTREAM_BRANCH}")
    if success and not diff_output:
        await m.edit("✅ Already up-to-date with upstream repo.")
        return

    # Reset to latest
    success, reset_output = run_cmd(f"git reset --hard origin/{UPSTREAM_BRANCH} -q")
    if not success:
        await m.edit(f"❌ Update failed while resetting:\n<code>{reset_output}</code>")
        return

    # Get latest commit info
    success, log_output = run_cmd("git log -1 --pretty=format:'%h - %s (%an)'")
    if not success:
        log_output = "No commit info."

    reply_text = (
        "✅ <b>Update Successful!</b>\n\n"
        f"<b>Latest Commit:</b>\n<code>{log_output}</code>\n\n"
        f"<b>Changes:</b>\n<code>{diff_output}</code>\n\n"
        "♻️ Restarting bot with <code>python3 bot.py</code>..."
    )

    await m.edit(reply_text)

    # Restart bot
    await asyncio.sleep(3)
    os.execvp("python3", ["python3", "bot.py"])
