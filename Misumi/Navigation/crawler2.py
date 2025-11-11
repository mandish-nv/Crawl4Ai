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
    Open a product page, click the Part Numbers tab, and execute a click-and-scrape loop 
    for all paginated pages.
    """
    # 1. JS to click the initial "Part Numbers" tab
    js_initial_click = """
        const delayInMilliseconds = 5000;
        setTimeout(() => {
            const selector = 'a[href="#codeList"]';
            const elementToClick = document.querySelector(selector);
            if (elementToClick) {
                elementToClick.click(); 
            } 
        }, delayInMilliseconds);
    """
    
    # 2. JS to click the Next button (used inside the Python loop)
    JS_NEXT_BUTTON_CLICK = """
        const nextButtonSelector = 'a[aria-label="Next Page"].Pagination_arrowRight__rRbGO';
        const nextButton = document.querySelector(nextButtonSelector);

        // Only click if the button is present AND not disabled (or visually hidden/empty)
        if (nextButton && nextButton.getAttribute('aria-disabled') !== 'true' && nextButton.offsetWidth > 0) {
            nextButton.click();
            return true; // Return true to signal a successful click
        }
        return false; // Return false to signal the end of pagination
    """

    # 3. CSS Selector for the content that appears on EVERY page
    CONTENT_SELECTOR = ".PartNumberColumn_data__mlNqG a"
    # 4. Selector for the Next button itself
    NEXT_BUTTON_SELECTOR = 'a[aria-label="Next Page"].Pagination_arrowRight__rRbGO'
    
    # 5. Session ID to keep the browser page open across iterations
    session_id = f"pagination_session_{hash(url)}"

    all_links: List[Dict[str, str]] = []
    page_num = 1
    has_next_page = True
    
    while has_next_page:
        # Configuration for the current iteration
        run_cfg = CrawlerRunConfig(
            url=url, # URL is needed for the first page load
            session_id=session_id, # **CRITICAL: Keeps the browser session open**
            cache_mode=CacheMode.BYPASS,
            target_elements=[CONTENT_SELECTOR],
            page_timeout=45000,
            # We use wait_for to ensure the content or button is loaded
            wait_for=CONTENT_SELECTOR, 
            wait_for_timeout=15000,
            scan_full_page=True,
            scroll_delay=0.3,
            simulate_user=True,
            verbose=False,
        )
        
        if page_num == 1:
            # First page: Load the URL and click the initial tab
            run_cfg.js_code = [js_initial_click]
            # Use a short delay to ensure the content loads after the tab click
            run_cfg.delay_before_return_html = 10.0 
        else:
            # Subsequent pages: Only execute the 'Next' click JS in the existing session
            run_cfg.js_code = [JS_NEXT_BUTTON_CLICK]
            run_cfg.js_only = True # **CRITICAL: Execute JS without new navigation**
            # Wait for the next button to be clickable again (or for the content to change)
            run_cfg.wait_for = f"css:{CONTENT_SELECTOR}"
            run_cfg.delay_before_return_html = 5.0 # Give the new content a moment to render

        print(f"   -> Scraping Page {page_num}...")
        
        result = await crawler.arun(url=url, config=run_cfg)

        if not result.success:
            print(f"❌ Failed to crawl {url} on page {page_num}: {result.error_message}")
            break

        # 1. SCRAPE CONTENT from the current page
        soup = BeautifulSoup(result.html or "", "html.parser")
        current_page_links = 0
        for a in soup.select(CONTENT_SELECTOR):
            href = a.get("href", "").strip()
            title = a.get("title", "").strip()
            if href:
                all_links.append({
                    "part_number_title": title or href,
                    "part_number_url": href
                })
                current_page_links += 1

        # 2. CHECK FOR NEXT BUTTON
        next_button = soup.select_one(NEXT_BUTTON_SELECTOR)
        
        # Determine if the loop should continue:
        # Check if the button is missing or visually disabled/hidden/aria-disabled
        if next_button is None or next_button.get('aria-disabled') == 'true':
            has_next_page = False
            print(f"   -> No 'Next' button found on page {page_num}. Ending pagination.")
        
        # Safety break if no links were found after the first page, indicating an issue
        if page_num > 1 and current_page_links == 0:
            print(f"   -> Warning: No content found on page {page_num}. Ending pagination to prevent infinite loop.")
            has_next_page = False

        page_num += 1
    
    # CRITICAL: Clean up the session when done
    await crawler.crawler_strategy.kill_session(session_id)
    
    return all_links


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
            # Sanitized title logic remains the same
            safe_title = "".join(c for c in title if c.isalnum() or c in (" ", "_", "-")).rstrip()
            output_file = os.path.join(output_folder, f"{safe_title}.csv")

            print(f"\n🔍 Crawling: {url}")
            # The session management and loop logic is now inside process_url
            part_links = await process_url(crawler, url) 

            if not part_links:
                print(f"⚠️ No part numbers found for {title}")
                continue

            # Write all collected links at once
            with open(output_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=["part_number_title", "part_number_url"])
                writer.writeheader()
                writer.writerows(part_links)

            print(f"✅ Saved {len(part_links)} part numbers → {output_file}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python crawler2.py <input.csv> <output_folder>")
        sys.exit(1)
    asyncio.run(main(sys.argv[1], sys.argv[2]))