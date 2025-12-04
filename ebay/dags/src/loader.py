import sqlite3
import json
import os

def create_database(db_name='ebay_products.db'):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            price REAL,
            currency TEXT,
            condition TEXT,
            seller_name TEXT,
            location TEXT,
            shipping_price REAL,
            rating REAL,
            reviews_count INTEGER,
            item_url TEXT UNIQUE,
            scraped_at TEXT,
            search_query TEXT,
            specifications TEXT
        )
    ''')

    cursor.execute('''CREATE INDEX IF NOT EXISTS idx_scraped_at ON products(scraped_at)''') 
    cursor.execute('''CREATE INDEX IF NOT EXISTS idx_search_query ON products(search_query)''')
    
    cursor.execute('''CREATE INDEX IF NOT EXISTS idx_price ON products(price)''')
    
    conn.commit()
    conn.close()
    print(f"✓ Database '{db_name}' created/updated")


def save_to_database(items_data, search_query, db_name='ebay_products.db'):

    if not items_data:
        print("⚠️  There is no data to save to the database.")
        return 0
    
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    
    inserted = 0
    updated = 0
    
    for item in items_data:
        try:
            specs = item.get('specifications')
            if specs and isinstance(specs, dict):
                specs = json.dumps(specs, ensure_ascii=False)
            elif specs and not isinstance(specs, str):
                specs = None
            
            cursor.execute('SELECT id FROM products WHERE item_url = ?', (item['item_url'],))
            existing = cursor.fetchone()
            
            if existing:
                cursor.execute('''
                    UPDATE products SET
                        title = ?,
                        price = ?,
                        currency = ?,
                        condition = ?,
                        seller_name = ?,
                        location = ?,
                        shipping_price = ?,
                        rating = ?,
                        reviews_count = ?,
                        scraped_at = ?,
                        search_query = ?,
                        specifications = ?
                    WHERE item_url = ?
                ''', (
                    item['title'],
                    item['price'],
                    item['currency'],
                    item['condition'],
                    item['seller_name'],
                    item['location'],
                    item['shipping_price'],
                    item['rating'],
                    item['reviews_count'],
                    item['scraped_at'],
                    search_query,
                    specs,
                    item['item_url']
                ))
                updated += 1
            else:
                cursor.execute('''
                    INSERT INTO products (
                        title, price, currency, condition, seller_name, 
                        location, shipping_price, rating, reviews_count, 
                        item_url, scraped_at, search_query, specifications
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    item['title'],
                    item['price'],
                    item['currency'],
                    item['condition'],
                    item['seller_name'],
                    item['location'],
                    item['shipping_price'],
                    item['rating'],
                    item['reviews_count'],
                    item['item_url'],
                    item['scraped_at'],
                    search_query,
                    specs
                ))
                inserted += 1
                
        except sqlite3.IntegrityError:
            continue
        except Exception as e:
            print(f"⚠️  Error saving product: {e}")
            continue
    
    conn.commit()
    conn.close()
    
    print(f"\n{'='*70}")
    print(f"💾 Saving to the database '{db_name}':")
    print(f"   ✓ New entries added: {inserted}")
    print(f"   ✓ Updated records: {updated}")
    print(f"   ✓ Total in the database: {get_total_records(db_name)}")
    print(f"{'='*70}")
    
    return inserted + updated


def get_total_records(db_name='ebay_products.db'):
    if not os.path.exists(db_name):
        return 0
    
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM products')
    count = cursor.fetchone()[0]
    conn.close()
    return count


def save_to_json(items_data, filename='ebay_results.json'):

    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(items_data, f, ensure_ascii=False, indent=2)
        print(f"✓ Data is stored in JSON: {filename}")
        return True
    except Exception as e:
        print(f"❌ Error saving JSON: {e}")
        return False


def load_and_save(items_data, search_query, save_json=True, save_db=True, 
                  json_filename='ebay_results.json', db_name='ebay_products.db'):

    stats = {
        'total_items': len(items_data),
        'json_saved': False,
        'db_records_saved': 0
    }
    
    print("\n" + "="*70)
    print("Saving data...")
    print("="*70)
    
    if save_json:
        stats['json_saved'] = save_to_json(items_data, json_filename)

    if save_db:
        create_database(db_name)
        stats['db_records_saved'] = save_to_database(items_data, search_query, db_name)
    
    return stats


if __name__ == "__main__":
    print("=" * 70)
    print("        EBAY LOADER - Saving data")
    print("=" * 70)
    print()
    
    import sys
    
    if len(sys.argv) > 1:
        json_file = sys.argv[1]
        search_query = sys.argv[2] if len(sys.argv) > 2 else 'unknown'
        
        print(f"Saving data from: {json_file}")
        with open(json_file, 'r', encoding='utf-8') as f:
            items_data = json.load(f)
        
        print(f"✓ Loaded {len(items_data)} records")

        create_database()
        save_to_database(items_data, search_query)
        
        print(f"\n✅ Done! Total in the database: {get_total_records()}")
    else:
        print("Usage: python loader.py <json_file> [search_query]")
        print("Example: python loader.py ebay_laptop_results.json laptop")