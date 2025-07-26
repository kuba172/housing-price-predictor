# main.py
import os
import sys
import pandas as pd
import json
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scrapers.otodom_scraper import OtodomScraper


def main():
    os.makedirs('data/raw', exist_ok=True)
    os.makedirs('data/processed', exist_ok=True)
    
    print("Inicjalizuję scraper Otodom...")
    scraper = OtodomScraper()
    
    print("Rozpoczynam scrapowanie...")
    print("To może potrwać kilka minut...")
    
    listings = scraper.scrape_all(max_pages=3)
    
    if listings:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        df = pd.DataFrame(listings)
        csv_path = f'data/raw/otodom_listings_{timestamp}.csv'
        df.to_csv(csv_path, index=False)
        print(f"\nZapisano {len(listings)} ogłoszeń do {csv_path}")
        
        json_path = f'data/raw/otodom_listings_{timestamp}.json'
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(listings, f, ensure_ascii=False, indent=2)
        print(f"Zapisano dane JSON do {json_path}")
        
        print("\n=== Podstawowe statystyki ===")
        print(f"Liczba ogłoszeń: {len(df)}")
        
        if 'price' in df.columns:
            print(f"Średnia cena: {df['price'].mean():,.0f} zł")
            print(f"Mediana ceny: {df['price'].median():,.0f} zł")
        
        if 'area' in df.columns:
            print(f"Średnia powierzchnia: {df['area'].mean():.1f} m²")
        
        if 'rooms' in df.columns:
            print(f"Rozkład liczby pokoi:")
            print(df['rooms'].value_counts().sort_index())
        
        df.to_csv('data/raw/otodom_latest.csv', index=False)
        
    else:
        print("Nie udało się pobrać żadnych ogłoszeń")
        print("Sprawdź czy strona Otodom jest dostępna i czy selektory CSS są aktualne")


if __name__ == "__main__":
    main()