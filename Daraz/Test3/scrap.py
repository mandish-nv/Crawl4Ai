import asyncio
import base64
import os
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator


def process_images(div, base_url):
    """
    Fix image URLs inside a div:
    - Handle lazy-loaded images
    - Replace base64 placeholders with actual URLs if possible
    - Convert relative URLs to absolute
    """
    for img in div.find_all("img"):
        for attr in ["data-src", "data-lazy-src", "data-original"]:
            if img.get(attr):
                img["src"] = img[attr]
                break

        if img.get("src") and img["src"].startswith("//"):
            img["src"] = "https:" + img["src"]
        elif img.get("src") and img["src"].startswith("/"):
            img["src"] = urljoin(base_url, img["src"])

        if img.get("src") and img["src"].startswith("data:image"):
            try:
                header, encoded_data = img["src"].split(",", 1)
                img_data = base64.b64decode(encoded_data)
                os.makedirs("images", exist_ok=True)
                filename = os.path.join("images", f"{hash(encoded_data)}.png")
                with open(filename, "wb") as f:
                    f.write(img_data)
                img["src"] = urljoin(base_url, filename)
            except Exception as e:
                print(f"⚠️ Failed to process base64 image: {e}")


async def scrape_url(semaphore, crawler, url, config):
    async with semaphore:
        try:
            print(f"🔗 Scraping: {url}")
            result = await crawler.arun(url, config=config)

            if result.success:
                html = result.html
                soup = BeautifulSoup(html, "html.parser")
                divs = soup.find_all("div", class_="Ms6aG")

                content = ""
                if divs:
                    for div in divs:
                        process_images(div, url)
                        content += str(div) + "\n\n"
                else:
                    print(f"⚠️ No <div class='Ms6aG'> found in {url}")
                return content

            else:
                print(f"❌ Failed to scrape {url}: {result.error_message}")
                return ""
        except Exception as e:
            print(f"❌ Error scraping {url}: {e}")
            return ""


async def scrape_filtered_urls_throttled(concurrency_limit=5):
    print(f"🚀 Starting throttled scraping with concurrency limit: {concurrency_limit}")

    with open("filtered_urls.txt", "r", encoding="utf-8") as f:
        urls = [line.strip() for line in f if line.strip()]

    if not urls:
        print("❌ No URLs found in filtered_urls.txt")
        return

    config = CrawlerRunConfig(
        markdown_generator=DefaultMarkdownGenerator(),
        delay_before_return_html=8.0,  # Wait for page load
        js_code="""
            const element = document.querySelector('.Ms6aG');
            if (element) { return true; }
            return false;
        """
    )

    scraped_content = ""
    semaphore = asyncio.Semaphore(concurrency_limit)

    async with AsyncWebCrawler() as crawler:
        tasks = [scrape_url(semaphore, crawler, url, config) for url in urls]
        results = await asyncio.gather(*tasks)

        for content in results:
            scraped_content += content

    output_filename = "scraped_output.md"
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(scraped_content)

    print(f"✅ Throttled scraping complete. Saved to {output_filename}")


if __name__ == "__main__":
    # Set concurrency limit to 5 by default
    asyncio.run(scrape_filtered_urls_throttled(concurrency_limit=5))
