import asyncio
import csv
import sys
import os
import yaml
from typing import List, Dict, Any
from bs4 import BeautifulSoup
from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig, CacheMode

# A global variable to hold our config data
CONFIG: Dict[str, Any] = {}

def load_config(config_path: str):
    """Load configuration from a YAML file."""
    global CONFIG
    try:
        with open(config_path, 'r') as f:
            CONFIG = yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Error: Config file not found at {config_path}")
        sys.exit(1)
    except yaml.YAMLError as exc:
        print(f"Error parsing YAML config: {exc}")
        sys.exit(1)

def read_input_csv(input_filename: str) -> List[Dict[str, str]]:
    # ... (function remains the same as it's independent of website config)
    rows = []
    try:
        with open(input_filename, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if "title" in row and "url" in row:
                    rows.append({"title": row["title"].strip(), "url": row["url"].strip()})
    except FileNotFoundError:
        print(f"Error: Input CSV not found at {input_filename}")
        sys.exit(1)
    return rows


async def process_url(crawler: AsyncWebCrawler, url: str) -> List[Dict[str, str]]:
    """
    Open a product page, click the Part Numbers tab, and execute a click-and-scrape loop 
    for all paginated pages.
    """
    # Get config values
    cfg = CONFIG["website"]
    selectors = cfg["selectors"]
    js_code = cfg["javascript"]
    timing = cfg["timing"]
    
    CONTENT_SELECTOR = selectors["content_element"]
    NEXT_BUTTON_SELECTOR = selectors["next_button"]

    # 1. JS to click the initial "Part Numbers" tab - injected selector
    js_initial_click = js_code["initial_tab_click_js"].replace(
        "%INITIAL_TAB_SELECTOR%", selectors["initial_tab_click"]
    )
    
    # 2. JS to click the Next button - injected selector
    JS_NEXT_BUTTON_CLICK = js_code["next_button_click_js"].replace(
        "%NEXT_BUTTON_SELECTOR%", NEXT_BUTTON_SELECTOR
    )
    
    session_id = f"pagination_session_{hash(url)}"
    all_links: List[Dict[str, str]] = []
    page_num = 1
    has_next_page = True
    
    while has_next_page:
        # Configuration for the current iteration (from config)
        run_cfg = CrawlerRunConfig(
            url=url,
            session_id=session_id,
            cache_mode=CacheMode.BYPASS,
            target_elements=[CONTENT_SELECTOR],
            page_timeout=timing["page_timeout_ms"],
            wait_for=CONTENT_SELECTOR, 
            wait_for_timeout=timing["wait_for_timeout_ms"],
            scan_full_page=True,
            scroll_delay=timing["scroll_delay_sec"],
            simulate_user=True,
            verbose=False,
        )
        
        if page_num == 1:
            run_cfg.js_code = [js_initial_click]
            run_cfg.delay_before_return_html = timing["delay_after_initial_click"]
        else:
            run_cfg.js_code = [JS_NEXT_BUTTON_CLICK]
            run_cfg.js_only = True
            run_cfg.wait_for = f"css:{CONTENT_SELECTOR}"
            run_cfg.delay_before_return_html = timing["delay_after_next_click"]

        print(f"  -> Scraping Page {page_num}...")
        
        result = await crawler.arun(url=url, config=run_cfg)

        if not result.success:
            print(f"❌ Failed to crawl {url} on page {page_num}: {result.error_message}")
            break

        # 1. SCRAPE CONTENT from the current page (Uses the configured CONTENT_SELECTOR)
        soup = BeautifulSoup(result.html or "", "html.parser")
        current_page_links = 0
        for a in soup.select(CONTENT_SELECTOR):
            title = a.text.strip()
            # Get the URL
            href = a.get("href", "").strip()
            
            if not title:
                continue # Skip if there's no title text inside <a>

            if href:
                # Store title AND url
                all_links.append({
                    "part_number_title": title,
                    "part_number_url": href
                })
            else:
                # Store only title if no url is attached
                all_links.append({
                    "part_number_title": title,
                    "part_number_url": "" # Store an empty string for the URL
                })
            current_page_links += 1

        # 2. CHECK FOR NEXT BUTTON (Uses the configured NEXT_BUTTON_SELECTOR)
        next_button = soup.select_one(NEXT_BUTTON_SELECTOR)
        
        if next_button is None or next_button.get('aria-disabled') == 'true':
            has_next_page = False
            print(f"   -> No 'Next' button found on page {page_num}. Ending pagination.")
        
        if page_num > 1 and current_page_links == 0:
            print(f"   -> Warning: No content found on page {page_num}. Ending pagination to prevent infinite loop.")
            has_next_page = False

        page_num += 1
    
    await crawler.crawler_strategy.kill_session(session_id)
    return all_links


async def main(input_csv: str, output_folder: str):
    rows = read_input_csv(input_csv)
    if not rows:
        print("No URLs to process.")
        return

    os.makedirs(output_folder, exist_ok=True)
    
    # Get browser config from the loaded CONFIG global
    browser_cfg_data = CONFIG["crawler"]["browser"]
    browser_cfg = BrowserConfig(
        headless=browser_cfg_data["headless"],
        user_agent_mode=browser_cfg_data["user_agent_mode"],
        java_script_enabled=browser_cfg_data["java_script_enabled"],
        viewport=browser_cfg_data["viewport"],
    )

    async with AsyncWebCrawler(config=browser_cfg) as crawler:
        for row in rows:
            title = row["title"]
            url = row["url"]
            safe_title = "".join(c for c in title if c.isalnum() or c in (" ", "_", "-")).rstrip()
            output_file = os.path.join(output_folder, f"{safe_title}.csv")

            print(f"\n🔍 Crawling: {url}")
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
    if len(sys.argv) != 4:
        # python crawler.py crawler1_nsk_config.yaml test.csv test
        print("Usage: python crawler.py <config.yaml> <input.csv> <output_folder>")
        sys.exit(1)
        
    config_file = sys.argv[1]
    input_file = sys.argv[2]
    output_dir = sys.argv[3]
    
    load_config(config_file)
    asyncio.run(main(input_file, output_dir))