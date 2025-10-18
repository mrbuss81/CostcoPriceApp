🧾 README: Costco Price Tracker (MVP)
🧠 Overview
The Costco Price Tracker is a Python-based tool that monitors product prices and automatically logs changes over time.
It was built as a learning project to combine web scraping, data parsing, and file I/O — while solving a real-world problem: tracking Costco product price drops (especially within return windows).

🚀 Features
✅ Parses product title and price from Costco product pages (or saved HTML)
✅ Stores all checks in a structured CSV file
✅ Detects and reports price drops or increases
✅ Clean console output with clear visual feedback
✅ Built using Python, BeautifulSoup, and standard libraries only

🧩 Tech Stack
Language: Python 3.9+
Libraries:
BeautifulSoup — HTML parsing
csv — structured data logging
datetime & os — timestamps and file handling
(Optional) matplotlib — for visualizing price trends (planned for v1.1)

⚙️ How It Works
Load a product page (saved locally or fetched later via Playwright).
Extract product title and price with BeautifulSoup.
Save each check into price_log.csv with timestamp.
Compare the latest price to the previous entry.
Print alerts for price drops or increases directly in the terminal.

🧮 Example Output
Page title: Simmons 20.3 cm (8 in.) Gel Memory Foam Mattress | Costco
Current price: 299.99
✅ Price logged successfully!
💸 Price dropped by $40.00 since last check!

🧔 About the Creator
Michael Buss — a CS student, dad, and lifelong learner behind The CompSci RV Dad.
This project combines practical skills in data parsing and automation with real-world motivation: making life simpler through smart tools.


---
### 🎥 YouTube Video Description

