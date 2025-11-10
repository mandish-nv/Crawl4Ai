import asyncio
import csv
from bs4 import BeautifulSoup
from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai.deep_crawling import BFSDeepCrawlStrategy
# from crawl4ai.link_filter import LinkFilter


def save_to_csv(data: list[dict], filename: str):
    """Save extracted link data to CSV."""
    if not data:
        print("No data to save.")
        return
    fieldnames = list(data[0].keys())
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    print(f"✅ Saved {len(data)} rows to {filename}")


async def crawler1():
    # --- Browser configuration ---
    browser_config = BrowserConfig(
        browser_type="chromium",
        headless=False,
        # enable_stealth=True,
        user_agent_mode="random",
        ignore_https_errors=True,
        java_script_enabled=True,
        text_mode=True,
        light_mode=True,
        viewport={"width": 1440, "height": 900},
    )

    # # --- Deep crawl setup: disable following links ---
    # link_filter = LinkFilter(
    #     include_patterns=[],  # don’t include anything else
    #     exclude_patterns=[".*"]  # exclude all other URLs
    # )
    deep_crawl_strategy = BFSDeepCrawlStrategy(
        max_depth=0,
        include_external=False,
        # link_filter=link_filter
    )

    # --- Crawler run configuration ---
    run_config = CrawlerRunConfig(
        deep_crawl_strategy=deep_crawl_strategy,
        cache_mode=CacheMode.BYPASS,
        scan_full_page=True,
        scroll_delay=0.5,
        # wait_until="networkidle",
        verbose=True,
        
        target_elements=[".Link_primary__7Eh11"],
        page_timeout=45000,          # 45 seconds timeout for page navigation/loading
        delay_before_return_html = 10.0,  # replace with wait for config
        mean_delay = 2.0,                   # Average random delay (in seconds) between requests to simulate human behavior.
        max_range = 4.0,                           # The maximum variation (randomness) for the delay calculation.
        remove_overlay_elements = True,           # Attempts to hide or remove sticky headers, consent popups, etc.
        simulate_user = True,                     # Enables aggressive user behavior simulation (e.g., random mouse movements).
        override_navigator = True,                # Enables techniques to spoof browser properties to prevent bot detection.
        magic = True,                             # Placeholder for aggressive, pre-configured stealth/anti-detection settings.
        adjust_viewport_to_content = True,        # Automatically adjusts the browser viewport size to match content dimensions.
        exclude_external_links = True,            # If True, filters out links pointing to other domains.
        exclude_social_media_links = True,        # If True, filters out links pointing to social media domains.   
    )

    # --- Start crawling ---
    async with AsyncWebCrawler(config=browser_config) as crawler:
        results = await crawler.arun(
            url="https://us.misumi-ec.com/vona2/mech_screw/M1808000000/",
            config=run_config,
            deep_crawl=False
        )

    # --- Extract product links ---
    all_links = []
    for result in results:
        if not result.html:
            continue

        # Parse HTML of the loaded page
        soup = BeautifulSoup(result.html, "html.parser")

        # Find anchors under the desired class
        for a in soup.select(".Link_primary__7Eh11"):
            href = a.get("href")
            text = a.get_text(strip=True)
            if href and text:
                # Resolve relative URLs if needed
                if href.startswith("/"):
                    href = "https://us.misumi-ec.com" + href
                all_links.append({"title": text, "url": href})

    # --- Save results ---
    if all_links:
        save_to_csv(all_links, "misumi_product_links.csv")
    else:
        print("No product links found.")


if __name__ == "__main__":
    asyncio.run(crawler1())
