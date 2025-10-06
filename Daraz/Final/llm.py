import os
import json
from bs4 import BeautifulSoup
from google import genai
from google.genai import types  # for config types etc
from markdownify import markdownify as md
from typing import List, Optional
from dotenv import load_dotenv
# Load environment variables from .env file
load_dotenv() 
# 1️⃣ Configure Gemini API
api_token = os.getenv("GEMINI_API_TOKEN")
if not api_token:
    raise ValueError("GEMINI_API_TOKEN environment variable not set.")
client = genai.Client(api_key=api_token)


def llm_process():
    # 2️⃣ Load scraped markdown
    try:
        with open("markdown.md", "r", encoding="utf-8") as f:
            markdown_data = f.read()
    except FileNotFoundError:
        print("Error: 'markdown.md' file not found. Please run crawler.py first.")
        exit()

    # 3️⃣ Split into product blocks (separated by blank lines)
    products = [p.strip() for p in markdown_data.strip().split("\n\n") if p.strip()]

    for product in products:
      print(product)

    OUTPUT_FILENAME = "products_batch.jsonl" 
    PRODUCT_DELIMITER = "\n\n---PRODUCT-SEPARATOR---\n\n"

    # Process in chunks of 1000
    for start in range(0, len(products), 1000):
        chunk = products[start:start+1000]
        all_product_markdowns = PRODUCT_DELIMITER.join([md(p) for p in chunk])

        print(f"Starting batch extraction for products {start+1}–{start+len(chunk)}. Appending to {OUTPUT_FILENAME}...")

        # The schema is now defined directly in the prompt (no Pydantic)
        prompt = f"""
        You are an expert product data extraction system.
        Each product record is separated by the text '---PRODUCT-SEPARATOR---'.

        For EACH record, extract the following fields if available:
        - url: URL of the product page
        - photo: URL of the main product photo
        - title: name or title of the product
        - price: product price including currency (as string)
        - units_sold: number of units sold (integer, if found)
        - rating: average customer rating (float, if found)
        - location: seller or shipping location

        Return ONLY a single valid JSON array of objects, like:
        [
          {{
            "url": "...",
            "photo": "...",
            "title": "...",
            "price": "...",
            "units_sold": 100,
            "rating": 4.5,
            "location": "Kathmandu"
          }},
          ...
        ]

        If a field is not found, set it to null. 
        Do not include any explanations, markdown, or extra text.

        Raw Product Records:
        {all_product_markdowns}
        """

        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash-lite",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )

            # Directly parse JSON
            extracted_products = []
            try:
                extracted_products = json.loads(response.text)
            except Exception as parse_err:
                print("⚠️ Failed to parse JSON, writing raw text instead.")
                with open(OUTPUT_FILENAME, "a", encoding="utf-8") as f:
                    f.write(response.text.strip() + "\n")
                continue

            # Append results
            with open(OUTPUT_FILENAME, "a", encoding="utf-8") as f:
                for product_data in extracted_products:
                    f.write(json.dumps(product_data, ensure_ascii=False) + "\n")

            print(f"✅ Batch {start//1000+1} complete. Wrote {len(extracted_products)} products.")

        except Exception as e:
            print(f"❌ Batch {start//1000+1} failed. Error: {e}")
            if "response" in locals() and response and hasattr(response, "prompt_feedback"):
                print(f"   Prompt Feedback: {response.prompt_feedback}")

# time -> 20sec for 40 products
if __name__=="__main__":
    llm_process()