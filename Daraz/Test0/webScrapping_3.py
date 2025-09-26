import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.deep_crawling.filters import FilterChain, DomainFilter, URLPatternFilter
from crawl4ai.deep_crawling import BFSDeepCrawlStrategy

async def daraz_catalog_scrape_to_md():
    """
    Crawls Daraz product pages and saves the entire content of each page
    to a single markdown file.
    """
    # 1️⃣ Define filters to crawl only product pages
    filters = FilterChain([
        DomainFilter(allowed_domains=["www.daraz.com.np"]),
        URLPatternFilter(patterns=["*/products/*"])  # typical product page URL pattern
    ])

    # 2️⃣ Setup BFS deep crawl strategy
    config = CrawlerRunConfig(
        deep_crawl_strategy=BFSDeepCrawlStrategy(
            max_depth=3,
            filter_chain=filters,
            include_external=False
        ),
        stream=True,
        only_text=True  # Change to True to get the markdown content directly
    )

    # 3️⃣ Open markdown file to save results
    output_filename = "daraz_products.md"
    with open(output_filename, "w", encoding="utf-8") as f:
        async with AsyncWebCrawler() as crawler:
            async for result in await crawler.arun(
                "https://www.daraz.com.np/catalog/?spm=a2a0e.searchlist.cate_6.5.6ca355a3zrHeVR&q=Smartphones&from=hp_categories&src=all_channel",
                config=config
            ):
                if result.success:
                    # Write the entire markdown content of the page
                    f.write(f"--- URL: {result.url} ---\n\n")
                    f.write(result.markdown)
                    f.write("\n\n")
                    print(f"✅ Saved page content for: {result.url}")

    print(f"\n✅ All product details saved to {output_filename}")

if __name__ == "__main__":
    asyncio.run(daraz_catalog_scrape_to_md())
