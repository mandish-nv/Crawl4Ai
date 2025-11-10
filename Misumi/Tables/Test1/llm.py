import os
import json
import re
from google import genai
from google.genai import types
from dotenv import load_dotenv
import pandas as pd
from io import StringIO

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
        # 4️⃣ Full Gemini Prompt (Comprehensive)
        # ----------------------------------------
        prompt = f"""
        You are a data extraction and HTML table understanding expert.

        Below is an HTML <table> and a reference image of the same table.

        🧩 Goal:
        Convert the provided table (and its visual layout from the image) into a clean,
        normalized **CSV** representation that reflects the table's *visual appearance and structure*,
        not just the raw HTML.

        ⚙️ Input:
        - HTML Table: may include inline CSS, nested tags, missing or borderless cells.
        - Reference Image: shows the true rendered layout of the table.

        🧠 Your Tasks:
        1. Parse and understand the logical structure of the table.
        2. Handle merged cells correctly:
            - If a cell uses rowspan or colspan, replicate its value in all spanned cells.
            - If cells appear visually merged due to CSS (e.g., border-top:none, border-left:none), 
              propagate the same value into all merged regions.
        3. Use the visual layout in the image to confirm merges and grouping.
        4. Preserve all numerical ranges, symbols (±, ≤, ≧, −), and special formatting characters.
        5. If a cell contains multiple lines (e.g., <br> tags), join them using a semicolon (;).
        6. Identify header cells (<th> or visually bold/centered cells):
            - If there are multi-level headers, concatenate using “ / ” (e.g., “Category / Size / Value”).
            - Ensure header hierarchy appears correctly as top CSV rows.

        ⚖️ CSV Output Rules:
        - Output **only pure CSV text** — no markdown, JSON, or explanations.
        - Separate columns with commas.
        - Each logical table row must be one line.
        - Preserve alignment and merged values as seen in the image.
        - Ensure rectangular structure (same column count for all rows).
        - Do NOT include any quotes, code fences, or commentary.

        🧾 Example Output:
        Column A, Column B, Column C
        Value 1, Value 2, Value 3
        A1, B1, C1
        A2, B2, C2

        ✅ Deliverable:
        Return **only the final CSV text**.

        --- HTML TABLE START ---
        {table_html}
        --- HTML TABLE END ---
        """

        # ----------------------------------------
        # 5️⃣ Attach reference image
        # ----------------------------------------
        image_path = "test.png"
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file '{image_path}' not found")

        with open(image_path, "rb") as img:
            image_bytes = img.read()

        image_part = types.Part.from_bytes(data=image_bytes, mime_type="image/png")

        # ----------------------------------------
        # 6️⃣ Send to Gemini
        # ----------------------------------------
        try:
            response = client.models.generate_content(
                model="gemini-2.5-pro",
                contents=[prompt, image_part],
                config=types.GenerateContentConfig(response_mime_type="text/plain"),
            )

            csv_text = response.text.strip()

            # ----------------------------------------
            # 7️⃣ Save results
            # ----------------------------------------
            csv_filename = f"table_{idx}.csv"
            json_entry = {
                "table_index": idx,
                "csv_file": csv_filename,
                "html_table": table_html,
                "csv_output": csv_text
            }

            # Append structured log entry
            with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(json_entry, ensure_ascii=False) + "\n")

            # Save the CSV itself
            try:
                df = pd.read_csv(StringIO(csv_text))
                df.to_csv(csv_filename, index=False, encoding="utf-8")
                print(f"✅ Table {idx} saved to {csv_filename}")
            except Exception as e:
                print(f"⚠️ Could not parse CSV with pandas: {e}")
                # fallback: raw CSV text
                with open(csv_filename, "w", encoding="utf-8") as f:
                    f.write(csv_text)
                print(f"💾 Saved raw CSV text for table {idx}")

        except Exception as e:
            print(f"❌ Failed to process table {idx}: {e}")

# ----------------------------------------
# 8️⃣ Entry Point
# ----------------------------------------
if __name__ == "__main__":
    extract_html_tables_from_markdown()
