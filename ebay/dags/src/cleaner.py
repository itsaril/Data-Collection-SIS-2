from bs4 import BeautifulSoup
from datetime import datetime
import re
import hashlib

import hashlib

def normalize_text(text):

    if not text or text in ["N/A", "Unknown", ""]:
        return None

    text = ' '.join(text.split())
    text = text.strip()
    
    return text if text else None


def normalize_price(price):

    if price is None or price == 0:
        return None
    
    try:
        price_float = float(price)
        return round(price_float, 2) if price_float > 0 else None
    except (ValueError, TypeError):
        return None


def normalize_condition(condition):

    if not condition or condition == "Unknown":
        return None
    
    condition_lower = condition.lower().strip()
    
    if any(word in condition_lower for word in ['new', 'новый', 'brand new']):
        return "New"
    elif any(word in condition_lower for word in ['refurbished', 'восстановлен', 'renewed']):
        return "Refurbished"
    elif any(word in condition_lower for word in ['used', 'б/у', 'pre-owned']):
        return "Used"
    else:
        return condition.title()


def normalize_location(location):

    if not location or location == "Unknown":
        return None
    
    location = location.strip()
    location = location.replace('from:', '').replace('From:', '').replace('из:', '').strip()
    
    return location.title() if location else None


def normalize_currency(currency):

    if not currency:
        return "USD"
    
    currency = currency.upper().strip()
   
    valid_currencies = ["USD", "EUR", "GBP", "RUB", "CNY"]
    
    return currency if currency in valid_currencies else "USD"


def normalize_url(url):

    if not url or url == "N/A":
        return None

    if '&' in url:
        url = url.split('&')[0]
    
    return url.strip()


def normalize_datetime(dt_string):

    if not dt_string:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        datetime.strptime(dt_string, "%Y-%m-%d %H:%M:%S")
        return dt_string
    except ValueError:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def clean_item_data(item):

    cleaned = {
        'title': normalize_text(item.get('title')),
        'price': normalize_price(item.get('price')),
        'currency': normalize_currency(item.get('currency')),
        'condition': normalize_condition(item.get('condition')),
        'seller_name': normalize_text(item.get('seller_name')),
        'location': normalize_location(item.get('location')),
        'shipping_price': normalize_price(item.get('shipping_price')),
        'rating': normalize_price(item.get('rating')),  
        'reviews_count': int(item.get('reviews_count', 0)) if item.get('reviews_count') else None,
        'item_url': normalize_url(item.get('item_url')),
        'scraped_at': normalize_datetime(item.get('scraped_at')),
        'specifications': item.get('specifications')  
    }
    
    return cleaned


def is_valid_item(item):

    return (
        item.get('title') is not None and
        item.get('item_url') is not None and
        len(item.get('title', '')) > 3
    )


def get_item_hash(item):

    url = item.get('item_url', '')
    if not url:
        unique_string = f"{item.get('title', '')}_{item.get('price', 0)}"
    else:
        unique_string = url
    
    return hashlib.md5(unique_string.encode()).hexdigest()


def remove_duplicates(items):

    seen_hashes = set()
    unique_items = []
    duplicates_count = 0
    
    for item in items:
        item_hash = get_item_hash(item)
        
        if item_hash not in seen_hashes:
            seen_hashes.add(item_hash)
            unique_items.append(item)
        else:
            duplicates_count += 1
    
    print(f" Duplicates removed: {duplicates_count}")
    
    return unique_items


def parse_raw_price(raw_price):
    try:
        price_str = re.sub(r'[^\d.,]', '', raw_price)

        if ',' in price_str and '.' in price_str:

            last_comma = price_str.rfind(',')
            last_dot = price_str.rfind('.')
            if last_comma > last_dot:
                price_str = price_str.replace('.', '').replace(',', '.')
            else:
                price_str = price_str.replace(',', '')
        elif ',' in price_str:
            parts = price_str.split(',')
            if len(parts[-1]) == 2:  
                price_str = price_str.replace(',', '.')
            else:
                price_str = price_str.replace(',', '')
        
        return float(price_str) if price_str else 0
    except:
        return 0


def parse_product_page(html):
    soup = BeautifulSoup(html, 'html.parser')
    data = {}
    
    try:
        import json
        script_tags = soup.find_all('script', type='application/json')
        
        for script in script_tags:
            try:
                json_data = json.loads(script.string)
                
                if 'trustSignals' in json_data:
                    for signal in json_data['trustSignals']:
                        if 'textSpans' in signal:
                            for span in signal['textSpans']:
                                text = span.get('text', '')
                                if 'positive feedback' in text:
                                    match = re.search(r'([\d.]+)%', text)
                                    if match:
                                        data['rating'] = float(match.group(1))
                                elif 'items sold' in text or 'sold' in text:
                                    sold_text = text.replace('items sold', '').replace('sold', '').strip()
                                    if 'K' in sold_text:
                                        num = float(sold_text.replace('K', '').strip())
                                        data['reviews_count'] = int(num * 1000)
                                    else:
                                        match = re.search(r'([\d,]+)', sold_text)
                                        if match:
                                            data['reviews_count'] = int(match.group(1).replace(',', ''))

                if 'ABOUT_THIS_ITEM' in json_data:
                    about_section = json_data['ABOUT_THIS_ITEM']
                    if 'sections' in about_section and 'features' in about_section['sections']:
                        features = about_section['sections']['features']
                        if 'dataItems' in features:
                            specs = {}
                            for key, item in features['dataItems'].items():
                                if isinstance(item, dict) and 'labels' in item and 'values' in item:
                                    label = ''
                                    if item['labels'] and 'textSpans' in item['labels'][0]:
                                        label = item['labels'][0]['textSpans'][0].get('text', '')

                                    value = ''
                                    if item['values'] and 'textSpans' in item['values'][0]:
                                        value = item['values'][0]['textSpans'][0].get('text', '')
                                    
                                    if label and value:
                                        specs[label] = value
                            
                            if specs:
                                data['specifications'] = json.dumps(specs, ensure_ascii=False)
                
            except (json.JSONDecodeError, KeyError, TypeError, AttributeError):
                continue
        seller_elem = soup.select_one('div.x-sellercard-atf__info__about-seller a')
        if seller_elem:
            data['seller_name'] = normalize_text(seller_elem.get_text())
        
        feedback_elem = soup.select_one('span.ux-textspans--SECONDARY')
        if feedback_elem:
            feedback_text = feedback_elem.get_text()
            match = re.search(r'\((\d+)\)', feedback_text)
            if match:
                data['seller_feedback_count'] = int(match.group(1))

        positive_elem = soup.select_one('span.ux-textspans--POSITIVE')
        if positive_elem:
            positive_text = positive_elem.get_text()
            match = re.search(r'([\d.]+)%', positive_text)
            if match:
                data['seller_positive_feedback'] = float(match.group(1))

        location_elem = soup.select_one('div.ux-labels-values--shipping span.ux-textspans--SECONDARY')
        if location_elem:
            data['item_location'] = normalize_location(location_elem.get_text())
        
        shipping_elem = soup.select_one('span[data-testid="ux-labels-values__values-content"] span.ux-textspans')
        if shipping_elem:
            shipping_text = shipping_elem.get_text()
            if 'Free' in shipping_text or 'Бесплатно' in shipping_text:
                data['shipping_price'] = 0.0
            else:
                match = re.search(r'[\$€£]?\s?([\d,]+\.?\d*)', shipping_text)
                if match:
                    price_str = match.group(1).replace(',', '')
                    data['shipping_price'] = float(price_str)

        condition_elem = soup.select_one('div.x-item-condition-text span.ux-textspans')
        if condition_elem:
            data['condition'] = normalize_condition(condition_elem.get_text())

        quantity_sold_elem = soup.select_one('span.ux-textspans--SECONDARY[data-testid="qty-sold"]')
        if quantity_sold_elem:
            sold_text = quantity_sold_elem.get_text()
            match = re.search(r'([\d,]+)', sold_text)
            if match:
                data['quantity_sold'] = int(match.group(1).replace(',', ''))

        views_elem = soup.select_one('span.ux-textspans--SECONDARY[class*="views"]')
        if views_elem:
            views_text = views_elem.get_text()
            match = re.search(r'([\d,]+)', views_text)
            if match:
                data['views_count'] = int(match.group(1).replace(',', ''))
        
        description_elem = soup.select_one('div.ux-layout-section__item--description')
        if description_elem:
            data['description'] = normalize_text(description_elem.get_text())

        specs = {}
        spec_rows = soup.select('div.ux-labels-values')
        for row in spec_rows:
            label_elem = row.select_one('span.ux-textspans--BOLD')
            value_elem = row.select_one('span.ux-textspans:not(.ux-textspans--BOLD)')
            
            if label_elem and value_elem:
                label = normalize_text(label_elem.get_text())
                value = normalize_text(value_elem.get_text())
                if label and value:
                    specs[label] = value
        
        if specs:
            data['specifications'] = specs
        
    except Exception as e:
        print(f"Error parsing product page: {e}")
    
    return data


def enrich_items_with_product_data(items_data, product_htmls):

    print("\n" + "="*70)
    print("DATA ENRICHMENT")
    print("="*70)
    
    enriched_items = []
    
    for idx, (item, html) in enumerate(zip(items_data, product_htmls), 1):
        enriched_item = item.copy()
        
        if html:
            product_data = parse_product_page(html)

            for key, value in product_data.items():
                if value is not None:

                    if key not in enriched_item or enriched_item.get(key) is None or enriched_item.get(key) == 'Unknown':
                        enriched_item[key] = value
            
            print(f"[{idx}/{len(items_data)}] ✓ Enriched: +{len(product_data)} fields")
        else:
            print(f"[{idx}/{len(items_data)}] Omitted (no HTML)")
        
        enriched_items.append(enriched_item)
    
    print("="*70)
    print(f"ENRICHMENT COMPLETED")
    print("="*70)
    
    return enriched_items


def parse_items(html_content):

    soup = BeautifulSoup(html_content, 'html.parser')

    cards = soup.find_all('div', class_='su-card-container')
    data = []
    
    print(f'Product cards found: {len(cards)}')
    
    for idx, card in enumerate(cards):
        try:
            title = "N/A"
            title_elem = card.find('span', class_='su-styled-text--header')
            if not title_elem:
                title_elem = card.find('div', class_='s-card__title')
            if title_elem:
                title = title_elem.get_text(strip=True)
                title = title.replace('New ad', '').replace('Opens in a new window or tab', '').strip()
            
            if title in ["N/A", "Shop on eBay", ""]:
                continue

            price_elem = card.find('span', class_='s-card__price')
            price_text = price_elem.get_text(strip=True) if price_elem else "$0"
            price = parse_raw_price(price_text)

            currency = "USD"
            if "EUR" in price_text or "€" in price_text:
                currency = "EUR"
            elif "GBP" in price_text or "£" in price_text:
                currency = "GBP"

            condition = "Unknown"
            subtitle_elem = card.find('div', class_='s-card__subtitle')
            if subtitle_elem:
                subtitle_text = subtitle_elem.get_text()
                if 'Совершенно новый' in subtitle_text or 'Brand New' in subtitle_text or 'New' in subtitle_text:
                    condition = "New"
                elif 'Восстановлен' in subtitle_text or 'Refurbished' in subtitle_text:
                    condition = "Refurbished"
                elif 'Б/у' in subtitle_text or 'Used' in subtitle_text or 'Pre-Owned' in subtitle_text:
                    condition = "Used"
            
            seller_name = "Unknown"

            location = "Unknown"
            all_spans = card.find_all('span', class_='su-styled-text')
            for span in all_spans:
                text = span.get_text(strip=True)
                if text.startswith('из:') or text.startswith('from:') or text.startswith('From:'):
                    location = text.replace('из:', '').replace('from:', '').replace('From:', '').strip()
                    break

            shipping_price = 0
            for span in all_spans:
                text = span.get_text(strip=True)
                if 'Бесплатная' in text or 'Free' in text or 'бесплатная' in text:
                    shipping_price = 0
                    break
                elif 'доставка' in text.lower() or 'shipping' in text.lower():
                    match = re.search(r'[\$€£]\s*[\d,\.]+', text)
                    if match:
                        shipping_price = parse_raw_price(match.group())
                    break
            
            rating = 0

            reviews_count = 0

            item_url = "N/A"
            link_elem = card.find_parent('a')
            if not link_elem:
                link_elem = card.find('a')
            if link_elem and link_elem.get('href'):
                item_url = link_elem.get('href')
                if len(item_url) > 200:
                    item_url = item_url.split('&itmprp=')[0]

            scraped_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            item_data = {
                'title': title[:150], 
                'price': price,
                'currency': currency,
                'condition': condition,
                'seller_name': seller_name,
                'location': location,
                'shipping_price': shipping_price,
                'rating': rating,
                'reviews_count': reviews_count,
                'item_url': item_url,
                'scraped_at': scraped_at
            }
            
            data.append(item_data)
            
        except Exception as e:
            print(f'Card parsing error #{idx}: {e}')
            continue
    
    return data


def parse_html_pages(html_pages):
    all_items = []
    
    print("\n" + "="*70)
    print("Parsing HTML pages...")
    print("="*70)
    
    for idx, html in enumerate(html_pages, 1):
        print(f"\nParsing pages {idx}/{len(html_pages)}...")
        items = parse_items(html)
        all_items.extend(items)
        print(f"✓ Products found: {len(items)}")
        print(f"Total collected: {len(all_items)}")
    
    print(f"\n{'='*70}")
    print("Data cleaning and normalization...")
    print(f"{'='*70}")

    print(f"\nInitial quantity of goods: {len(all_items)}")
    valid_items = [item for item in all_items if is_valid_item(item)]
    invalid_count = len(all_items) - len(valid_items)
    if invalid_count > 0:
        print(f"Invalid products removed: {invalid_count}")
    
    print(f"\n Data clearing...")
    cleaned_items = [clean_item_data(item) for item in valid_items]
    print(f"   ✓ Items cleared: {len(cleaned_items)}")

    print(f"\nRemoving duplicates...")
    unique_items = remove_duplicates(cleaned_items)
    print(f" Unique products: {len(unique_items)}")
    
    final_items = [item for item in unique_items if is_valid_item(item)]

    print(f"\n{'='*70}")
    print(" CLEANING STATISTICS:")
    print(f"{'='*70}")
    print(f"   Original goods:     {len(all_items)}")
    print(f"   Invalid:           -{invalid_count}")
    print(f"   After cleaning:        {len(cleaned_items)}")
    print(f"   Duplicates removed:   -{len(cleaned_items) - len(unique_items)}")
    print(f"   TOTAL:                {len(final_items)}")
    print(f"\n DATA COMPLETENESS:")
    print(f"{'='*70}")
    
    if final_items:
        fields = ['price', 'condition', 'location', 'shipping_price']
        for field in fields:
            filled = sum(1 for item in final_items if item.get(field) is not None)
            percentage = (filled / len(final_items)) * 100
            print(f"   {field:20s}: {filled:4d}/{len(final_items)} ({percentage:.1f}%)")
    
    print(f"{'='*70}")
    print(f"Parsing complete! Total products: {len(final_items)}")
    print(f"{'='*70}")
    
    return final_items


if __name__ == "__main__":
    print("=" * 70)
    print("        EBAY CLEANER - parsing HTML")
    print("=" * 70)
    print()

    import sys
    
    if len(sys.argv) > 1:
        filename = sys.argv[1]
        print(f"Loading HTML from a file: {filename}")
        with open(filename, 'r', encoding='utf-8') as f:
            html = f.read()
        
        items = parse_items(html)

        import json
        output_file = filename.replace('.html', '_parsed.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(items, f, ensure_ascii=False, indent=2)
        
        print(f"\n✓ Data saved in {output_file}")
    else:
        print("Usage: python cleaner.py <html_file>")