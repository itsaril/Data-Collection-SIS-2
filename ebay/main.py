import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from .src.scraper import scrape_ebay, setup_driver, scrape_product_pages
from .src.cleaner import parse_html_pages, enrich_items_with_product_data
from .src.loader import load_and_save


def main(search_query="laptop", max_items=100, save_html=True, enrich_data=True):

    print("=" * 70)
    print("        EBAY SCRAPER - FULL CYCLE")
    print("=" * 70)
    print(f"\n Search query: {search_query}")
    print(f" Goal: minimum {max_items} goods")
    print(f" Saving HTML: {'Yes' if save_html else 'No'}")
    print(f" Data enrichment: {'Yes' if enrich_data else 'No'}")
    print()
    print("\n" + "="*70)
    print("Step 1: LOADING PAGES")
    print("="*70)
    
    html_pages = scrape_ebay(
        search_query=search_query, 
        max_items=max_items, 
        save_html=save_html
    )
    
    if not html_pages:
        print("\n Failed to load pages!")
        return None
    
    print("\n" + "="*70)
    print("STEP 2: DATA PARSE")
    print("="*70)
    
    items_data = parse_html_pages(html_pages)
    
    if not items_data:
        print("\n Failed to parse data!")
        return None
    

    if enrich_data:
        print("\n" + "="*70)
        print("STEP 2.5: DATA ENRICHMENT")
        print("="*70)
        print("Loading product pages for detailed information...")

        product_htmls = scrape_product_pages(items_data, save_html=save_html)

        items_data = enrich_items_with_product_data(items_data, product_htmls)
   
    print("\n" + "="*70)
    print("STEP 3: SAVE")
    print("="*70)
    
    json_filename = f'ebay_{search_query}_results.json'
    db_name = 'ebay_products.db'
    
    stats = load_and_save(
        items_data=items_data,
        search_query=search_query,
        save_json=True,
        save_db=True,
        json_filename=json_filename,
        db_name=db_name
    )

    print("\n" + "="*70)
    print("PRODUCT EXAMPLES (first 5):")
    print("="*70)
    
    for i, item in enumerate(items_data[:5], 1):
        print(f"\n{i}. {item['title']}")
        print(f"   Cost: {item['currency']} ${item['price']:.2f}" if item.get('price') else "   Cost: N/A")
        
        shipping = item.get('shipping_price')
        if shipping is not None:
            print(f"   Delivery: ${shipping:.2f}")
        else:
            print(f"   Delivery: N/A")
        
        print(f"   State: {item.get('condition', 'N/A')}")
        print(f"   Location: {item.get('location', 'N/A')}")
        print(f"   URL: {item['item_url'][:70]}...")

    print("\n" + "="*70)
    print("Parsing Completed!")
    print("="*70)
    print(f"Pages loaded: {len(html_pages)}")
    print(f"Products found: {stats['total_items']}")
    print(f"JSON saved: {json_filename}")
    print(f"Database: {db_name}")
    print(f"Records in the database: {stats['db_records_saved']}")
    print("="*70)
    
    return stats

if __name__ == "__main__":
    print("\n" + "="*70)
    print(" EBAY SCRAPER - Modular Architecture")
    print("="*70)
    print("\n Modules:")
    print(" • src/scraper.py - Downloading pages via Selenium")
    print(" • src/cleaner.py - Parsing HTML and extracting data")
    print(" • src/loader.py - Saving to JSON and SQLite")
    print("\n New Features:")
    print(" • Data enrichment - downloading product pages for detailed information")
    print(" • Random delays between requests (2-5 seconds)")
    print(" • Parsing: seller, rating, sales, views, characteristics")
    print("\n Dependencies:")
    print(" pip install selenium webdriver-manager beautifulsoup4")
    print()
    
    search_query = "laptop"
    max_items = 100
    enrich_data = True  

    if len(sys.argv) > 1:
        search_query = sys.argv[1]
    if len(sys.argv) > 2:
        try:
            max_items = int(sys.argv[2])
        except ValueError:
            print(" Invalid max_items format, using 100")
    if len(sys.argv) > 3:
        enrich_data = sys.argv[3].lower() in ['true', 'yes', '1', 'да']

    main(search_query=search_query, max_items=max_items, save_html=True, enrich_data=enrich_data)
