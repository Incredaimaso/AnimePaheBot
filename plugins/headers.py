import asyncio
import json
from pyppeteer import launch

HEADERS = {
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
}

async def get_html(url: str) -> str:
    browser = await launch(headless=True, args=['--no-sandbox'])
    try:
        page = await browser.newPage()
        await page.setUserAgent(HEADERS['user-agent'])
        await page.goto(url, {'waitUntil': 'networkidle2', 'timeout': 60000})
        await asyncio.sleep(4)
        return await page.content()
    finally:
        await browser.close()

async def get_api_json(query: str):
    url = f"https://animepahe.ru/api?m=search&q={query.replace(' ', '+')}"
    html = await get_html(url)
    try:
        return json.loads(html)
    except json.JSONDecodeError:
        print("❌ JSON decode failed. Possibly a JS challenge page.")
        return None
