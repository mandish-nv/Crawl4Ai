import os
import json
from bs4 import BeautifulSoup
import google.generativeai as genai

# 1️⃣ Configure Gemini API
api_token = os.getenv("GEMINI_API_TOKEN")
if not api_token:
    raise ValueError("GEMINI_API_TOKEN environment variable not set.")
genai.configure(api_key=api_token)


def parse_with_bs(html_block: str) -> dict:
    """Extract obvious fields with BeautifulSoup as pre-parser."""
    soup = BeautifulSoup(html_block, "html.parser")

    # Default structure
    data = {
        "url": None,
        "photo": None,
        "title": None,
        "price": None,
        "units_sold": None,
        "rating": None,
        "location": None,
    }

    # Extract fields if available
    a_tag = soup.find("a", href=True)
    if a_tag:
        data["url"] = "https:" + a_tag["href"] if a_tag["href"].startswith("//") else a_tag["href"]

    img_tag = soup.find("img")
    if img_tag and img_tag.get("src"):
        data["photo"] = img_tag["src"]

    title_tag = soup.find("a", title=True)
    if title_tag:
        data["title"] = title_tag["title"]

    price_tag = soup.find("span", class_="ooOxS")
    if price_tag:
        data["price"] = price_tag.get_text(strip=True)

    location_tag = soup.find("span", class_="oa6ri")
    if location_tag:
        data["location"] = location_tag.get_text(strip=True)

    # Units sold and rating are not always explicit → left for Gemini
    return data




# 2️⃣ Load scraped markdown
try:
    with open("scraped_output.md", "r", encoding="utf-8") as f:
        markdown_data = f.read()
except FileNotFoundError:
    print("Error: 'scraped_output.md' file not found. Please run crawler.py first.")
    exit()

# 3️⃣ Split into product blocks (separated by blank lines)
products = [p.strip() for p in markdown_data.strip().split("\n\n") if p.strip()]

# Initialize model + results
model = genai.GenerativeModel("gemini-2.0-flash-lite")
output_data = []


for product_md in products:
    # First, parse with BeautifulSoup
    bs_data = parse_with_bs(product_md)

    # Prompt Gemini only for the missing fields
    prompt = f"""
    Extract the following fields from the markdown content and return JSON only:
    - url
    - photo
    - title
    - price
    - units_sold
    - rating
    - location

    Some fields may already be known:
    {json.dumps(bs_data, indent=2)}

    If a field is not found, set it to null. Do not add extra text.

    Markdown content:
    ```html
    {product_md}
    ```
    """

    try:
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )

        gemini_data = json.loads(response.text)

        # Merge Gemini’s response with BeautifulSoup defaults
        merged = {k: gemini_data.get(k) or bs_data.get(k) for k in bs_data.keys()}

    except Exception as e:
        print(f"⚠️ Failed to process product: {e}")
        merged = bs_data  # fallback

    output_data.append(merged)

# 4️⃣ Save output JSON
with open("products.json", "w", encoding="utf-8") as f:
    json.dump(output_data, f, indent=4, ensure_ascii=False)

print("✅ Extraction complete. Saved to products.json")
