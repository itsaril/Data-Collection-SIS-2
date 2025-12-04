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
    """Настройка Chrome WebDriver с заголовками"""
    chrome_options = Options()
    
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    chrome_options.add_argument('--log-level=3')
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.binary_location = "/usr/bin/chromium"
    service = Service("/usr/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver


def scrape_page(driver, url, page_num):
    print(f"\n{'='*70}")
    print(f"📄 Страница {page_num}: {url}")
    print(f"{'='*70}")
    driver.get(url)
    
    if page_num == 1:
        print("Проверка на CAPTCHA...")
        time.sleep(3)
        
        if "challenge" in driver.current_url or "captcha" in driver.page_source.lower():
            print("\n" + "="*70)
            print("⚠️  ОБНАРУЖЕНА CAPTCHA!")
            print("Пожалуйста, решите CAPTCHA вручную в открытом браузере")
            print("После решения CAPTCHA нажмите Enter в консоли...")
            print("="*70)
            input("Нажмите Enter после решения CAPTCHA: ")
            time.sleep(2)
    else:
        time.sleep(2)
    
    print("Ожидание загрузки товаров...")
    try:
        wait = WebDriverWait(driver, 20)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.su-card-container")))
        print("✓ Товары загружены!")
    except Exception as e:
        print(f"⚠️  Не удалось дождаться загрузки товаров: {e}")
        print("Продолжаем с текущим содержимым страницы...")
    
    print("Прокрутка страницы...")
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight/3);")
    time.sleep(1)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
    time.sleep(1)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)
    
    html = driver.page_source
    print(f"✓ HTML страницы получен ({len(html)} символов)")
    
    return html

def scrape_ebay(search_query="laptop", max_items=100, save_html=True):
    driver = None
    html_pages = []
    
    try:
        print("=" * 70)
        print("Запуск браузера...")
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
                print(f"✓ HTML сохранен в {filename}")
            
            html_pages.append(html)
            
            estimated_items = page_num * 60  
            total_items_found = estimated_items
            
            print(f"📊 Примерно собрано: ~{total_items_found} товаров")
            
            if total_items_found >= max_items:
                print(f"\n✅ Достигнуто примерное количество товаров")
                break
            
            page_num += 1
            print(f"\n⏩ Переход на страницу {page_num}...")
            time.sleep(2)
        
        print(f"\n✓ Загружено страниц: {len(html_pages)}")
        return html_pages
        
    except Exception as e:
        print(f"\n❌ Ошибка при загрузке: {e}")
        import traceback
        traceback.print_exc()
        return html_pages
        
    finally:
        if driver:
            print("\nЗакрытие браузера...")
            driver.quit()

