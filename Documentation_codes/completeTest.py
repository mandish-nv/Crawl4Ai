import asyncio
import json
import os

from crawl4ai import (
    AsyncWebCrawler,
    BrowserConfig,
    CrawlerRunConfig,
    CacheMode,
    LLMConfig,
    LLMContentFilter,
    DefaultMarkdownGenerator,
    JsonCssExtractionStrategy
)

async def main():
    # 1) Browser configuration
    browser_conf = BrowserConfig(
        headless=True,
        viewport_width=1280,
        viewport_height=800,
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/120.0.0.0 Safari/537.36"
    )

    # 2) Define extraction schema (basic CSS selectors)
    schema = {
    "name": "Articles",
    "baseSelector": "article.post",
    "fields": [
        {"name": "title", "selector": "h2.post-title a", "type": "text"},
        {"name": "link", "selector": "h2.post-title a", "type": "attribute", "attribute": "href"}
    ]
}

    extraction = JsonCssExtractionStrategy(schema)

    # 3) LLM config (example with Gemini – replace api_token)
    gemini_conf = LLMConfig(
        provider="gemini/gemini-2.5-flash-lite",
        api_token=os.getenv("GEMINI_API_TOKEN")
    )

    # 4) LLM content filter
    filter = LLMContentFilter(
        llm_config=gemini_conf,
        instruction="""
        Summarize the educational or technical content from this page.
        - Keep only useful concepts and explanations
        - Ignore navigation/ads/sidebars
        Format result as clean markdown with sections.
        """,
        chunk_token_threshold=500,
        verbose=True
    )

    # 5) Markdown generator using the filter
    md_generator = DefaultMarkdownGenerator(
        content_filter=filter,
        options={"ignore_links": True}
    )

    # 6) Crawler run configuration
    run_conf = CrawlerRunConfig(
        markdown_generator=md_generator,
        extraction_strategy=extraction,
        cache_mode=CacheMode.BYPASS,   # Always fetch fresh
    )

    # 7) Run crawler
    async with AsyncWebCrawler(config=browser_conf) as crawler:
        result = await crawler.arun(
            url="https://blog.scrapinghub.com/page/1",
            config=run_conf
        )

        if result.success:
            print("\n--- Extracted JSON ---")
            print(result.extracted_content)

            print("\n--- LLM Processed Markdown ---")
            print(result.markdown[:1000])  # first 1000 chars
        else:
            print("Error:", result.error_message)


if __name__ == "__main__":
    asyncio.run(main())
