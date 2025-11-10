import asyncio
from crawl4ai import AsyncWebCrawler
# Import necessary config classes for advanced features
from crawl4ai.async_configs import (
    BrowserConfig,
    CrawlerRunConfig,
    CacheMode,
    ProxyConfig,
)
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from crawl4ai.deep_crawling import BFSDeepCrawlStrategy
from crawl4ai.deep_crawling.filters import FilterChain, URLPatternFilter
# from crawl4ai.async_configs import RoundRobinProxyStrategy # Strategy for rotating proxies
import re
from bs4 import BeautifulSoup

# Define example proxy configurations
# In a real-world scenario, you would load these securely from a file or environment variables.
EXAMPLE_PROXIES = [
    ProxyConfig(
        server="http://192.168.1.1:8000",
        username="user1_rotate",
        password="pass123"
    ),
    ProxyConfig(
        server="http://192.168.1.2:8000",
        username="user2_rotate",
        password="pass456"
    ),
]

# Instantiate the proxy rotation strategy
# proxy_rotation_strategy = RoundRobinProxyStrategy(EXAMPLE_PROXIES)


async def crawlScrap():
    
    browser_config = BrowserConfig(
        # ---------- browser basics ----------
        browser_type = "chromium",         # chromium is usually best-supported
        headless = False,                  # False is slightly more stealthy; set True for CI
        browser_mode = "dedicated",        # fresh instance per run
        use_managed_browser = False,       # local browser
        # cdp_url = None,                    # launch locally
        use_persistent_context = False,    # False => fresh context each run (incognito-like)
        # user_data_dir = None,              # None => temporary profile (no cached cookies)
        chrome_channel = "msedge",
        channel = "msedge",

        # ---------- networking / proxy ----------
        proxy_config = None,               # or MY_PROXY / rotation strategy
        host = "localhost",

        # ---------- viewport / downloads ----------
        viewport_width = 1920,
        viewport_height = 1080,
        accept_downloads = False,

        # ---------- security / rendering ----------
        ignore_https_errors = True,
        java_script_enabled = True,
        text_mode = False,
        light_mode = False,

        # ---------- stealth & anti-detection ----------
        # enable_stealth = True,             # enable stealth techniques (navigator, webdriver, etc)
        # add common args that help avoid automation flags and improve stealth in containers
        extra_args = [
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-blink-features=AutomationControlled",
            "--disable-infobars",
            "--disable-web-security",
            "--start-maximized",
            "--window-size=1920,1080",
        ],

        # ---------- agent / headers ----------
        # prefer rotating/randomized UA over hard-coded UA
        # user_agent = None,                 # leave None when using user_agent_mode="random"
        user_agent_mode = "random",        # 'random' or 'rotate' is better than 'manual'
        # user_agent_generator_config = {
        #     # optional: bias toward recent desktop agents; provider-specific config allowed
        #     "platform": "windows",
        #     "device": "desktop",
        # },

        # you can set default headers (Accept-Language is useful)
        headers = {
            "Accept-Language": "en-US,en;q=0.9",
            # "Referer": "https://www.google.com/",  # consider setting when appropriate
        },

        # ---------- automation control & debugging ----------
        sleep_on_close = False,
        verbose = True,
    )

    run_config = CrawlerRunConfig(
        # ==============================================================================
        # CRAWL CONTENT EXTRACTION & CLEANING
        # ==============================================================================
        word_count_threshold = 50,
        markdown_generator = DefaultMarkdownGenerator(),
        only_text = False,
        excluded_tags = ['header', 'nav', 'footer', 'aside', 'form', 'script', 'style'],
        remove_forms = True,
        parser_type = "lxml",

        # ==============================================================================
        # NETWORK, PROXY, AND CACHING (UPDATED WITH EXAMPLE VALUES)
        # ==============================================================================
        # 1. proxy_config: Configuration for a single static proxy (if not using rotation)
        # proxy_config = ProxyConfig(
        #     server="http://static.proxyprovider.com:8888",
        #     username="static_user",
        #     password="static_password"
        # ),
        
        # 2. proxy_rotation_strategy: Uses the imported strategy for multiple proxies
        # proxy_rotation_strategy = proxy_rotation_strategy,
        
        disable_cache = False,
        no_cache_read = False,
        no_cache_write = False,
        method = "GET",
        check_robots_txt = False,
        
        # 3. user_agent_mode: Enables user agent randomization/rotation
        user_agent_mode="random", # Set to "random" or "rotate" to enable dynamic UAs
        
        # 4. user_agent_generator_config: Narrows down the generated user agents
        user_agent_generator_config={},

        # ==============================================================================
        # BROWSER TIMING & DYNAMIC RENDERING
        # ==============================================================================
        delay_before_return_html = 20.0,
        mean_delay = 2.0,
        max_range = 6.0,
        semaphore_count = 5,
        js_code = """
        (async () => {
            for (let i = 0; i < 10; i++) {
                window.scrollBy(0, window.innerHeight);
                await new Promise(r => setTimeout(r, 1500));
            }
            return true;
        })();
        """,
        scan_full_page = True,
        scroll_delay = 2,
        max_scroll_steps = 20,
        process_iframes = False,
        remove_overlay_elements = True,
        simulate_user = True,
        override_navigator = True,
        magic = True,
        adjust_viewport_to_content = True,

        # ==============================================================================
        # LINK FILTERING & CRAWLING
        # ==============================================================================
        exclude_social_media_domains = [],
        exclude_external_links = True,
        exclude_social_media_links = True,
        exclude_domains = [],
        deep_crawl_strategy = BFSDeepCrawlStrategy(
            max_pages=1,
            max_depth=0,
            include_external=False,
        ),

        # ==============================================================================
        # DEBUGGING & EXPERIMENTAL
        # ==============================================================================
        verbose = True,
        log_console = False,
        capture_network_requests = False,
        capture_console_messages = False,
        experimental = {},
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        results = await crawler.arun(
            url="https://us.misumi-ec.com/vona2/detail/110310764549/?searchFlow=results2products&KWSearch=linear%20shaft&list=PageCategory",
            config=run_config,
            deep_crawl=False
        )

        if results:
            total = len(results)
            print(f"✅ Total pages crawled: {total}")


            # Open the markdown file for writing (will create it if it doesn't exist)
            with open("markdown.md", "w", encoding="utf-8") as m:
                for i, result in enumerate(results, start=1):
                    if hasattr(result, "url") and result.url:
                        print(f"✅ [{i}/{total}] Processing: {result.url}")

                    if hasattr(result, "html") and result.html:
                        html = result.html
                        soup = BeautifulSoup(html, "html.parser")

                        # --- MODIFICATION START ---
                        # Select only <table> elements within the .l-adaptive-content container
                        tables = soup.select(".l-adaptive-content table")

                        content = ""

                        # Only include the string representation of the <table> elements
                        if tables:
                            print(f"   Found {len(tables)} table(s). Storing...")
                            for table in tables:
                                # Store the complete HTML of the table
                                content += str(table) + "\n\n"
                        else:
                            print(f"⚠️ No matching <table> found in {result.url}")
                        # --- MODIFICATION END ---

                        # Write content (the tables' HTML) to the markdown file
                        # We use the '---' separator for organization
                        if content:
                            m.write(f"<!-- Tables from: {result.url} -->\n")
                            m.write(content)
                            m.write("\n\n---\n\n")

        else:
            print("❌ Crawl failed or returned no results.")

if __name__ == "__main__":
    asyncio.run(crawlScrap())
