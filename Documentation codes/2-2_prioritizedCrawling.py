import asyncio
import sys
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.deep_crawling.scorers import KeywordRelevanceScorer
from crawl4ai.deep_crawling import BestFirstCrawlingStrategy

async def main():
    # Keyword relevance scorer
    keyword_scorer = KeywordRelevanceScorer(
        keywords=["crawl", "example", "async", "configuration"],
        weight=0.7
    )

    config = CrawlerRunConfig(
        deep_crawl_strategy=BestFirstCrawlingStrategy(
            max_depth=2,
            url_scorer=keyword_scorer
        ),
        stream=True  # BestFirst works best with streaming
    )

    async with AsyncWebCrawler() as crawler:
        # First await arun() to get the async iterator
        stream = await crawler.arun("https://example.com", config=config)

        # Now consume the stream
        async for result in stream:
            score = result.metadata.get("score", 0)
            print(f"Score: {score:.2f} | {result.url}")

if __name__ == "__main__":
    asyncio.run(main())
