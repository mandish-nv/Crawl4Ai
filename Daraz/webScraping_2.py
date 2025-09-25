import asyncio
import re
from urllib.parse import urljoin, urlparse
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.deep_crawling import BFSDeepCrawlStrategy
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

async def crawl_catalogue_and_products(catalogue_url: str, output_file: str, max_products: int = 10):
    """
    Crawls a catalogue page to find product links, then crawls each product
    page and saves the combined output as a single Markdown file.

    Args:
        catalogue_url: The URL of the catalogue/category page.
        output_file: The name of the file to save the markdown content to.
        max_products: The maximum number of products to scrape.
    """
    
    # This configuration is for crawling each individual product page.
    # We only want the content from that page, so max_depth is 0.
    product_crawl_config = CrawlerRunConfig(
        deep_crawl_strategy=BFSDeepCrawlStrategy(max_depth=0),
        markdown_generator=DefaultMarkdownGenerator()
    )

    # This configuration is for the initial crawl of the catalogue page.
    # We just need to find the links on this page, so a depth of 1 is sufficient.
    catalogue_crawl_config = CrawlerRunConfig(
        deep_crawl_strategy=BFSDeepCrawlStrategy(max_depth=1)
    )

    async with AsyncWebCrawler() as crawler:
        # 1️⃣ Crawl the main catalogue page to find all product links
        print(f"🔍 Starting crawl on catalogue page: {catalogue_url}")
        catalogue_results = await crawler.arun(catalogue_url, config=catalogue_crawl_config)

        # The arun method returns a list, so we take the first result for our single URL
        if not catalogue_results:
            print("❌ Crawl returned no results.")
            return
        catalogue_result = catalogue_results[0]

        if not catalogue_result.success:
            print(f"❌ Failed to crawl catalogue page: {catalogue_result.error_message}")
            return

        # 2️⃣ Extract unique product links using a regular expression
        # The `catalogue_result.links` attribute contains all the href values
        # from the <a> tags found on the page, which is what we need.
        product_links = set()
        
        # This pattern is specific to Daraz's URL structure for products,
        # ensuring we only select links pointing to a product page.
        product_pattern = re.compile(r'/products/.*-i\d+.*\.html')
        base_url = f"{urlparse(catalogue_url).scheme}://{urlparse(catalogue_url).netloc}"

        print("ℹ️ Filtering all found links to identify product pages...")
        for link in catalogue_result.links:
            # The link could be a full URL, a relative path, or protocol-relative (starting with //).
            # We apply the regex to see if it matches the product URL format you pointed out.
            if product_pattern.search(link):
                # urljoin correctly handles all cases (relative, absolute, protocol-relative)
                # to create a full, valid URL for the next step of scraping.
                absolute_link = urljoin(base_url, link)
                product_links.add(absolute_link)

        if not product_links:
            print("❌ No product links found on the catalogue page. Please check the URL and the page's HTML structure.")
            return
            
        product_links = list(product_links)[:max_products]
        print(f"✅ Found {len(product_links)} unique product links. Starting individual scrapes...")

        # 3️⃣ Define a helper function to crawl a single product URL
        async def crawl_product(url: str):
            """Crawls a single product and returns its markdown content."""
            print(f"  -> Scraping product: {url}")
            results = await crawler.arun(url, config=product_crawl_config)
            
            # arun returns a list, so we take the first result
            if not results:
                print(f"  ❌ Failed: {url} | Reason: No result returned from crawl.")
                return None
            result = results[0]

            if result.success and result.markdown:
                print(f"  ✅ Success: {url}")
                return result.markdown.raw_markdown
            else:
                print(f"  ❌ Failed: {url} | Reason: {result.error_message}")
                return None

        # 4️⃣ Create and run concurrent tasks for all product links
        tasks = [crawl_product(link) for link in product_links]
        markdown_results = await asyncio.gather(*tasks)

        # 5️⃣ Filter out any failed crawls and combine the results
        successful_markdowns = [md for md in markdown_results if md]
        
        if not successful_markdowns:
            print("❌ All product scrapes failed. No output file will be created.")
            return
            
        final_markdown = "\n\n---\n\n".join(successful_markdowns)

        # 6️⃣ Write the combined markdown to the output file
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(final_markdown)
        
        print(f"\n🎉 Successfully scraped {len(successful_markdowns)} products and saved content to {output_file}")


if __name__ == "__main__":
    # --- CONFIGURATION ---
    # Change this URL to the catalogue/category page you want to scrape
    target_catalogue_url = "https://www.daraz.com.np/catalog/?from=hp_categories&page=1&q=Smartphones&service=all_channel&spm=a2a0e.searchlist.cate_6.5.6ca355a3zrHeVR&src=all_channel"
    
    # The name of the final output file
    output_filename = "scraped_products.md"
    
    # Set a limit for the number of products to avoid excessively long runs
    max_products_to_scrape = 5 
    
    # --- RUN THE SCRIPT ---
    asyncio.run(crawl_catalogue_and_products(
        target_catalogue_url, 
        output_filename, 
        max_products=max_products_to_scrape
    ))


