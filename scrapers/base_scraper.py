# scrapers/base_scraper.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any
import requests
from bs4 import BeautifulSoup
import time
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """Abstrakcyjna klasa bazowa dla scraperów"""
    
    def __init__(self, base_url: str, delay: float = 1.0):
        self.base_url = base_url
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    @abstractmethod
    def parse_listing(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Parsuje pojedyncze ogłoszenie"""
        pass
    
    @abstractmethod
    def get_listings_urls(self, page: int) -> List[str]:
        """Pobiera URLe ogłoszeń z danej strony"""
        pass
    
    def scrape_listing(self, url: str) -> Dict[str, Any]:
        """Scrapuje pojedyncze ogłoszenie"""
        try:
            response = self.session.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            listing_data = self.parse_listing(soup)
            listing_data['url'] = url
            listing_data['scraped_at'] = datetime.now().isoformat()
            
            return listing_data
            
        except Exception as e:
            logger.error(f"Błąd przy scrapowaniu {url}: {e}")
            return None
    
    def scrape_all(self, max_pages: int = 5) -> List[Dict[str, Any]]:
        """Scrapuje wszystkie ogłoszenia"""
        all_listings = []
        
        for page in range(1, max_pages + 1):
            logger.info(f"Scrapuję stronę {page}/{max_pages}")
            
            urls = self.get_listings_urls(page)
            
            for url in urls:
                listing = self.scrape_listing(url)
                if listing:
                    all_listings.append(listing)
                time.sleep(self.delay)
            
        return all_listings


