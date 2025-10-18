from bs4 import BeautifulSoup
import csv
from datetime import datetime
import os
from io import StringIO

# --- Parse saved Costco page ---
with open("sample_product.html", "r", encoding="utf-8") as file:
    html = file.read()

soup = BeautifulSoup(html, "html.parser")
print("Page title:", soup.title.string if soup.title else "No title found")

price_element = soup.select_one("div#pull-right-price span.value.canada-currency-size")

if price_element:
    price_text = price_element.text.strip()
    print("Current price:", price_text)
else:
    print("Price not found – inspect HTML to confirm tag/class.")

# --- CSV Logging ---
csv_path = "price_log.csv"

if price_element:
    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    product_name = soup.title.string if soup.title else "Unknown Product"

    file_exists = os.path.exists(csv_path)
    with open(csv_path, "a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file, quoting=csv.QUOTE_ALL)
        if not file_exists:
            writer.writerow(["Date", "Product", "Price"])
        writer.writerow([date, product_name, price_text])

    print("✅ Price logged successfully!")

# --- Compare last vs current price ---
def get_last_logged_price(csv_path):
    """Return the previous logged price (not including the latest entry)."""
    if not os.path.exists(csv_path):
        return None

    with open(csv_path, "r", encoding="utf-8") as file:
        lines = file.readlines()
        if len(lines) <= 2:  # only header + 1 data line
            return None

        # Use the second-to-last data row for comparison
        prev_line = list(csv.reader(StringIO(lines[-2])))[0]
        try:
            return float(prev_line[-1])
        except ValueError:
            return None


last_price = get_last_logged_price(csv_path)

if last_price is not None:
    try:
        current_price = float(price_text)
        if current_price < last_price:
            difference = last_price - current_price
            print(f"💸 Price dropped by ${difference:.2f} since last check!")
        elif current_price > last_price:
            difference = current_price - last_price
            print(f"⬆️ Price increased by ${difference:.2f} since last check.")
        else:
            print("No price change since last check.")
    except ValueError:
        print("⚠️ Could not compare prices (invalid numeric data).")
else:
    print("📘 This is your first logged entry — no previous price to compare.")
