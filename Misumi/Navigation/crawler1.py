import asyncio
import csv
import sys
import yaml
from bs4 import BeautifulSoup
from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai.deep_crawling import BFSDeepCrawlStrategy
from typing import Dict, Any, List

# --- Helper function to load configuration ---
def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration from a YAML file."""
    try:
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
        return config
    except FileNotFoundError:
        print(f"❌ Error: Config file not found at '{config_path}'")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"❌ Error parsing YAML configuration: {e}")
        sys.exit(1)

# --- Helper function to save data ---
def save_to_csv(data: List[Dict[str, str]], filename: str):
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


async def crawler1(config_path: str):
    """
    Crawl a target URL using configurations loaded from a YAML file.
    """
    print(f"⏳ Loading configuration from: {config_path}")
    config_data = load_config(config_path)
    
    # --- Configuration mapping ---
    
    # 1. Map Browser Configuration
    browser_config = BrowserConfig(**config_data["browser_config"])

    # 2. Map Deep Crawl Strategy Configuration
    deep_crawl_strategy = BFSDeepCrawlStrategy(
        **config_data["deep_crawl_strategy"]
    )

    # 3. Map Crawler Run Configuration (and inject the strategy)
    run_config_data = config_data["run_config"].copy() # Use a copy to avoid mutating the config dict
    
    # Convert string cache_mode to enum
    try:
        run_config_data["cache_mode"] = CacheMode[run_config_data["cache_mode"].upper()]
    except KeyError:
        print(f"❌ Invalid cache_mode: {run_config_data['cache_mode']}. Must be one of {list(CacheMode.__members__.keys())}")
        return

    run_config = CrawlerRunConfig(
        deep_crawl_strategy=deep_crawl_strategy,
        **run_config_data
    )
    
    # --- Start crawling ---
    url = config_data["url"]
    print(f"🚀 Starting crawl for URL: {url}")
    
    async with AsyncWebCrawler(config=browser_config) as crawler:
        results = await crawler.arun(
            url=url,
            config=run_config,
            deep_crawl=config_data["deep_crawl"]
        )

    # --- Extract product links ---
    all_links = []
    target_css_selector = config_data["target_css_selector"]
    base_url_for_relative = config_data["base_url_for_relative"]
    
    print(f"🎯 Extracting links using selector: {target_css_selector}")
    
    for result in results:
        if not result.html:
            continue
            
        soup = BeautifulSoup(result.html, "html.parser")

        for a in soup.select(target_css_selector):
            href = a.get("href")
            text = a.get_text(strip=True)
            if href and text:
                # Resolve relative URLs
                if href.startswith("/"):
                    href = base_url_for_relative + href
                all_links.append({"title": text, "url": href})

    # --- Save results ---
    if all_links:
        save_to_csv(all_links, config_data["output_filename"])
    else:
        print("No product links found.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        # User needs to provide exactly one argument: the path to the config file
        print("Usage: python crawler1.py <path_to_config.yaml>")
        sys.exit(1)
        
    # Get the config file path from the first command-line argument (sys.argv[1])
    config_file_path = sys.argv[1]
    
    # Run the main crawler function with the provided config path
    asyncio.run(crawler1(config_file_path))