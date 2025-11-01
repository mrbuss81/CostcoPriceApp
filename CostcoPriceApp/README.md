# 💰 Costco Price Tracker App
**Author:** Michael Buss  
**Project Phase:** 1.5 (out of 3)  
**Language:** Python (Playwright + BeautifulSoup + pandas)

---

## 🧾 Overview
This project tracks **weekly Costco sale prices** across Western Canada by scraping data from the public **Costco West Blog**.  
It automates price collection, calculates savings, and logs differences over time — serving as the foundation for a future **price-alert / watchlist system**.

---

## 🧩 Key Features
- 🔍 **Web Scraping:** Collects product names, prices, savings %, and URLs using Playwright + BeautifulSoup.  
- 📊 **Data Comparison:** `price_checker.py` analyzes differences between the latest scrape and previous logs.  
- 💾 **Data Storage:** Exports results as timestamped CSVs (e.g., `sales_2025-10-30.csv`) and maintains a master `price_log.csv`.  
- 🕓 **Version Control:** Keeps historical data in `/data/archive` for longitudinal tracking.  
- 🧠 **Savings Logic:** Computes percentage change between regular and sale prices.  
- 🧾 **Logging:** Detailed runtime and error logs for each scrape in `/logs`.

---

## 🗂️ Project Structure
```text
CostcoPriceApp/
  README.md                    - Project overview (this file)
  costcowest_scraper.py        - Main scraper script
  price_checker.py             - Compares and calculates savings
  price_diff_notifier.py       - Future notifications module
  data/                        - CSV outputs and price logs
    archive/                   - Historical snapshots
    sales_YYYY-MM-DD.csv       - Dated weekly scrape data
    price_log.csv              - Master aggregated log
    sample_urls.txt            - Optional list of test URLs
  logs/                        - Execution and debug logs
  notes.md                     - Dev notes and to-dos
  sample_product.html          - For offline scraper testing
  requirements.txt             - Dependencies list
  venv/                        - Local Python virtual environment
```

---

## ⚙️ Installation & Usage
```bash
# 1. Clone the repository
git clone https://github.com/CompSciRVDad/CostcoPriceApp.git
cd CostcoPriceApp

# 2. Set up the environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Run the scraper and save latest data
python costcowest_scraper.py

# 4. Compare against previous data (optional)
python price_checker.py
```

Outputs are saved under `/data/` and deltas logged automatically.

---


### ⚡ Quick Setup Tip

After installing dependencies, you’ll need to install Playwright’s browser binaries once:

```bash
playwright install chromium


---

## 🧠 Design Highlights
- **Readable Pipeline:** Each phase (scrape → save → compare → log) is separated into modular scripts.  
- **Data Integrity:** Old files archived before new runs.  
- **Portable Format:** All results are CSV for easy import into Excel or SQL tools.  
- **Extensible:** `price_diff_notifier.py` already prepared for future alert logic.

---

## 🚀 Phase 2 Roadmap
| Feature | Description | Status |
|----------|--------------|--------|
| 🔔 Notifications | Email / Discord alerts for price drops on tracked items | ⏳ Planned |
| 📋 Watchlist | User-defined CSV/JSON for specific product tracking | ⏳ Planned |
| 🕒 Automation | Scheduled runs using `cron` or `schedule` module | ⏳ Planned |
| 🧩 Dashboard | Simple web interface for search and reporting | ⏳ Future Idea |

**Current Phase:** 1.5 – data collection and comparison fully functional.  
**Next Milestone:** Implement notification logic for price drops (this winter).

---

## 📈 Learning Outcomes
- Strengthened Python skills (Playwright, BeautifulSoup, pandas).  
- Practiced file I/O, logging, and data versioning.  
- Applied software design principles for real-world data workflow.  

---

## 🧭 Author
**Michael Buss**  
Computer Science Undergraduate – University of the Fraser Valley  
GitHub: [mrbuss81](https://github.com/mrbuss81)  |  [CompSciRVDad](https://github.com/CompSciRVDad)  
📫 michaelbuss@ufv.ca  

---

### 🛣️ Project Journey
Part of my ongoing **“CompSci RV Dad”** learning series — building real-world projects that blend coursework and practical development.  
This repository represents both my learning process and my commitment to continuous improvement.

