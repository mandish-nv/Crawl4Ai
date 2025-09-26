import asyncio
import sys
import pickle
import csv
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

async def save_resume_crawl(start_url="https://docs.python.org/3/", state_file="crawl_results.pkl"):
    # Load previously saved results if available
    try:
        with open(state_file, "rb") as f:
            results = pickle.load(f)
        print(f"Loaded {len(results)} previously saved results.")
    except FileNotFoundError:
        results = []
        print("No previous crawl state found. Starting fresh.")

    # Filters
    filter_chain = FilterChain([
        DomainFilter(allowed_domains=["docs.python.org"]),
        URLPatternFilter(patterns=["*tutorial*", "*guide*", "*reference*"]),
        ContentTypeFilter(allowed_types=["text/html"])
    ])

    # Scorer
    keyword_scorer = KeywordRelevanceScorer(
        keywords=["async", "context manager", "coroutine", "tutorial", "example"],
        weight=0.8
    )

    # Crawl configuration
    config = CrawlerRunConfig(
        deep_crawl_strategy=BestFirstCrawlingStrategy(
            max_depth=3,
            include_external=False,
            filter_chain=filter_chain,
            url_scorer=keyword_scorer,
            # concurrency=2  # Reduce concurrency to prevent browser crashes
        ),
        scraping_strategy=LXMLWebScrapingStrategy(),
        stream=True,
        # retries=2,
        verbose=True
    )

    # Start crawling
    async with AsyncWebCrawler() as crawler:
        try:
            stream = await crawler.arun(start_url, config=config)
            async for result in stream:
                results.append(result)
                score = result.metadata.get("score", 0)
                depth = result.metadata.get("depth", 0)
                print(f"Depth: {depth} | Score: {score:.2f} | {result.url}")

                # Periodically save progress
                if len(results) % 5 == 0:
                    with open(state_file, "wb") as f:
                        pickle.dump(results, f)
                    print(f"Saved {len(results)} results to {state_file}")

        except Exception as e:
            print(f"Error during crawl: {e}")
            print("Saving progress before exiting...")
            with open(state_file, "wb") as f:
                pickle.dump(results, f)

    # Save final results
    with open(state_file, "wb") as f:
        pickle.dump(results, f)
    print(f"Final results saved: {len(results)} pages")

    # Export to Markdown
    with open("crawl_results.md", "w", encoding="utf-8") as f:
        for result in results:
            if result.markdown and result.markdown.raw_markdown:
                f.write(f"# {result.url}\n\n")
                f.write(result.markdown.raw_markdown + "\n\n---\n\n")

    # Export to CSV
    with open("crawl_results.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["URL", "Score", "Depth"])
        for result in results:
            writer.writerow([
                result.url,
                result.metadata.get("score", 0),
                result.metadata.get("depth", 0)
            ])

    print("Crawl exported to 'crawl_results.md' and 'crawl_results.csv'")

if __name__ == "__main__":
    asyncio.run(save_resume_crawl())
