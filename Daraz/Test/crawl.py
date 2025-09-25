import asyncio
import sys
import re
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.deep_crawling import BFSDeepCrawlStrategy
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator


async def deep_crawl_daraz():
    """
    Performs a deep crawl on a Daraz catalog page, exploring multiple
    linked pages and printing the URLs of each page successfully crawled.
    """
    print("🚀 Starting the deep crawling process...")

    # Define a deep crawling strategy to explore multiple pages.
    # BFSDeepCrawlStrategy crawls all links at one depth before moving to the next.
    # We set a limit of 10 pages to prevent an overly long crawl.
    deep_crawl_strategy = BFSDeepCrawlStrategy(
        max_pages=100,
        max_depth=2,
        # Set a low word count threshold for pages to be considered relevant.
        # word_count_threshold=100,
        # Ensure we stay within the daraz.com.np domain.
        include_external=False
    )

    # Configure the crawler with the deep crawl strategy.
    # We are not generating markdown in this version, as the goal is to list URLs.
    config = CrawlerRunConfig(
        deep_crawl_strategy=deep_crawl_strategy,
        verbose=True
    )
    
    # Use AsyncWebCrawler within an async context manager
    async with AsyncWebCrawler() as crawler:
        # Start the deep crawl from the specified URL.
        # arun_many() is used for multi-page crawling and returns a list of results.
        results = await crawler.arun(
                "https://www.daraz.com.np/catalog/?spm=a2a0e.searchlist.cate_6.5.6ca355a3zrHeVR&q=Smartphones&from=hp_categories&src=all_channel",
            config=config
        )

        print("\n--- Crawled URLs containing 'catalog' ---")
        filtered_count = 0
        for result in results:
            if re.search(r"daraz\.com\.np/catalog", result.url):
                print(f"✅ Found: {result.url}")
                filtered_count += 1
        
        print(f"\n--- Crawl complete. Found {filtered_count} matching page(s). ---")


if __name__ == "__main__":
    # Run the main asynchronous function
    asyncio.run(deep_crawl_daraz())
