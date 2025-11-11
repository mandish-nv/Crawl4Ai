import asyncio
import csv
import re
from typing import List, Dict, Any, Optional

from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BrowserConfig
from crawl4ai.deep_crawling import BestFirstCrawlingStrategy
from crawl4ai.deep_crawling.scorers import URLScorer

# --- 1. Custom URL Scorer for Prioritization ---
class MisumiUrlScorer(URLScorer):
    """
    Prioritizes URLs that contain the '/detail/' path segment 
    (like your examples 2, 3, and 4) with a high score (1.0).
    Gives a medium score (0.5) to the general category pages.
    """
# Note: The reason string is often dropped when ScorerResult is removed, 
    # but the core logic is the score itself.
    def score(self, url: str, **kwargs) -> float: # Note the return type change to float
        if "/vona2/detail/" in url:
            # Highest score for the specific product detail pages
            return 1.0 
        elif "/vona2/mech_screw/" in url:
            # Medium score for category/listing pages
            return 0.5 
        else:
            # Low score for everything else, to be discarded quickly
            return 0.1

# --- 2. Data Extraction Logic ---
async def extract_data(result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    A simple example of extraction logic. 
    In a real scenario, you would use a JsonCssExtractionStrategy
    or LLM-based extraction within the CrawlerRunConfig.
    For demonstration, we'll extract the URL and its score.
    """
    url = result.get('url', 'N/A')
    
    # You would typically use result.extraction_result if using a strategy,
    # but since we are just deep crawling, we pull from the metadata.
    # The 'score' is from the BestFirst strategy.
    
    # Let's extract the product code (e.g., KED2-6) if present
    hissu_code_match = re.search(r'HissuCode=([^&]+)', url)
    hissu_code = hissu_code_match.group(1) if hissu_code_match else 'N/A'
    
    # A simplified data structure to save
    return {
        'URL': url,
        'URL_Type': result.get('scorer_reason', 'N/A'),
        'Scrape_Score': result.get('score', 'N/A'),
        'HissuCode': hissu_code
    }


# --- 3. The Main Crawling Function ---
async def crawl_misumi(start_url: str, output_csv: str):
    """Executes the Best-First crawl and saves results to CSV."""
    
    print(f"🚀 Starting best-first crawl from: {start_url}")
    
    # 3.1. Configure the Best-First Strategy with our custom scorer
    custom_scorer = MisumiUrlScorer()
    strategy = BestFirstCrawlingStrategy(
        max_depth=3,            # Go up to 3 levels deep
        max_pages=50,           # Stop after crawling 50 pages
        url_scorer=custom_scorer, # Our custom URL scorer
        include_external=False  # Only crawl the starting domain
    )

    # 3.2. Define the Run Configuration
    run_conf = CrawlerRunConfig(
        deep_crawling_strategy=strategy,
        # Set to True to get the raw HTML/text, which you'd normally parse
        generate_markdown=False, 
        # Using BYPASS cache during development to get fresh results
        cache_mode="BYPASS" 
    )

    # 3.3. Initialize the Crawler
    # Using an asynchronous context manager is the best practice
    async with AsyncWebCrawler(config=BrowserConfig(headless=True)) as crawler:
        
        # 3.4. Execute the Deep Crawl
        # The result is a stream/generator of CrawlResult objects
        crawl_stream = crawler.adeeper_run(
            start_urls=[start_url],
            config=run_conf,
            stream_results=True # Get results as they are found
        )

        all_scraped_data = []
        
        # 3.5. Process the results stream
        print("\n⚙️ Processing pages as they are crawled...")
        async for result in crawl_stream:
            # The result from the stream will have extra metadata 
            # like 'score' and 'scorer_reason' from the deep crawling strategy
            
            scraped_item = await extract_data(result.to_dict())
            if scraped_item:
                all_scraped_data.append(scraped_item)
                print(f"  [Scraped] Score: {scraped_item['Scrape_Score']:.2f} | URL: {scraped_item['URL']}")

    # 3.6. Save to CSV
    if all_scraped_data:
        keys = all_scraped_data[0].keys()
        with open(output_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(all_scraped_data)
        
        print(f"\n✅ Crawl complete! Data saved to **{output_csv}** ({len(all_scraped_data)} records).")
    else:
        print("\n❌ Crawl completed, but no data was successfully extracted.")


# --- 4. Execution ---
if __name__ == "__main__":
    
    # Your start URL
    START_URL = "https://us.misumi-ec.com/vona2/mech_screw/M1808000000/"
    OUTPUT_FILE = "misumi_scraped_data.csv"
    
    # It's an async function, so we run it in the event loop
    try:
        asyncio.run(crawl_misumi(START_URL, OUTPUT_FILE))
    except Exception as e:
        print(f"An error occurred during the crawl: {e}")