import asyncio
import csv
import sys
import os
from typing import List, Dict
from bs4 import BeautifulSoup
from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig, CacheMode

def read_input_csv(input_filename: str) -> List[Dict[str, str]]:
    rows = []
    with open(input_filename, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if "title" in row and "url" in row:
                rows.append({"title": row["title"].strip(), "url": row["url"].strip()})
    return rows


async def process_url(crawler: AsyncWebCrawler, url: str) -> List[Dict[str, str]]:
    """
    Open a product page, click the Part Numbers tab, and extract all product links.
    """
    js_click_code = """
    const delayInMilliseconds = 5000;

    setTimeout(() => {
        const selector = 'a[href="#codeList"]';
        const elementToClick = document.querySelector(selector);
        if (elementToClick) {
            elementToClick.click(); 
        }
    }, delayInMilliseconds);
    """

    run_cfg = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        js_code=js_click_code,
        target_elements=[".PartNumberColumn_data__mlNqG a"],
        page_timeout=45000,
        delay_before_return_html=10.0,
        scan_full_page=True,
        scroll_delay=0.3,
        simulate_user=True,
        verbose=False,
        wait_for=".PartNumberColumn_data__mlNqG a"
    )

    result = await crawler.arun(url=url, config=run_cfg)

    links: List[Dict[str, str]] = []
    if not result.success:
        print(f"❌ Failed to crawl {url}: {result.error_message}")
        return links

    soup = BeautifulSoup(result.html or "", "html.parser")
    for a in soup.select(".PartNumberColumn_data__mlNqG a"):
        href = a.get("href", "").strip()
        title = a.get("title", "").strip()
        if href:
            links.append({
                "part_number_title": title or href,
                "part_number_url": href
            })
    return links


async def main(input_csv: str, output_folder: str):
    rows = read_input_csv(input_csv)
    if not rows:
        print("No URLs to process.")
        return

    os.makedirs(output_folder, exist_ok=True)

    browser_cfg = BrowserConfig(
        headless=False,
        user_agent_mode="random",
        java_script_enabled=True,
        viewport={"width": 1440, "height": 900},
    )

    async with AsyncWebCrawler(config=browser_cfg) as crawler:
        for row in rows:
            title = row["title"]
            url = row["url"]
            safe_title = "".join(c for c in title if c.isalnum() or c in (" ", "_", "-")).rstrip()
            output_file = os.path.join(output_folder, f"{safe_title}.csv")

            print(f"🔍 Crawling: {url}")
            part_links = await process_url(crawler, url)

            if not part_links:
                print(f"⚠️ No part numbers found for {title}")
                continue

            with open(output_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=["part_number_title", "part_number_url"])
                writer.writeheader()
                writer.writerows(part_links)

            print(f"✅ Saved {len(part_links)} part numbers → {output_file}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python crawl_parts.py <input.csv> <output_folder>")
        sys.exit(1)
    asyncio.run(main(sys.argv[1], sys.argv[2]))
