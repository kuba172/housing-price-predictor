# scrapers/otodom_scraper.py
import re
import sys
import os
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
import json
import time

if __name__ == "__main__":
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from scrapers.base_scraper import BaseScraper
else:
    from .base_scraper import BaseScraper

import logging
logger = logging.getLogger(__name__)


class OtodomScraper(BaseScraper):
    """Scraper dla portalu Otodom"""
    
    def __init__(self):
        super().__init__(base_url="https://www.otodom.pl")
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'pl-PL,pl;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
    
    def get_listings_urls(self, page: int) -> List[str]:
        """Pobiera URLe ogłoszeń z listy wyników"""
        url = f"{self.base_url}/pl/wyniki/sprzedaz/mieszkanie/mazowieckie/warszawa?page={page}"
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            listings = []
            
            links = soup.find_all('a', {'data-cy': 'listing.link'})
            if not links:
                links = soup.find_all('a', href=re.compile(r'/pl/oferta/[^/]+$'))
            if not links:
                articles = soup.find_all('article')
                for article in articles:
                    link = article.find('a', href=re.compile(r'/oferta/'))
                    if link:
                        links.append(link)
            
            for link in links:
                href = link.get('href')
                if href:
                    full_url = self.base_url + href if href.startswith('/') else href
                    if '/oferta/' in full_url and full_url not in listings:
                        listings.append(full_url)
            
            logger.info(f"Znaleziono {len(listings)} ofert na stronie {page}")
            return listings[:36]
            
        except Exception as e:
            logger.error(f"Błąd przy pobieraniu listy ogłoszeń: {e}")
            return []
    
    def parse_parameters_block(self, text: str) -> Dict[str, Any]:
        """Parsuje blok parametrów z tekstu"""
        params = {}
        
        # Czynsz
        czynsz_match = re.search(r'Czynsz:\s*([^:]+?)(?=Stan|Rynek|Forma|$)', text)
        if czynsz_match:
            czynsz = czynsz_match.group(1).strip()
            if czynsz != 'brak informacji':
                try:
                    params['rent'] = int(re.sub(r'[^\d]', '', czynsz))
                except:
                    pass
        
        # Stan wykończenia
        stan_match = re.search(r'Stan wykończenia:\s*([^:]+?)(?=Rynek|Forma|Dostępne|$)', text)
        if stan_match:
            params['finish_state'] = stan_match.group(1).strip()
        
        # Rynek
        rynek_match = re.search(r'Rynek:\s*(pierwotny|wtórny)', text)
        if rynek_match:
            params['market'] = rynek_match.group(1)
        
        # Forma własności
        forma_match = re.search(r'Forma własności:\s*([^:]+?)(?=Dostępne|Typ|$)', text)
        if forma_match:
            params['ownership'] = forma_match.group(1).strip()
        
        # Typ ogłoszeniodawcy
        typ_match = re.search(r'Typ ogłoszeniodawcy:\s*([^:]+?)(?=Informacje|$)', text)
        if typ_match:
            params['advertiser_type'] = typ_match.group(1).strip()
        
        # Rok budowy
        rok_match = re.search(r'Rok budowy:\s*(\d{4})', text)
        if rok_match:
            params['year_built'] = int(rok_match.group(1))
        
        # Winda
        winda_match = re.search(r'Winda:\s*(tak|nie)', text)
        if winda_match:
            params['elevator'] = winda_match.group(1) == 'tak'
        
        # Rodzaj zabudowy
        zabudowa_match = re.search(r'Rodzaj zabudowy:\s*([^:]+?)(?=Materiał|Okna|$)', text)
        if zabudowa_match:
            params['building_type'] = zabudowa_match.group(1).strip()
        
        # Materiał budynku
        material_match = re.search(r'Materiał budynku:\s*([^:]+?)(?=Okna|Wyposażenie|$)', text)
        if material_match:
            params['building_material'] = material_match.group(1).strip()
        
        return params
    
    def parse_listing(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Parsuje dane z pojedynczego ogłoszenia"""
        data = {}
        
        try:
            # Tytuł
            title_elem = soup.find('h1')
            if title_elem:
                data['title'] = title_elem.text.strip()
            
            # Cena
            price_patterns = [
                r'(\d+[\s\d]*)\s*zł',
                r'PLN\s*(\d+[\s\d]*)',
                r'"price":\s*"?(\d+)"?',
                r'"amount":\s*(\d+)'
            ]
            
            page_text = str(soup)
            for pattern in price_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    price_str = match.group(1).replace(' ', '').replace('\xa0', '')
                    try:
                        data['price'] = int(price_str)
                        break
                    except ValueError:
                        continue
            
            # Szukamy głównego bloku z parametrami
            main_text = soup.get_text()
            
            # Powierzchnia
            area_match = re.search(r'(\d+[,.]?\d*)\s*m[²2]', main_text)
            if area_match:
                data['area'] = float(area_match.group(1).replace(',', '.'))
            
            # Liczba pokoi
            rooms_patterns = [
                r'(\d+)-pokojowe',
                r'(\d+)\s*poko[ij]',
                r'Liczba pokoi:\s*(\d+)'
            ]
            for pattern in rooms_patterns:
                rooms_match = re.search(pattern, main_text, re.IGNORECASE)
                if rooms_match:
                    data['rooms'] = int(rooms_match.group(1))
                    break
            
            # Kawalerka = 1 pokój
            if 'rooms' not in data and re.search(r'kawalerka', main_text, re.IGNORECASE):
                data['rooms'] = 1
            
            # Piętro - tylko pierwsza wartość przed "/"
            floor_patterns = [
                r'piętro[:\s]*([^/\s]+)(?:/|$)',
                r'(\d+|parter|suterena)/\d+',
                r'Piętro:\s*([^/\n]+)'
            ]
            
            for pattern in floor_patterns:
                floor_match = re.search(pattern, main_text, re.IGNORECASE)
                if floor_match:
                    floor_value = floor_match.group(1).strip()
                    if floor_value and floor_value != 'brak informacji':
                        data['floor'] = floor_value
                        break
            
            # Parsowanie bloku parametrów
            params_start = main_text.find('Czynsz:')
            if params_start == -1:
                params_start = main_text.find('Stan wykończenia:')
            
            if params_start != -1:
                params_end = main_text.find('OpisPokaż więcej', params_start)
                if params_end == -1:
                    params_end = main_text.find('ID:', params_start)
                
                if params_end != -1:
                    params_text = main_text[params_start:params_end]
                    parsed_params = self.parse_parameters_block(params_text)
                    data.update(parsed_params)
            
            # Lokalizacja z meta description
            meta_desc = soup.find('meta', {'name': 'description'})
            if meta_desc:
                desc_content = meta_desc.get('content', '')
                # Szukamy ulicy
                street_match = re.search(r'ul\.\s*([^,]+)', desc_content)
                city_match = re.search(r'w miejscowości\s+([^,]+)', desc_content)
                
                if street_match and city_match:
                    data['address'] = f"{street_match.group(0)}, {city_match.group(1)}"
                elif city_match:
                    # Szukamy dzielnicy
                    district_match = re.search(r',\s*([^,]+)$', desc_content)
                    if district_match:
                        data['address'] = f"{city_match.group(1)}, {district_match.group(1)}"
                    else:
                        data['address'] = city_match.group(1)
            
            # Wyposażenie i features
            features = []
            
            # Informacje dodatkowe
            info_match = re.search(r'Informacje dodatkowe:\s*([^:]+?)(?=Budynek|$)', main_text)
            if info_match:
                info_items = info_match.group(1).strip().split()
                features.extend([item.strip() for item in info_items if item.strip()])
            
            # Wyposażenie
            wypos_match = re.search(r'Wyposażenie:\s*([^:]+?)(?=Zabezpieczenia|Media|Opis|$)', main_text)
            if wypos_match:
                wypos_items = wypos_match.group(1).strip().split()
                features.extend([item.strip() for item in wypos_items if item.strip()])
            
            # Media
            media_match = re.search(r'Media:\s*([^:]+?)(?=Opis|$)', main_text)
            if media_match:
                media_items = media_match.group(1).strip().split()
                features.extend([item.strip() for item in media_items if item.strip()])
            
            data['features'] = list(set(features))  # Usuń duplikaty
            
            # Opis
            opis_start = main_text.find('OpisPokaż więcej')
            if opis_start != -1:
                opis_end = main_text.find('ID:', opis_start)
                if opis_end != -1:
                    opis_text = main_text[opis_start+16:opis_end].strip()
                    if len(opis_text) > 10:
                        data['description'] = opis_text
            
            logger.info(f"Sparsowano: {len([v for v in data.values() if v])} pól danych")
            
        except Exception as e:
            logger.error(f"Błąd przy parsowaniu ogłoszenia: {e}")
            
        return data


if __name__ == "__main__":
    import pandas as pd
    import json
    
    os.makedirs('../data/raw', exist_ok=True)
    
    print("Testowanie zaktualizowanego scrapera Otodom v3...")
    scraper = OtodomScraper()
    
    print("\nPobieranie listy ofert...")
    test_urls = scraper.get_listings_urls(1)
    
    if test_urls:
        print(f"Znaleziono {len(test_urls)} ofert")
        
        test_results = []
        for i, url in enumerate(test_urls[:5]):
            print(f"\nTestowanie oferty {i+1}/5: {url}")
            result = scraper.scrape_listing(url)
            if result:
                print("Znalezione dane:")
                for key, value in result.items():
                    if key not in ['description', 'features', 'url', 'scraped_at']:
                        print(f"  {key}: {value}")
                if result.get('features'):
                    print(f"  features ({len(result['features'])}): {', '.join(result['features'][:5])}...")
                test_results.append(result)
            time.sleep(2)
        
        if test_results:
            with open('../data/raw/test_results_v3.json', 'w', encoding='utf-8') as f:
                json.dump(test_results, f, ensure_ascii=False, indent=2)
            print("\nWyniki zapisane do test_results_v3.json")
            
            df = pd.DataFrame(test_results)
            print("\n=== KOMPLETNOŚĆ DANYCH ===")
            for col in ['price', 'area', 'rooms', 'floor', 'address', 'market', 'finish_state', 'year_built']:
                if col in df.columns:
                    count = df[col].notna().sum()
                    pct = (count / len(df)) * 100
                    print(f"{col}: {count}/{len(df)} ({pct:.0f}%)")
    else:
        print("Nie udało się pobrać URLi ofert")