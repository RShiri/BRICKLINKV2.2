from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from bs4 import BeautifulSoup, Tag
from typing import Dict, Any, List
import re
from datetime import datetime
from database import Database
import logging

class BrickLinkScraperV2:
    """
    Playwright-based BrickLink scraper (more stable than Selenium).
    Handles browser binaries automatically, better anti-detection, faster performance.
    """
    BASE_URL = "https://www.bricklink.com/v2/catalog/catalogitem.page"
    INV_URL = "https://www.bricklink.com/catalogItemInv.asp"

    def __init__(self):
        self.db = Database()
        self.current_type = 'S'
        self.playwright = None
        self.browser = None
        self.context = None
        self._init_browser()

    def _init_browser(self):
        """Initializes Playwright browser with anti-detection settings."""
        if self.playwright:
            return
            
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=True,
            args=['--disable-blink-features=AutomationControlled']
        )
        self.context = self.browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        )

    def close(self):
        """Closes the persistent browser."""
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        self.playwright = None
        self.browser = None
        self.context = None

    def get_minifigs_in_set(self, set_id: str, force: bool = False) -> List[Dict]:
        """Scrapes minifigure inventory for a set."""
        cached_data, timestamp = self.db.get_inventory(set_id)
        if not force and cached_data:
            return cached_data
        
        page = self.context.new_page()
        minifigs_dict = {}
        
        try:
            url = f"{self.INV_URL}?S={set_id if '-' in set_id else f'{set_id}-1'}&viewItemType=M"
            page.goto(url, wait_until='domcontentloaded', timeout=30000)
            page.wait_for_selector("table", timeout=15000)
            
            html = page.content()
            soup = BeautifulSoup(html, 'html.parser')
            
            for row in soup.find_all('tr'):
                mf_link = row.find('a', href=re.compile(r'\?M='))
                if mf_link:
                    mf_id = mf_link.get('href').split('?M=')[1].split('&')[0]
                    if mf_id not in minifigs_dict:
                        minifigs_dict[mf_id] = {
                            'id': mf_id,
                            'name': mf_link.get_text(strip=True),
                            'qty': 1
                        }
            
            res = list(minifigs_dict.values())
            self.db.save_inventory(set_id, res)
            return res
            
        except PlaywrightTimeout:
            logging.error(f"Timeout loading inventory for {set_id}")
            return []
        except Exception as e:
            logging.error(f"Inventory Error for {set_id}: {e}")
            return []
        finally:
            page.close()

    def scrape(self, item_id: str, item_type: str = 'S', force: bool = False) -> Dict[str, Any]:
        """Scrapes BrickLink price data for an item."""
        self.current_type = item_type
        
        if not force:
            cached = self.db.get_item(item_id)
            if cached:
                return cached

        page = self.context.new_page()
        
        try:
            url = f"{self.BASE_URL}?{item_type}={item_id}#T=P"
            page.goto(url, wait_until='networkidle', timeout=30000)
            
            # Wait for price tables to load
            page.wait_for_selector(".pcipgInnerTable", timeout=20000)
            
            # Wait for real data (not placeholders)
            page.wait_for_function(
                "() => document.body.innerText.toLowerCase().includes('ils') || document.body.innerText.includes('~')",
                timeout=15000
            )
            
            # Get HTML and parse
            html = page.content()
            data = self._parse_html(item_id, html)
            
            self.db.save_item(item_id, data)
            return data
            
        except PlaywrightTimeout:
            logging.error(f"Timeout loading {item_id}")
            return {"error": "Timeout waiting for page load"}
        except Exception as e:
            logging.error(f"Scrape error for {item_id}: {e}")
            return {"error": str(e)}
        finally:
            page.close()

    def _parse_html(self, item_id: str, html: str) -> Dict[str, Any]:
        """Parses BrickLink HTML to extract price data."""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract item name and year
        item_name = "Unknown"
        title_tag = soup.find('h1', id='item-name-title') or soup.find('title')
        if title_tag:
            item_name = title_tag.get_text().split(":")[0].strip()
        
        year = None
        year_match = re.search(r'Year Released\D*(\d{4})', soup.get_text())
        if year_match:
            year = int(year_match.group(1))

        data = {
            "meta": {
                "item_id": item_id,
                "item_name": item_name,
                "year_released": year,
                "specs": self._extract_specs(soup),
                "timestamp": datetime.now().isoformat()
            },
            "new": {"sold": [], "stock": []},
            "used": {"sold": [], "stock": []}
        }

        tables = soup.find_all('table', class_='pcipgInnerTable')
        if len(tables) >= 4:
            data["new"]["sold"] = self._extract_rows(tables[0], "sold")
            data["used"]["sold"] = self._extract_rows(tables[1], "sold")
            data["new"]["stock"] = self._extract_rows(tables[2], "stock")
            data["used"]["stock"] = self._extract_rows(tables[3], "stock")
        
        return data

    def _extract_specs(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extracts item specifications (weight, parts, minifigs)."""
        text = soup.get_text()
        specs = {"weight_g": 0, "parts": 0, "minifigs": 0}
        
        # Weight
        w_match = re.search(r'Weight:\s*([\d.]+)\s*g', text)
        if w_match:
            specs["weight_g"] = float(w_match.group(1))
        
        # Parts
        p_match = re.search(r'(\d+)\s*Parts', text)
        if p_match:
            specs["parts"] = int(p_match.group(1))
        
        # Minifigs
        m_match = re.search(r'(\d+)\s*Minifig', text)
        if m_match:
            specs["minifigs"] = int(m_match.group(1))
        
        return specs

    def _extract_rows(self, table: Tag, table_type: str) -> List[Dict]:
        """Extracts price rows from a table with currency conversion."""
        rows = []
        
        for tr in table.find_all('tr'):
            tds = tr.find_all('td')
            if len(tds) < 2:
                continue
            
            # Check for incomplete status
            is_inc = False
            if tr.find(class_="js-item-status-incomplete") or "(i)" in tr.get_text().lower():
                is_inc = True

            try:
                # Extract price and quantity based on table type
                q_idx, p_idx = (-2, -1) if table_type == "sold" else (1, 2)
                p_text = tds[p_idx].get_text(strip=True).replace(',', '')
                
                # Currency Detection and Conversion
                rate = 1.0
                p_upper = p_text.upper()
                
                CURRENCY_RATES = {
                    'US': 3.20, 'USD': 3.20, '$': 3.20,
                    'EU': 3.95, 'EUR': 3.95, '€': 3.95,
                    'GB': 4.65, 'GBP': 4.65, '£': 4.65,
                    'CA': 2.60, 'CAD': 2.60,
                    'AU': 2.35, 'AUD': 2.35,
                    'IL': 1.00, 'ILS': 1.00, '₪': 1.00 
                }

                # Specific checks (longer strings first)
                if 'ILS' in p_upper or '₪' in p_upper:
                    rate = 1.0
                elif 'US' in p_upper:
                    rate = CURRENCY_RATES['US']
                elif 'CA' in p_upper:
                    rate = CURRENCY_RATES['CA']
                elif 'AU' in p_upper:
                    rate = CURRENCY_RATES['AU']
                elif 'EU' in p_upper or '€' in p_upper:
                    rate = CURRENCY_RATES['EU']
                elif 'GB' in p_upper or '£' in p_upper:
                    rate = CURRENCY_RATES['GB']
                elif '$' in p_upper:
                    rate = CURRENCY_RATES['$']
                
                raw_val = float(re.sub(r'[^\d.]', '', p_text))
                final_price = raw_val * rate

                rows.append({
                    'qty': int(re.sub(r'[^\d]', '', tds[q_idx].get_text(strip=True))),
                    'price': round(final_price, 2),
                    'currency': 'ILS',
                    'status': "incomplete" if is_inc else "complete"
                })
            except:
                continue
        
        return rows
