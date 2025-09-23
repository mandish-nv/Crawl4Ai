import asyncio
import csv
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.deep_crawling.filters import FilterChain, DomainFilter, URLPatternFilter
from crawl4ai.deep_crawling import BFSDeepCrawlStrategy

async def daraz_catalog_scrape_to_csv():
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
        stream=True,      # stream results
        only_text=False   # keep HTML for markdown extraction
    )

    # 3️⃣ Open CSV file to save results
    with open("daraz_products.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["URL", "Title", "Markdown"])  # CSV header

        # 4️⃣ Start crawling
        async with AsyncWebCrawler() as crawler:
            async for result in await crawler.arun(
                "https://www.daraz.com.np/catalog/?spm=a2a0e.searchlist.cate_6.5.6ca355a3zrHeVR&q=Smartphones&from=hp_categories&src=all_channel",
                config=config
            ):
                if result.success:
                    url = result.url
                    title = result.metadata.get("title") or "No title"
                    
                    # 5️⃣ Extract markdown content
                    markdown_content = ""
                    if result.markdown and result.markdown.fit_markdown:
                        markdown_content = result.markdown.fit_markdown
                    elif result.markdown and result.markdown.raw_markdown:
                        markdown_content = result.markdown.raw_markdown
                    
                    # 6️⃣ Write to CSV
                    writer.writerow([url, title, markdown_content[:500]])  # truncate markdown for preview
                    print(f"Saved: {title} | {url}")

    print("\n✅ All product details saved to daraz_products.csv")

if __name__ == "__main__":
    asyncio.run(daraz_catalog_scrape_to_csv())
