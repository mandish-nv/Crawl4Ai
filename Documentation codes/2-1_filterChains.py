import asyncio
import sys
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.deep_crawling import BFSDeepCrawlStrategy
from crawl4ai.deep_crawling.filters import (
    FilterChain,
    URLPatternFilter,
    DomainFilter,
    ContentTypeFilter,
)

# Define filters
filter_chain = FilterChain([
    URLPatternFilter(patterns=["*guide*", "*tutorial*"]),
    DomainFilter(
        allowed_domains=["docs.python.org"],   # <-- use a real site
        blocked_domains=["old.docs.python.org"],
    ),
    ContentTypeFilter(allowed_types=["text/html"]),
])

# Configure deep crawl with BFS
config = CrawlerRunConfig(
    deep_crawl_strategy=BFSDeepCrawlStrategy(
        max_depth=2,
        filter_chain=filter_chain,
    )
)


async def main():
    async with AsyncWebCrawler() as crawler:
        results = await crawler.arun(
            url="https://docs.python.org/3/",  # <-- replace with target
            config=config,
        )

        # `results` is a list of CrawlResult
        for i, result in enumerate(results, start=1):
            print(f"\n=== Page {i}: {result.url} ===")
            if result.success:
                print("Status:", result.status_code)
                print("Extracted text sample:", (result.markdown.raw_markdown[:200] if result.markdown else "No markdown"))
            else:
                print("Error:", result.error_message)


if __name__ == "__main__":
    asyncio.run(main())


# URLPatternFilter: Matches URL patterns using wildcard syntax
# DomainFilter: Controls which domains to include or exclude
# ContentTypeFilter: Filters based on HTTP Content-Type
# ContentRelevanceFilter: Uses similarity to a text query
# SEOFilter: Evaluates SEO elements (meta tags, headers, etc.)