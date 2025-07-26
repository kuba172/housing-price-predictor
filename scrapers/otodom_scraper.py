# scrapers/otodom_scraper.py
import re
from typing import List, Dict, Any
from bs4 import BeautifulSoup
from .base_scraper import BaseScraper


class OtodomScraper(BaseScraper):
    """Scraper dla portalu Otodom"""
    
    def __init__(self):
        super().__init__(base_url="https://www.otodom.pl")
    
    def get_listings_urls(self, page: int) -> List[str]:
        """Pobiera URLe ogłoszeń z listy wyników"""
        url = f"{self.base_url}/pl/wyniki/sprzedaz/mieszkanie/mazowieckie/warszawa?page={page}"
        
        try:
            response = self.session.get(url)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            listings = []
            for link in soup.select('a[data-cy="listing-item-link"]'):
                href = link.get('href')
                if href:
                    full_url = self.base_url + href if href.startswith('/') else href
                    listings.append(full_url)
            
            return listings
            
        except Exception as e:
            logger.error(f"Błąd przy pobieraniu listy ogłoszeń: {e}")
            return []
    
    def parse_listing(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Parsuje dane z pojedynczego ogłoszenia"""
        data = {}
        
        try:
            price_elem = soup.select_one('strong[data-cy="adPageHeaderPrice"]')
            if price_elem:
                price_text = price_elem.text.strip()
                price = int(re.sub(r'[^\d]', '', price_text))
                data['price'] = price
            
            for item in soup.select('div[data-testid="table-value-item"]'):
                label = item.select_one('p')
                value = item.select_one('strong')
                
                if label and value:
                    label_text = label.text.strip().lower()
                    value_text = value.text.strip()
                    
                    if 'powierzchnia' in label_text:
                        data['area'] = float(re.sub(r'[^\d,.]', '', value_text).replace(',', '.'))
                    elif 'liczba pokoi' in label_text:
                        data['rooms'] = int(re.sub(r'[^\d]', '', value_text))
                    elif 'piętro' in label_text:
                        data['floor'] = value_text
                    elif 'rok budowy' in label_text:
                        data['year_built'] = int(re.sub(r'[^\d]', '', value_text))
            
            location_elem = soup.select_one('a[aria-label="Adres"]')
            if location_elem:
                data['address'] = location_elem.text.strip()
            
            title_elem = soup.select_one('h1[data-cy="adPageAdTitle"]')
            if title_elem:
                data['title'] = title_elem.text.strip()
            
            description_elem = soup.select_one('div[data-cy="adPageAdDescription"]')
            if description_elem:
                data['description'] = description_elem.text.strip()
            
            features = []
            for feature in soup.select('li[data-cy="ad-details-equipment-item"]'):
                features.append(feature.text.strip())
            data['features'] = features
            
            return data
            
        except Exception as e:
            logger.error(f"Błąd przy parsowaniu ogłoszenia: {e}")
            return data


if __name__ == "__main__":
    from scrapers.otodom_scraper import OtodomScraper
    import pandas as pd
    import json
    
    scraper = OtodomScraper()
    
    print("Rozpoczynam scrapowanie...")
    listings = scraper.scrape_all(max_pages=3)
    
    if listings:
        df = pd.DataFrame(listings)
        df.to_csv('data/raw/otodom_listings.csv', index=False)
        print(f"Zapisano {len(listings)} ogłoszeń do pliku CSV")
        
        with open('data/raw/otodom_listings.json', 'w', encoding='utf-8') as f:
            json.dump(listings, f, ensure_ascii=False, indent=2)
    else:
        print("Nie udało się pobrać żadnych ogłoszeń")