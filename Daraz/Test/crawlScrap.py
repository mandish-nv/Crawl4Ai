import asyncio
import sys
import re
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.deep_crawling import BFSDeepCrawlStrategy
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator



async def scrape_daraz_product(results):
    print("\n--- Crawled URLs containing 'catalog' ---")
    filtered_results = []
    filtered_count = 0
    for result in results:
        if re.search(r"daraz\.com\.np/catalog", result.url):
            print(f"✅ Found: {result.url}")
            filtered_results.append(result)  # ✅ add to filtered_results
            filtered_count += 1
    
    filtered_urls = []
    for res in filtered_results:
        filtered_urls.append(res.url)
        
    # Save URLs to a text file
    output_file = "filtered_urls.txt"
    with open(output_file, "a", encoding="utf-8") as f:
        for url in filtered_urls:
            f.write(url + "\n")

    print(f"✅ Saved {len(filtered_urls)} URLs to {output_file}")
        
    print(f"\n--- Crawl complete. Found {filtered_count} matching page(s). ---")
        
    print("🚀 Starting the scraping process...")
    config = CrawlerRunConfig(
        markdown_generator=DefaultMarkdownGenerator(),
        delay_before_return_html=1.0 
    )
    
    # Use AsyncWebCrawler within an async context manager
    async with AsyncWebCrawler() as crawler:
        # Crawl the specified URL with the configured settings
        result = await crawler.arun_many(
          filtered_urls,
          config=config
        )

        for i, result in enumerate(results, start=1):
            if result:
                if result.markdown is not None:
                    output_filename = "test.md"
                    with open(output_filename, "a", encoding="utf-8") as f:
                        f.write(result.markdown)
                    print(f"✅ Product page scraped successfully. Saved to {output_filename}")
                else:
                    print(f"WARNING: Could not write result for URL: {result.url if hasattr(result, 'url') else 'Unknown URL'}. Content was None.")
            else:
                print("❌ Crawling failed:")
                print(f"URL: {result.url}")
                print(f"Error: {result.error_message}")
                if result.status_code:
                    print(f"Status Code: {result.status_code}")

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

        await scrape_daraz_product(results)


if __name__ == "__main__":
    # Run the main asynchronous function
    asyncio.run(deep_crawl_daraz())
