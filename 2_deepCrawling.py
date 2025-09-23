import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.deep_crawling import BFSDeepCrawlStrategy
from crawl4ai.content_scraping_strategy import LXMLWebScrapingStrategy

async def main():
    # Configure a 2-level deep crawl
    config = CrawlerRunConfig(
        deep_crawl_strategy=BFSDeepCrawlStrategy(
            max_depth=2, 
            include_external=False
        ),
        scraping_strategy=LXMLWebScrapingStrategy(),
        verbose=True
    )

    async with AsyncWebCrawler() as crawler:
        results = await crawler.arun("https://example.com", config=config)

        print(f"Crawled {len(results)} pages in total")

        # Access individual results
        for result in results[:3]:  # Show first 3 results
            print(f"URL: {result.url}")
            print(f"Depth: {result.metadata.get('depth', 0)}")

if __name__ == "__main__":
    asyncio.run(main())


# # BFS
# strategy = BFSDeepCrawlStrategy(
#     max_depth=2,               # Crawl initial page + 2 levels deep
#     include_external=False,    # Stay within the same domain
#     max_pages=50,              # Maximum number of pages to crawl (optional)
#     score_threshold=0.3,       # Minimum score for URLs to be crawled (optional)
# )

# # DFS
# strategy = DFSDeepCrawlStrategy(
#     max_depth=2,               # Crawl initial page + 2 levels deep
#     include_external=False,    # Stay within the same domain
#     max_pages=30,              # Maximum number of pages to crawl (optional)
#     score_threshold=0.5,       # Minimum score for URLs to be crawled (optional)
# )

# # BestFirstCrawlingStrategy (⭐️ - Recommended Deep crawl strategy)
# from crawl4ai.deep_crawling import BestFirstCrawlingStrategy
# from crawl4ai.deep_crawling.scorers import KeywordRelevanceScorer

# # Create a scorer
# scorer = KeywordRelevanceScorer(
#     keywords=["crawl", "example", "async", "configuration"],
#     weight=0.7
# )

# # Configure the strategy
# strategy = BestFirstCrawlingStrategy(
#     max_depth=2,
#     include_external=False,
#     url_scorer=scorer,
#     max_pages=25,              # Maximum number of pages to crawl (optional)
# )