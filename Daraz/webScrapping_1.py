import asyncio
import csv
import json
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
        stream=True,
        only_text=False  # keep HTML for parsing
    )

    # 3️⃣ Open CSV file to save results
    with open("daraz_products_1.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["URL", "Title", "Photo", "Rating", "Price", "Description"])

        async with AsyncWebCrawler() as crawler:
            async for result in await crawler.arun(
                "https://www.daraz.com.np/catalog/?spm=a2a0e.searchlist.cate_6.5.6ca355a3zrHeVR&q=Smartphones&from=hp_categories&src=all_channel",
                config=config
            ):
                if result.success:
                    url = result.url
                    title = result.metadata.get("title") or "No title"

                    # Default values
                    photo = rating = price = description = "N/A"
                    await asyncio.sleep(2)

                    # Attempt to extract JSON-LD data from HTML
                    if result.html:
                        try:
                            start = result.html.find('<script type="application/ld+json">')
                            if start != -1:
                                end = result.html.find('</script>', start)
                                json_ld_text = result.html[start+len('<script type="application/ld+json">'):end].strip()
                                data = json.loads(json_ld_text)

                                # Some fields may be nested
                                photo = data.get("image", photo)
                                price = data.get("offers", {}).get("price", price)
                                rating = data.get("aggregateRating", {}).get("ratingValue", rating)
                                description = data.get("description", description)
                        except Exception:
                            pass

                    # Write row
                    writer.writerow([url, title, photo, rating, price, description])
                    print(f"Saved: {title} | {url}")

    print("\n✅ All product details saved to daraz_products.csv")

if __name__ == "__main__":
    asyncio.run(daraz_catalog_scrape_to_csv())
