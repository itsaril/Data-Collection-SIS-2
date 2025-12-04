# 🛒 eBay 

We chose eBay (https://www.ebay.com) because:
- It is a dynamic, JavaScript-rendered website  
- Product lists update dynamically  
- Many items load via lazy loading / infinite scroll  
- Product cards contain structured fields suitable for scraping  

The scraper collects product information based on any search query (e.g., "laptop"), including:
- title  
- price & currency  
- condition (new / used / refurbished)  
- seller name  
- item location  
- shipping cost  
- rating & review count  
- specifications (JSON if available)  
- product URL  
- timestamp  

The final cleaned dataset contains at least 100 valid products, as required.

---

# 🗄️ How to Run Airflow

The DAG is located in:
```
airflow_dag.py
```
▶️ Using Docker Airflow
```
docker compose build
docker compose up -d
```

Then open Airflow UI:
``` http://localhost:8080 ```

Inside the UI:

Locate the DAG: ebay_data_pipeline
- Turn it on
- Run manually (or wait for the scheduled run)

After a successful run, Airflow will show:

- green “success” marks
- logs for each task
- updated database in data/output.db

<img width="1916" height="982" alt="Screenshot 2025-12-04 172804" src="https://github.com/user-attachments/assets/b4cf3621-9c94-4a01-ba5a-b5259657ae2d" />

# 📦 Expected Output
1. SQLite database (output.db)
A table products containing:
 - title
 - price
 - currency
 - condition
 - seller_name
 - location
 - shipping_price
 - rating
 - reviews_count
 - item_url
 - scraped_at
 - search_query
 - specifications (JSON)

<img width="1916" height="1029" alt="image" src="https://github.com/user-attachments/assets/da500098-8705-4a20-9cc3-9e80cafd8316" />

<img width="1915" height="980" alt="image" src="https://github.com/user-attachments/assets/c463e103-ee09-4ff2-bc58-998f1ab1338c" />

2. JSON file with results
 ``` ebay_<search_query>_results.json ```

