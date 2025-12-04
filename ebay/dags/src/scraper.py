from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import random


def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    chrome_options.add_argument('--log-level=3')

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver


def scrape_page(driver, url, page_num):

    print(f"\n{'='*70}")
    print(f"Page {page_num}: {url}")
    print(f"{'='*70}")
    driver.get(url)
    
    if page_num == 1:
        print("CAPTCHA check...")
        time.sleep(3)
        
        if "challenge" in driver.current_url or "captcha" in driver.page_source.lower():
            print("\n" + "="*70)
            print("CAPTCHA DETECTED!")
            print("Please solve the CAPTCHA manually in an open browser.")
            print("After solving the CAPTCHA, press Enter in the console...")
            print("="*70)
            input("Press Enter after solving the CAPTCHA: ")
            time.sleep(2)
    else:
        time.sleep(2)

    print("Waiting for goods to load...")
    try:
        wait = WebDriverWait(driver, 20)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.su-card-container")))
        print("✓ Products loaded!")
    except Exception as e:
        print(f"Unable to wait for items to load: {e}")
        print("We continue with the current content of the page...")

    print("Scrolling the page...")
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight/3);")
    time.sleep(1)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
    time.sleep(1)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)

    html = driver.page_source
    print(f"✓ HTML page received ({len(html)} symbols)")
    
    return html


def scrape_product_page(driver, url, item_index, total_items):

    try:
        delay = random.uniform(2.0, 5.0)
        print(f"\n[{item_index}/{total_items}] Delay {delay:.1f}с...")
        time.sleep(delay)
        
        print(f"[{item_index}/{total_items}] Delay: {url[:80]}...")
        driver.get(url)

        try:
            wait = WebDriverWait(driver, 10)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.vim")))
        except:
            pass

        time.sleep(random.uniform(1.0, 2.0))
        
        html = driver.page_source
        print(f"[{item_index}/{total_items}] ✓ Received {len(html)} symbols")
        
        return html
        
    except Exception as e:
        print(f"[{item_index}/{total_items}] error: {e}")
        return None


def scrape_product_pages(items_data, save_html=True):

    driver = None
    product_htmls = []
    
    try:
        print("\n" + "="*70)
        print("LOADING PRODUCT PAGES")
        print("="*70)
        print(f"Total products: {len(items_data)}")
        print(f"Average latency: 3-4 seconds between requests")
        
        driver = setup_driver()
        
        for idx, item in enumerate(items_data, 1):
            url = item.get('item_url')
            
            if not url:
                print(f"[{idx}/{len(items_data)}] Missing: No URL")
                product_htmls.append(None)
                continue

            html = scrape_product_page(driver, url, idx, len(items_data))
            product_htmls.append(html)

            if save_html and html:
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                item_id = url.split('/')[-1].split('?')[0][:50]
                filename = f'ebay_product_{item_id}_{timestamp}.html'
                
                try:
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(html)
                    print(f"[{idx}/{len(items_data)}] Saved: {filename}")
                except Exception as e:
                    print(f"[{idx}/{len(items_data)}]  Failed to save: {e}")
        
        print("\n" + "="*70)
        print(f" DOWNLOAD COMPLETED")
        print(f"Succes: {sum(1 for h in product_htmls if h is not None)}/{len(items_data)}")
        print("="*70)
        
        return product_htmls
        
    finally:
        if driver:
            print("Closing the browser...")
            driver.quit()


def scrape_ebay(search_query="laptop", max_items=100, save_html=True):

    driver = None
    html_pages = []
    
    try:
        print("=" * 70)
        print("Launching the browser...")
        driver = setup_driver()
        
        page_num = 1
        total_items_found = 0
        
        while total_items_found < max_items:
            url = f"https://www.ebay.com/sch/i.html?_nkw={search_query}&_sacat=0&_from=R40&_pgn={page_num}"

            html = scrape_page(driver, url, page_num)

            if save_html:
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f'ebay_{search_query}_page{page_num}_{timestamp}.html'
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(html)
                print(f"✓ HTML saved in {filename}")
            
            html_pages.append(html)

            estimated_items = page_num * 60  
            total_items_found = estimated_items
            
            print(f" Approximately collected: ~{total_items_found} goods")

            if total_items_found >= max_items:
                print(f"\n The approximate quantity of goods has been reached")
                break

            page_num += 1
            print(f"\n Go to page{page_num}...")
            time.sleep(2)  
        
        print(f"\n✓ Pages loaded: {len(html_pages)}")
        return html_pages
        
    except Exception as e:
        print(f"\n Error loading: {e}")
        import traceback
        traceback.print_exc()
        return html_pages
        
    finally:
        if driver:
            print("\nClosing the browser...")
            driver.quit()


if __name__ == "__main__":
    print("=" * 70)
    print("        EBAY SCRAPER - Loading pages")
    print("=" * 70)
    print()
    
    html_pages = scrape_ebay(search_query="laptop", max_items=100, save_html=True)
    print(f"\n Loaded {len(html_pages)} pages")
