#!/usr/bin/env python3
# price_diff_notifier.py
#
# Automatically detect newest sales snapshots and report price drops.

import csv, sys, argparse
from pathlib import Path
from datetime import datetime

DATA_DIR = Path(__file__).resolve().parent / "data"

def parse_price(price_str):
    """Convert a price like '$18.99' to float 18.99"""
    if not price_str:
        return None
    digits = ''.join(ch for ch in price_str if (ch.isdigit() or ch == '.'))
    try:
        return float(digits)
    except ValueError:
        return None

def load_csv(path):
    """Load sale data into a dict keyed by product_name + source_url"""
    data = {}
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = (row["product_name"].strip().lower(), row["source_url"].strip())
            data[key] = row
    return data

def compare(old_data, new_data):
    """Return list of price drop dicts"""
    drops = []
    for key, new_item in new_data.items():
        if key not in old_data:
            continue
        old_price = parse_price(old_data[key]["sale_price"])
        new_price = parse_price(new_item["sale_price"])
        if old_price and new_price and new_price < old_price:
            drops.append({
                "product_name": new_item["product_name"],
                "old_price": old_price,
                "new_price": new_price,
                "drop_amount": round(old_price - new_price, 2),
                "post_title": new_item.get("post_title", ""),
                "post_date": new_item.get("post_date", ""),
                "source_url": new_item.get("source_url", "")
            })
    return drops

def save_drops(drops, out_path):
    """Save price drops to CSV"""
    fieldnames = ["product_name", "old_price", "new_price", "drop_amount", "post_title", "post_date", "source_url"]
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for d in drops:
            w.writerow(d)

def auto_find_sales_files():
    """Find the two newest sales_*.csv files in /data/"""
    csvs = sorted(DATA_DIR.glob("sales_*.csv"), key=lambda p: p.stat().st_mtime, reverse=True)
    if len(csvs) < 2:
        print("❗ Need at least two sales_*.csv files in /data to compare.")
        sys.exit(1)
    return csvs[1], csvs[0]  # (oldest_recent, newest)

def main():
    ap = argparse.ArgumentParser(description="Detect Costco price drops automatically.")
    ap.add_argument("--old", help="(optional) override old CSV path")
    ap.add_argument("--new", help="(optional) override new CSV path")
    args = ap.parse_args()

    if args.old and args.new:
        old_path, new_path = Path(args.old), Path(args.new)
    else:
        old_path, new_path = auto_find_sales_files()

    print(f"Comparing:\n  OLD → {old_path.name}\n  NEW → {new_path.name}\n")

    old_data = load_csv(old_path)
    new_data = load_csv(new_path)
    drops = compare(old_data, new_data)

    if not drops:
        print("No price drops detected.")
        return

    print(f"=== PRICE DROPS ({len(drops)}) ===")
    for d in drops:
        print(f"🔔 {d['product_name']} — ${d['new_price']} ↓ from ${d['old_price']} (−${d['drop_amount']}) [{d['post_title']}]")

    out_file = DATA_DIR / f"price_drops_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    save_drops(drops, out_file)
    print(f"\nSaved {len(drops)} drops to {out_file}")

if __name__ == "__main__":
    main()
