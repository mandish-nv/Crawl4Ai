import asyncio
import sys
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator


async def scrape_daraz_product():
    print("🚀 Starting the scraping process...")
    config = CrawlerRunConfig(
        markdown_generator=DefaultMarkdownGenerator(),
        delay_before_return_html=1.0 
    )
    
    # Use AsyncWebCrawler within an async context manager
    async with AsyncWebCrawler() as crawler:
        # Crawl the specified URL with the configured settings
        result = await crawler.arun(
            # "https://www.daraz.com.np/products/cmf-phone-1-8-128gb-667-120-hz-super-amoled-display-mediatek-dimensity-7300-5g-processor-5000-mah-33w-fast-charging-i138665388.html?spm=a2a0e.searchlist.list.1.4a79a389hSm1EE",
            "https://www.daraz.com.np/catalog/?spm=a2a0e.searchlist.cate_6.5.6ca355a3zrHeVR&q=Smartphones&from=hp_categories&src=all_channel",
            config=config
        )

        if result.success:
            output_filename = "test.md"
            with open(output_filename, "w", encoding="utf-8") as f:
                f.write(result.markdown)
            print(f"✅ Product page scraped successfully. Saved to {output_filename}")
        else:
            print("❌ Crawling failed:")
            print(f"URL: {result.url}")
            print(f"Error: {result.error_message}")
            if result.status_code:
                print(f"Status Code: {result.status_code}")


if __name__ == "__main__":
    asyncio.run(scrape_daraz_product())
