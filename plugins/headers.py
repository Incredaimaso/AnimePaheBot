from pyppeteer import launch
from bs4 import BeautifulSoup
import asyncio

HEADERS = {
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
}

async def search_anime_html(query: str):
    browser = await launch(headless=True, args=['--no-sandbox'])
    try:
        page = await browser.newPage()
        await page.setUserAgent(HEADERS['user-agent'])

        # Go to homepage
        await page.goto('https://animepahe.ru', {'waitUntil': 'domcontentloaded'})

        # Type search query
        await page.type('#search', query)
        await asyncio.sleep(3)  # Wait for dropdown to populate

        content = await page.content()
        soup = BeautifulSoup(content, "html.parser")

        results = []
        for item in soup.select("ul#list > li > a"):
            title = item.get("title") or item.text.strip()
            href = item.get("href")
            if "/anime/" in href:
                session = href.split("/anime/")[-1]
                results.append({"title": title, "session": session})

        return results
    finally:
        await browser.close()
