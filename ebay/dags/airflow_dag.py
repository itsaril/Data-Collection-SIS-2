import sys
import os
sys.path.append("/opt/airflow/dags/src")

from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import logging
import json

from src.scraper import scrape_ebay, scrape_product_pages
from src.cleaner import parse_html_pages, enrich_items_with_product_data
from src.loader import load_and_save

SEARCH_QUERY = "laptop"
MAX_ITEMS = 100

RAW_JSON_PATH = "/opt/airflow/dags/raw_items.json"
CLEAN_JSON_PATH = "/opt/airflow/dags/clean_items.json"
DB_NAME = "/opt/airflow/dags/ebay_products.db"

def scraping_task():
    logging.info("🚀 START SCRAPING TASK")

    html_pages = scrape_ebay(
        search_query=SEARCH_QUERY,
        max_items=MAX_ITEMS,
        save_html=False   
    )

    if not html_pages:
        raise Exception("❌ SCRAPING FAILED: No pages downloaded")

    with open(RAW_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(html_pages, f)

    logging.info(f"✅ SCRAPING DONE. Pages saved: {len(html_pages)}")
    logging.info(f"💾 RAW DATA SAVED TO: {RAW_JSON_PATH}")

def cleaning_task():
    logging.info("🧹 START CLEANING TASK")

    if not os.path.exists(RAW_JSON_PATH):
        raise Exception("❌ RAW FILE NOT FOUND")

    with open(RAW_JSON_PATH, "r", encoding="utf-8") as f:
        html_pages = json.load(f)

    cleaned_items = parse_html_pages(html_pages)

    if not cleaned_items:
        raise Exception("❌ CLEANING FAILED: No valid items")

    with open(CLEAN_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(cleaned_items, f, ensure_ascii=False, indent=2)

    logging.info(f"✅ CLEANING DONE. Clean items: {len(cleaned_items)}")
    logging.info(f"💾 CLEAN DATA SAVED TO: {CLEAN_JSON_PATH}")


def loading_task():
    logging.info("💾 START LOADING TASK")

    if not os.path.exists(CLEAN_JSON_PATH):
        raise Exception("❌ CLEAN FILE NOT FOUND")

    with open(CLEAN_JSON_PATH, "r", encoding="utf-8") as f:
        items_data = json.load(f)

    stats = load_and_save(
        items_data=items_data,
        search_query=SEARCH_QUERY,
        save_json=False,
        save_db=True,
        db_name=DB_NAME
    )

    logging.info("✅ LOADING DONE SUCCESSFULLY")
    logging.info(f"📊 LOAD STATS: {stats}")


default_args = {
    "owner": "airflow",
    "retries": 3,                              
    "retry_delay": timedelta(minutes=3),      
    "depends_on_past": False,
}

with DAG(
    dag_id="ebay_scraper_pipeline",            
    default_args=default_args,
    description="Ebay Scraping → Cleaning → Loading Pipeline",
    schedule_interval=timedelta(days=1),       
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["ebay", "scraping", "etl"],
) as dag:

    scrape = PythonOperator(
        task_id="scraping",
        python_callable=scraping_task,
    )

    clean = PythonOperator(
        task_id="cleaning",
        python_callable=cleaning_task,
    )

    load = PythonOperator(
        task_id="loading",
        python_callable=loading_task,
    )

    scrape >> clean >> load