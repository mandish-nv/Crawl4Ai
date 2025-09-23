import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.content_scraping_strategy import LXMLWebScrapingStrategy
from crawl4ai.deep_crawling import BestFirstCrawlingStrategy
from crawl4ai.deep_crawling.filters import (
    FilterChain,
    DomainFilter,
    URLPatternFilter,
    ContentTypeFilter
)
from crawl4ai.deep_crawling.scorers import KeywordRelevanceScorer

async def run_advanced_crawler():
    # Filter chain
    filter_chain = FilterChain([
        DomainFilter(
            allowed_domains=["docs.python.org"],  # only domain, no https://
            blocked_domains=[]
        ),
        URLPatternFilter(patterns=["*guide*", "*tutorial*", "*blog*", "*reference*"]),
        ContentTypeFilter(allowed_types=["text/html"])
    ])

    # Keyword relevance scorer
    keyword_scorer = KeywordRelevanceScorer(
        keywords=["tutorial", "library", "module", "examples", "reference"],
        weight=0.7,
    )

    # Crawler config
    config = CrawlerRunConfig(
        deep_crawl_strategy=BestFirstCrawlingStrategy(
            max_depth=5,
            include_external=False,
            filter_chain=filter_chain,
            url_scorer=keyword_scorer
        ),
        scraping_strategy=LXMLWebScrapingStrategy(),
        stream=True,
        verbose=True
    )

    # Execute crawl
    results = []
    async with AsyncWebCrawler() as crawler:
        # First await the coroutine to get the async iterator
        stream = await crawler.arun("https://docs.python.org/3/", config=config)
        async for result in stream:
            results.append(result)
            score = result.metadata.get("score", 0)
            depth = result.metadata.get("depth", 0)
            print(f"Depth: {depth} | Score: {score:.2f} | {result.url}")

    # Analyze results
    print(f"Crawled {len(results)} high-value pages")
    if results:
        avg_score = sum(r.metadata.get("score", 0) for r in results) / len(results)
        print(f"Average score: {avg_score:.2f}")

        # Group by depth
        depth_counts = {}
        for result in results:
            depth = result.metadata.get("depth", 0)
            depth_counts[depth] = depth_counts.get(depth, 0) + 1

        print("Pages crawled by depth:")
        for depth, count in sorted(depth_counts.items()):
            print(f"  Depth {depth}: {count} pages")

if __name__ == "__main__":
    asyncio.run(run_advanced_crawler())


# Average score -> [0-1]