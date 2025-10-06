import asyncio
import base64
import os
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, ProxyConfig, ProxyRotationStrategy
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

async def scrape_url(semaphore, crawler, url, config):
    async with semaphore:
        try:
            print(f"🔗 Scraping: {url}")
            result = await crawler.arun(url, config=config)

            if result.success:
                html = result.html
                soup = BeautifulSoup(html, "html.parser")
                divs = soup.find_all("div", class_="Ms6aG")

                content = ""
                if divs:
                    for div in divs:
                        content += str(div) + "\n\n"
                else:
                    print(f"⚠️ No <div class='Ms6aG'> found in {url}")
                    print(html)
                return content

            else:
                print(f"❌ Failed to scrape {url}: {result.error_message}")
                return ""
        except Exception as e:
            print(f"❌ Error scraping {url}: {e}")
            return ""


async def scrape_filtered_urls_throttled(concurrency_limit=1):
    print(f"🚀 Starting throttled scraping with concurrency limit: {concurrency_limit}")

    with open("filtered_urls.txt", "r", encoding="utf-8") as f:
        urls = [line.strip() for line in f if line.strip()]

    if not urls:
        print("❌ No URLs found in filtered_urls.txt")
        return

    config = CrawlerRunConfig(
        # --- LAZY LOADING & DELAY HANDLING ---
        delay_before_return_html=10.0,   # Increased wait time for rendering
        scroll_delay=1.5,                # Add small pauses during scroll to mimic human
        max_scroll_steps=10,              # Limit scrolls to avoid infinite loops
        js_code="""
            // Scroll to bottom to trigger lazy loading
            window.scrollTo(0, document.body.scrollHeight); 
            return true;
        """,

        # --- CONTENT TARGETING ---
        # css_selector='.Ms6aG',
        markdown_generator=DefaultMarkdownGenerator(),
        # target_elements=['.Ms6aG'],
        only_text=False,

        # --- ROBUSTNESS & CLEANING ---
        scan_full_page=True,
        excluded_tags=['script', 'style', 'header', 'footer', 'nav', 'aside'],
        parser_type="lxml",

        # # --- ANTI-SCRAPING / STEALTH OPTIONS ---
        # proxy_config=ProxyConfig(
        #     server="",  # Use rotating proxies
        #     username="",
        #     password="",
        #     ip=""
        # ),
        # proxy_rotation_strategy=ProxyRotationStrategy(
            
        #     ),     # Rotate IPs between requests

        user_agent_mode="rotate",                  # Rotate user agents
        user_agent_generator_config={
            "device_types": ["desktop", "mobile"], # Mimic real browsers
            "browsers": ["chrome", "firefox", "edge"],
        },

        simulate_user=True,                        # Simulate mouse/keyboard behavior
        override_navigator=False,                   # Fake navigator.webdriver=false
        adjust_viewport_to_content=True,           # Match viewport to page

        # check_robots_txt=False,                    # Avoid blocking if robots.txt disallows
        
        # --- TIMING BEHAVIORS (avoid patterns) ---
        mean_delay=2.0,                            # Random delay between actions
        max_range=5.0,
    )

    scraped_content = ""
    semaphore = asyncio.Semaphore(concurrency_limit)

    async with AsyncWebCrawler() as crawler:
        tasks = [scrape_url(semaphore, crawler, url, config) for url in urls]
        results = await asyncio.gather(*tasks)

        for content in results:
            scraped_content += content

    output_filename = "scraped_output.md"
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(scraped_content)

    print(f"✅ Throttled scraping complete. Saved to {output_filename}")


if __name__ == "__main__":
    asyncio.run(scrape_filtered_urls_throttled(concurrency_limit=1))
