import os
import json
import re
import html
from bs4 import BeautifulSoup
from google import genai
from google.genai import types
from dotenv import load_dotenv
import pandas as pd

# ============================================================
# 1️⃣ Setup
# ============================================================
load_dotenv()
api_token = os.getenv("GEMINI_API_TOKEN")
if not api_token:
    raise ValueError("GEMINI_API_TOKEN not found. Add GEMINI_API_TOKEN to .env")

client = genai.Client(api_key=api_token)

# ============================================================
# 2️⃣ Utilities
# ============================================================
def clean_html(html_text: str) -> str:
    """Decode and remove irrelevant tags like script/style."""
    cleaned = html.unescape(html_text)
    soup = BeautifulSoup(cleaned, "html.parser")
    for tag in soup(["script", "style", "svg", "noscript"]):
        tag.decompose()
    return str(soup)

def extract_tables(html_content: str):
    """Extract all <table>...</table> blocks including nested."""
    soup = BeautifulSoup(html_content, "html.parser")
    return [str(t) for t in soup.find_all("table")]

def estimate_tokens(text: str) -> int:
    """
    Rough token estimate for Gemini (1 token ≈ 4 chars typical).
    Safe upper bound.
    """
    return len(text) // 4

# ============================================================
# 3️⃣ Main Extraction
# ============================================================
def extract_html_tables_from_markdown():
    # Load scraped file
    with open("markdown.md", "r", encoding="utf-8") as f:
        content = f.read()

    cleaned = clean_html(content)
    tables = extract_tables(cleaned)
    print(f"🔍 Found {len(tables)} tables (including nested).")

    if not tables:
        print("No tables found.")
        return

    OUTPUT_JSONL = "tables_extracted_safe.jsonl"
    MAX_TOKENS = 100000  # Keep below Gemini 2.5 Flash limit (~128k)

    batch, batch_tokens = [], 0
    batch_index, table_index = 0, 1

    for table_html in tables:
        tokens = estimate_tokens(table_html)
        if tokens > MAX_TOKENS * 0.8:
            print(f"⚠️ Table {table_index} too large ({tokens} tokens). Skipping.")
            table_index += 1
            continue

        # Add to batch if safe
        if batch_tokens + tokens < MAX_TOKENS * 0.8:
            batch.append(table_html)
            batch_tokens += tokens
        else:
            # Process current batch before overflow
            process_batch(batch, batch_index, table_index, OUTPUT_JSONL)
            batch, batch_tokens = [table_html], tokens
            batch_index += 1
        table_index += 1

    # Process last batch
    if batch:
        process_batch(batch, batch_index, table_index, OUTPUT_JSONL)

# ============================================================
# 4️⃣ Gemini Batch Processing
# ============================================================
def process_batch(batch, batch_index, start_index, output_file):
    joined_tables = "\n\n---TABLE-SEPARATOR---\n\n".join(batch)

    prompt = f"""
    You are a professional HTML table parser.
    Below are multiple HTML <table> elements separated by '---TABLE-SEPARATOR---'.

    ✅ Instructions:
    - Parse each table accurately into structured JSON.
    - Resolve rowspan and colspan by repeating merged values.
    - Handle nested tables (expand inline logically).
    - Replace missing or blank cells with null.
    - Include header names if possible.
    - Output a JSON array of tables, each with:
      {{
        "table_index": <integer>,
        "headers": ["Header1", "Header2", ...],
        "rows": [{{"Header1": "Value1", "Header2": "Value2"}}, ...]
      }}

    Do not include any text or explanation outside the JSON.

    Tables:
    {joined_tables}
    """

    print(f"\n🚀 Sending batch {batch_index+1} with {len(batch)} tables to Gemini...")

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json"),
        )
        raw_json = response.text.strip()

        try:
            parsed = json.loads(raw_json)
        except Exception as e:
            print(f"⚠️ Batch {batch_index+1} JSON parse failed: {e}")
            with open(output_file, "a", encoding="utf-8") as f:
                f.write(json.dumps({"batch": batch_index+1, "raw": raw_json}, ensure_ascii=False) + "\n")
            return

        # Write to JSONL and CSV
        with open(output_file, "a", encoding="utf-8") as f:
            for t in parsed:
                f.write(json.dumps(t, ensure_ascii=False) + "\n")
                if "rows" in t and isinstance(t["rows"], list) and t["rows"]:
                    df = pd.DataFrame(t["rows"])
                    csv_name = f"table_{t.get('table_index', start_index)}.csv"
                    df.to_csv(csv_name, index=False, encoding="utf-8")
                    print(f"✅ Saved {csv_name} ({len(df)} rows)")

    except Exception as e:
        print(f"❌ Gemini call failed for batch {batch_index+1}: {e}")

# ============================================================
# 5️⃣ Run
# ============================================================
if __name__ == "__main__":
    extract_html_tables_from_markdown()
