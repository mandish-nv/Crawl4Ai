import asyncio
import json
import argparse
import logging
import httpx
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BrowserConfig
from crawl4ai.content_scraping_strategy import LXMLWebScrapingStrategy
from crawl4ai.deep_crawling import BestFirstCrawlingStrategy, DFSDeepCrawlStrategy
from crawl4ai.deep_crawling.filters import (
    FilterChain,
    DomainFilter,
    URLPatternFilter,
)
from crawl4ai.deep_crawling.scorers import KeywordRelevanceScorer

def validate_config(config, website_name):
    """Validates the structure and types of the configuration."""
    if 'start_url' not in config:
        raise ValueError(f"'start_url' is missing for website '{website_name}'.")
    if 'allowed_domains' not in config or not isinstance(config['allowed_domains'], list):
        raise ValueError(f"'allowed_domains' must be a list for website '{website_name}'.")
    if 'max_depth' in config and not isinstance(config['max_depth'], int):
        raise ValueError(f"'max_depth' must be an integer for website '{website_name}'.")
    return True

def load_config(website_name, config_path='config.json'):
    """Loads and validates the configuration for a specific website."""
    try:
        with open(config_path, 'r') as f:
            full_config = json.load(f)
    except FileNotFoundError:
        logging.error(f"Config file not found at {config_path}")
        return None
    except json.JSONDecodeError:
        logging.error(f"Error decoding JSON from {config_path}. Please check for syntax errors.")
        return None

    try:
        default_config = full_config.get('default', {})
        website_config = full_config['websites'][website_name]

        config = {**default_config, **website_config}
        validate_config(config, website_name)
        return config
    except KeyError:
        logging.error(f"Website '{website_name}' not found in the config file, or the file has an invalid structure (missing 'websites' key).")
        return None
    except ValueError as e:
        logging.error(f"Configuration error for '{website_name}': {e}")
        return None

def setup_crawler_config(config):
    """Sets up the crawler configuration based on the loaded config."""
    filter_chain = FilterChain([
        DomainFilter(allowed_domains=config.get('allowed_domains', [])),
        URLPatternFilter(patterns=config.get('url_patterns', [])),
    ])

    keyword_scorer = KeywordRelevanceScorer(
        keywords=list(config.get('keywords', {}).keys()),
        weight=0.7
    )
    show_more_js = """
    const btn = document.querySelector('#children-product-on-show-more');
    if (btn && btn.style.display !== 'none') {
        btn.click();
    }
    """
    crawler_run_config = CrawlerRunConfig(
        deep_crawl_strategy=BestFirstCrawlingStrategy(
            max_depth=config.get('max_depth', 2),
            include_external=config.get('include_external', False),
            filter_chain=filter_chain,
            url_scorer=keyword_scorer,

        ),
        page_timeout = 120000,
        scraping_strategy=LXMLWebScrapingStrategy(),
        stream=True,
        verbose=config.get('verbose', True),
        scan_full_page=config.get('scan_full_page', True),
        wait_for_timeout = 50000, 
        wait_until="domcontentloaded",
        # js_code=[show_more_js]
    )
    
    browser_config = BrowserConfig(
        headless=config.get('headless', True),
        enable_stealth=True,
        # CRITICAL: These args help with VPN/proxy routing
        extra_args=[
            '--disable-blink-features=AutomationControlled',
            '--disable-dev-shm-usage',
        ],
        # Increase viewport for better rendering
        viewport_width=1920,
        viewport_height=1080,
    )
    
    return crawler_run_config, browser_config

async def run_crawler(website_name, config_path='config.json'):
    """Runs the advanced crawler for a given website."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    config = load_config(website_name, config_path)
    if not config:
        return

    crawler_run_config, browser_config = setup_crawler_config(config)
    start_url = config['start_url']
    output_file = config.get('output_file', 'crawled_results.json')
    crawled_page_count = 0

    logging.info(f"Starting crawl for {website_name} at {start_url}")

    try:
        with open(output_file, "w", encoding="utf-8") as f:
            async with AsyncWebCrawler(config=browser_config) as crawler:
                crawl_generator = await crawler.arun(start_url, config=crawler_run_config)
                async for result in crawl_generator:
                    try:
                        detailed_data = {
                            "url": result.url,
                            "depth": result.metadata.get("depth", 0),
                            "score": result.metadata.get("score", 0),
                            "title": result.metadata.get("title", "N/A"),
                            # "raw_html":result.html, 
                            # "markdown":str(result.markdown),
                            "cleaned_html":result.cleaned_html
                        }
                        f.write(json.dumps(detailed_data, ensure_ascii=False) + '\n')
                        crawled_page_count += 1

                        score = result.metadata.get("score", 0)
                        depth = result.metadata.get("depth", 0)
                        logging.info(f"SUCCESS: Depth: {depth} | Score: {score:.2f} | {result.url}")
                    except (httpx.ConnectError, httpx.ReadTimeout) as e:
                        logging.warning(f"SKIPPING: Network error for a page: {e}")
                    except httpx.HTTPStatusError as e:
                        logging.warning(f"SKIPPING: HTTP error {e.response.status_code} for page: {e.request.url}")
                    except Exception as e:
                        logging.error(f"SKIPPING: An unexpected error occurred for a page: {e}")

    except (IOError, PermissionError) as e:
        logging.critical(f"Error writing to output file {output_file}: {e}")
        return
    except Exception as e:
        logging.critical(f"A fatal error occurred during the crawl setup or execution: {e}")
        return

    if crawled_page_count > 0:
        logging.info(f"Crawled {crawled_page_count} high-value pages. Results saved to {output_file}")
    else:
        logging.warning("No pages were successfully crawled.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="A configurable, deep web crawler.")
    parser.add_argument("website", help="The name of the website to crawl (must be a key in the config file).")
    parser.add_argument("--config", default="config.json", help="Path to the configuration file.")
    args = parser.parse_args()

    asyncio.run(run_crawler(args.website, args.config))
    
    # python deep_crawler_v1.py misumi_usa