import os
import json
import re
from google import genai
from google.genai import types
from dotenv import load_dotenv
import pandas as pd

# ----------------------------------------
# 1️⃣ Load environment and setup Gemini
# ----------------------------------------
load_dotenv()
api_token = os.getenv("GEMINI_API_TOKEN")
if not api_token:
    raise ValueError("GEMINI_API_TOKEN not found. Add GEMINI_API_TOKEN to .env")

client = genai.Client(api_key=api_token)


# ----------------------------------------
# 2️⃣ Main extraction logic
# ----------------------------------------
def extract_html_tables_from_markdown():
    # Load markdown file
    with open("markdown.md", "r", encoding="utf-8") as f:
        html_content = f.read()

    # ----------------------------------------
    # 3️⃣ Extract <table>...</table> sections
    # ----------------------------------------
    tables = re.findall(r"<table.*?>.*?</table>", html_content, re.DOTALL | re.IGNORECASE)
    print(f"🔍 Found {len(tables)} HTML tables in markdown.md")

    if not tables:
        print("No HTML tables found.")
        return

    OUTPUT_FILE = "html_tables_extracted.jsonl"

    for idx, table_html in enumerate(tables, start=1):
        print(f"\n🚀 Processing table {idx}...")

        # ----------------------------------------
        # 4️⃣ Gemini Prompt
        # ----------------------------------------
        prompt = f"""
        You are a data extraction and HTML table understanding expert.

        Below is an HTML table extracted from a technical webpage.
        - Interpret and reconstruct it into structured JSON.
        - Properly handle rowspan, colspan, nested or missing cells.
        - Propagate values downwards/sideways for merged cells where logical.
        - Extract clear header labels.
        - Preserve all cell text content (cleaned of HTML tags).
        - Use `null` for missing or empty cells.

        Output only valid JSON with this schema:
        {{
          "table_index": {idx},
          "headers": ["Header1", "Header2", ...],
          "rows": [
            {{"Header1": "Value1", "Header2": "Value2"}},
            ...
          ]
        }}

        HTML Table:
        {table_html}
        """

        # ----------------------------------------
        # 5️⃣ Send to Gemini
        # ----------------------------------------
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(response_mime_type="application/json"),
            )

            raw_json = response.text.strip()

            try:
                table_data = json.loads(raw_json)
            except Exception as parse_err:
                print(f"⚠️ Table {idx} JSON parse error: {parse_err}")
                with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
                    f.write(json.dumps({"table_index": idx, "raw": raw_json}, ensure_ascii=False) + "\n")
                continue

            # ----------------------------------------
            # 6️⃣ Save JSON and CSV
            # ----------------------------------------
            with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(table_data, ensure_ascii=False) + "\n")

            if "rows" in table_data and table_data["rows"]:
                df = pd.DataFrame(table_data["rows"])
                df.to_csv(f"table_{idx}.csv", index=False, encoding="utf-8")

            print(f"✅ Table {idx} extracted successfully.")

        except Exception as e:
            print(f"❌ Failed to process table {idx}: {e}")


# ----------------------------------------
# 7️⃣ Entry Point
# ----------------------------------------
if __name__ == "__main__":
    extract_html_tables_from_markdown()
