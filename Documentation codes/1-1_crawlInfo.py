import asyncio
import sys

from crawl4ai import AsyncWebCrawler, CrawlResult

async def handle_result(result: CrawlResult):
    if not result.success:
        print("Crawl error:", result.error_message)
        return

    # Basic info
    print("Crawled URL:", result.url)
    print("Status code:", result.status_code)

    # HTML
    print("Original HTML size:", len(result.html))
    print("Cleaned HTML size:", len(result.cleaned_html or ""))

    # Markdown output
    if result.markdown:
        print("Raw Markdown:", result.markdown.raw_markdown[:300])
        print("Citations Markdown:", result.markdown.markdown_with_citations[:300])
        if result.markdown.fit_markdown:
            print("Fit Markdown:", result.markdown.fit_markdown[:200])

    # Media & Links
    if result.media and "images" in result.media:
        print("Image count:", len(result.media["images"]))
    if result.links and "internal" in result.links:
        print("Internal link count:", len(result.links["internal"]))

    # Extraction strategy result
    if result.extracted_content:
        print("Structured data:", result.extracted_content)

    # Screenshot/PDF/MHTML
    if result.screenshot:
        print("Screenshot length:", len(result.screenshot))
    if result.pdf:
        print("PDF bytes length:", len(result.pdf))
    if result.mhtml:
        print("MHTML length:", len(result.mhtml))

    # Network and console capturing
    if result.network_requests:
        print(f"Network requests captured: {len(result.network_requests)}")
        req_types = {}
        for req in result.network_requests:
            if "resource_type" in req:
                req_types[req["resource_type"]] = req_types.get(req["resource_type"], 0) + 1
        print(f"Resource types: {req_types}")

    if result.console_messages:
        print(f"Console messages captured: {len(result.console_messages)}")
        msg_types = {}
        for msg in result.console_messages:
            msg_types[msg.get("type", "unknown")] = msg_types.get(msg.get("type", "unknown"), 0) + 1
        print(f"Message types: {msg_types}")


async def main():
    async with AsyncWebCrawler() as crawler:
        # result = await crawler.arun(url="https://www.example.com")
        result = await crawler.arun(url="https://www.daraz.com.np/catalog/?spm=a2a0e.searchlist.cate_6.5.6ca355a3zrHeVR&q=Smartphones&from=hp_categories&src=all_channel")
        await handle_result(result)


if __name__ == "__main__":
    asyncio.run(main())

