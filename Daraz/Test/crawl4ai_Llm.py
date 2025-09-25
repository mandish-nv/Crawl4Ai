import asyncio
import os
from crawl4ai import AsyncWebCrawler, LLMConfig

async def extract_products_from_markdown(input_file: str, output_file: str):
    # 1️⃣ Load markdown data
    with open(input_file, "r", encoding="utf-8") as f:
        markdown_data = f.read()

    # 2️⃣ Gemini LLM config
    llm_config = LLMConfig(
        provider="gemini/gemini-2.5-flash-lite",
        api_token=os.getenv("GEMINI_API_TOKEN"),
        temperature=0.2,
    )

    # 3️⃣ Instruction for LLM
    prompt = """
    You are given markdown scraped from Daraz.com.
    Extract product details and return ONLY a JSON array with objects containing:
    - url
    - title
    - photo
    - rating
    - price
    - description
    Ensure valid JSON with no extra text.
    """

    # 4️⃣ Use LLM to process the markdown (not crawling again)
    async with AsyncWebCrawler() as crawler:
        result = await crawler.aprocess_content(
            content=markdown_data,
            llm_config=llm_config,
            extraction_prompt=prompt,
        )

    # 5️⃣ Save JSON output
    if result.success and result.extracted_content:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(result.extracted_content)
        print(f"✅ Products extracted and saved to {output_file}")
    else:
        print("❌ Extraction failed:", result.error_message)


if __name__ == "__main__":
    asyncio.run(extract_products_from_markdown("test.md", "products.json"))
