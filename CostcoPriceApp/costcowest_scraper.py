#!/usr/bin/env python3
# costcowest_scraper.py
#
# Scrapes a CostcoWest sale post (blog) and extracts:
#   product_name, sale_price, reg_price (if visible), post_title, post_date, source_url
#
# Usage examples:
#   python3 costcowest_scraper.py --url "https://<costcowest>/weekly-sales-oct-21-2025" --save sales.csv
#   python3 costcowest_scraper.py --urls-file sample_urls.txt --save sales.csv --watch watchlist.txt

import re, csv, sys, time, argparse, datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import requests
from bs4 import BeautifulSoup, Tag

HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/120.0 Safari/537.36"),
    "Accept-Language": "en-CA,en;q=0.9",
}

PRICE_RE = re.compile(r"(?:\$|CAD\s*\$?)\s*\d{1,3}(?:[,\d]{0,3})?(?:\.\d{2})?")
REG_RE   = re.compile(r"(?:reg|regular)\s*price\s*:?\s*(?:\$|CAD\s*\$?)\s*\d{1,3}(?:[,\d]{0,3})?(?:\.\d{2})?", re.I)
DATE_RE  = re.compile(r"(?:\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},\s+\d{4}\b)", re.I)

def fetch(url: str, timeout: int = 20) -> str:
    """Fetch HTML with retries."""
    for attempt in range(3):
        try:
            r = requests.get(url, headers=HEADERS, timeout=timeout)
            r.raise_for_status()
            return r.text
        except Exception:
            if attempt == 2: raise
            time.sleep(1.5 * (attempt + 1))
    return ""

def clean_text(t: str) -> str:
    return re.sub(r"\s+", " ", t or "").strip()

def extract_post_meta(soup: BeautifulSoup) -> Tuple[str, Optional[str]]:
    """Try to get post title and date from common blog patterns."""
    title = ""
    date_str = None

    for sel in ["h1.entry-title", "h1.post-title", "h1", "title"]:
        node = soup.select_one(sel)
        if node and clean_text(node.get_text()):
            title = clean_text(node.get_text())
            break

    meta_date = soup.find("meta", {"property": "article:published_time"}) or soup.find("meta", {"name": "date"})
    if meta_date and meta_date.get("content"):
        date_str = meta_date["content"]

    if not date_str:
        date_node = soup.find(string=DATE_RE)
        if date_node:
            date_str = clean_text(date_node)

    return title, date_str

def nearest_text_before(node: Tag, max_chars: int = 180) -> str:
    parent_text = clean_text(node.parent.get_text(" ")) if node.parent else ""
    text = parent_text
    text = PRICE_RE.sub("§PRICE§", text)
    left = text.split("§PRICE§")[0].strip()
    if left:
        chunks = re.split(r"[•\-\–\|:\n]", left)
        if chunks:
            cand = clean_text(chunks[-1])[-max_chars:]
            return cand
    if node.parent:
        prev = node.parent.previous_sibling
        if isinstance(prev, Tag):
            return clean_text(prev.get_text(" "))[:max_chars]
        elif prev and isinstance(prev, str):
            return clean_text(prev)[:max_chars]
    return ""

def extract_items_from_post(soup: BeautifulSoup, source_url: str, post_title: str, post_date: Optional[str]) -> List[Dict]:
    """
    Strategy:
      1) Find all occurrences of $xx.xx in the post body.
      2) For each price, derive a product name from nearby text.
      3) Capture 'INSTANT SAVINGS' amounts if present.
    """
    items = []
    content_scopes = soup.select(".entry-content, .post-content, article, .post, .content") or [soup.body or soup]
    seen_pairs = set()

    for scope in content_scopes:
        if not scope:
            continue
        texts = scope.find_all(string=PRICE_RE)

        for t in texts:
            txt = clean_text(t)

            # --- Fixed extraction logic ---
            instant_match = re.search(r"\(\$(\d+(?:\.\d{2})?)\s+INSTANT\s+SAVINGS", txt, re.I)
            instant_savings = instant_match.group(1) if instant_match else ""

            all_prices = PRICE_RE.findall(txt)
            sale_price = all_prices[-1] if all_prices else ""

            if not sale_price:
                continue
            # --- End fix ---

            parent = t.parent
            name = ""
            if parent:
                img = parent.find_previous("img")
                if img and img.get("alt"):
                    name = clean_text(img.get("alt"))
            if not name:
                name = nearest_text_before(t)

            regular_price = ""
            key = (name.lower(), sale_price)
            if not name or key in seen_pairs:
                continue
            seen_pairs.add(key)

            items.append({
                "post_title": post_title,
                "post_date": post_date or "",
                "product_name": name,
                "sale_price": sale_price,
                "regular_price": regular_price,
                "instant_savings": instant_savings,
                "source_url": source_url
            })
    return items

def save_csv(rows: List[Dict], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "post_title", "post_date", "product_name",
        "sale_price", "regular_price", "instant_savings",
        "approx_regular_price", "discount_percent",
        "source_url", "scraped_at"
    ]

    def to_float(val):
        if not val:
            return None
        match = re.search(r"\d+\.\d{2}", str(val))
        if match:
            try:
                return float(match.group(0))
            except ValueError:
                return None
        return None

    new_rows = []
    now = datetime.datetime.now().isoformat(timespec="seconds")

    for r in rows:
        rr = dict(r)
        sale = to_float(rr.get("sale_price"))
        instant = to_float(rr.get("instant_savings"))

        if sale and instant:
            regular = sale + instant
            rr["approx_regular_price"] = round(regular, 2)
            rr["discount_percent"] = round((instant / regular) * 100, 1)
        else:
            rr["approx_regular_price"] = ""
            rr["discount_percent"] = ""

        rr["scraped_at"] = now
        new_rows.append(rr)

    exists = out_path.exists()
    with out_path.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        if not exists:
            w.writeheader()
        for r in new_rows:
            w.writerow(r)

def recompute_csv(input_path: Path, output_path: Optional[Path] = None) -> None:
    if not input_path.exists():
        print(f"File not found: {input_path}")
        return
    out_path = output_path or input_path
    rows = []
    with input_path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rr = dict(row)
            def to_float(v):
                digits = ''.join(ch for ch in str(v) if (ch.isdigit() or ch == '.'))
                try:
                    return float(digits)
                except ValueError:
                    return None

            sale = to_float(rr.get("sale_price"))
            instant = to_float(rr.get("instant_savings"))

            if sale and instant:
                regular = sale + instant
                rr["approx_regular_price"] = round(regular, 2)
                rr["discount_percent"] = round((instant / regular) * 100, 1)
            else:
                rr["approx_regular_price"] = ""
                rr["discount_percent"] = ""

            rows.append(rr)


    with out_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print(f"✅ Recomputed derived fields for {len(rows)} rows → {out_path}")

def summarize_csv(input_path: Path, top_n: int = 10, flag_high: bool = False) -> None:

    if not input_path.exists():
        print(f"File not found: {input_path}")
        return
    rows = []
    with input_path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    if not rows:
        print("No data found.")
        return

    def to_float(v):
        digits = ''.join(ch for ch in str(v) if (ch.isdigit() or ch == '.'))
        try:
            return float(digits)
        except ValueError:
            return None

    discounts = []
    for r in rows:
        pct = to_float(r.get("discount_percent"))
        if pct:
            discounts.append((pct, r))

    print(f"\n📊 Summary for {input_path}")
    print("─" * 60)
    print(f"Total items: {len(rows)}")
    print(f"Items with instant savings: {len(discounts)}")
    if not discounts:
        print("No discount data available.")
        print("─" * 60)
        return
    avg = sum(p for p, _ in discounts) / len(discounts)
    hi, hi_row = max(discounts, key=lambda x: x[0])
    lo, lo_row = min(discounts, key=lambda x: x[0])
    print(f"Average discount: {avg:.1f}%")
    print(f"Highest discount: {hi:.1f}%")
    print(f"Lowest discount:  {lo:.1f}%")
    print(f"Top discounted item: {hi_row['product_name']} — {hi:.1f}% off")
    print("─" * 60)
    print(f"🏆 Top {min(top_n, len(discounts))} discounts:")
        # Optional flag for suspiciously high discounts
    if flag_high:

        flagged = [(pct, r) for pct, r in discounts if pct >= 60]
        if flagged:
            print("\n⚠️  Items with unusually high discounts (>= 60%):")
            for pct, row in flagged:
                print(f"- {row['product_name']} — {pct:.1f}% off")
        else:
            print("\n✅ No suspicious discounts (>= 60%) found.")

    for rank, (pct, row) in enumerate(sorted(discounts, key=lambda x: x[0], reverse=True)[:top_n], start=1):
        print(f"{rank:2d}. {row['product_name'][:60]} — {pct:.1f}% off")
    print("─" * 60)

def load_watchlist(path: Optional[Path]) -> List[str]:
    if not path or not path.exists(): return []
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

def filter_by_watchlist(items: List[Dict], watch: List[str]) -> List[Dict]:
    if not watch: return []
    results = []
    for it in items:
        name = it["product_name"].lower()
        if any(w.lower() in name for w in watch):
            results.append(it)
    return results

def scrape_one(url: str) -> List[Dict]:
    html = fetch(url)
    soup = BeautifulSoup(html, "lxml")
    post_title, post_date = extract_post_meta(soup)
    items = extract_items_from_post(soup, url, post_title, post_date)
    return items

def parse_args():
    ap = argparse.ArgumentParser(description="Scrape CostcoWest sale post(s) into CSV.")
    ap.add_argument("--url", help="A single CostcoWest sale post URL")
    ap.add_argument("--urls-file", help="Path to a text file of URLs (one per line)")
    ap.add_argument("--save", default="sales.csv", help="Output CSV path")
    ap.add_argument("--watch", help="Optional watchlist file (keywords, one per line)")
    ap.add_argument("--compute", action="store_true", help="Recompute approx_regular_price for an existing CSV file")
    ap.add_argument("--summary", action="store_true", help="Print discount summary for an existing CSV file")
    ap.add_argument("--top", type=int, default=10, help="Show top N discounts when using --summary (default 10)")
    ap.add_argument("--flag-high", action="store_true", help="Flag items with unusually high discounts (>= 60%)")
    return ap.parse_args()


def main():
    args = parse_args()
    if args.compute:
        recompute_csv(Path(args.save))
        sys.exit(0)
    if args.summary:
        summarize_csv(Path(args.save), top_n=args.top, flag_high=args.flag_high)

        sys.exit(0)

    urls = []
    if args.url:
        urls.append(args.url.strip())
    if args.urls_file:
        p = Path(args.urls_file)
        if p.exists():
            for line in p.read_text(encoding="utf-8").splitlines():
                if line.strip(): urls.append(line.strip())
    if not urls:
        print("No URLs provided. Use --url or --urls-file.")
        sys.exit(1)

    all_items: List[Dict] = []
    for u in urls:
        try:
            items = scrape_one(u)
            print(f"Parsed {len(items)} items from {u}")
            all_items.extend(items)
        except Exception as e:
            print(f"Error scraping {u}: {e}")

    if not all_items:
        print("No items found.")
        sys.exit(0)

    out_path = Path(args.save)
    save_csv(all_items, out_path)
    print(f"Saved {len(all_items)} rows to {out_path}")

    watch = load_watchlist(Path(args.watch) if args.watch else None)
    if watch:
        hits = filter_by_watchlist(all_items, watch)
        if hits:
            print("\n=== WATCHLIST MATCHES ===")
            for h in hits:
                print(f"- {h['product_name']} — {h['sale_price']} (post: {h['post_title']})")
        else:
            print("\n(No watchlist matches this run.)")

if __name__ == "__main__":
    main()
