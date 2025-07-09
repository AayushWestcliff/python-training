"""
Manual Login + Auto Scraper
===========================

This script opens a website, waits for you to manually enter credentials,
then automatically scrapes data and saves it to text files.

Perfect for:
- Sites with complex authentication
- Two-factor authentication
- Sites that block automated login
- When you want manual control over login process

Requirements:
pip install selenium webdriver-manager beautifulsoup4
"""

import time
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
import json
import csv

class ManualLoginScraper:
    def __init__(self, headless=False):
        """Initialize the scraper with browser setup"""
        self.setup_driver(headless)
        self.data_folder = "scraped_data"
        self.create_data_folder()
        
    def setup_driver(self, headless=False):
        """Set up Chrome driver"""
        print("🚀 Setting up browser...")
        
        chrome_options = Options()
        if headless:
            chrome_options.add_argument('--headless')
        
        # Keep browser open and visible for manual interaction
        chrome_options.add_argument('--window-size=1200,800')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Hide webdriver property
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        print("✅ Browser ready!")
        
    def create_data_folder(self):
        """Create folder for scraped data"""
        if not os.path.exists(self.data_folder):
            os.makedirs(self.data_folder)
            print(f"📁 Created data folder: {self.data_folder}")
            
    def open_website(self, url):
        """Open the target website"""
        print(f"🌐 Opening website: {url}")
        self.driver.get(url)
        print("✅ Website opened successfully!")
        
    def wait_for_manual_login(self, success_indicator=None, timeout=300):
        """
        Wait for user to manually complete login process
        
        Args:
            success_indicator: CSS selector or element that indicates successful login
            timeout: Maximum time to wait (default 5 minutes)
        """
        print("\n" + "="*50)
        print("🔐 MANUAL LOGIN REQUIRED")
        print("="*50)
        print("Please complete the login process manually in the browser window.")
        print("This script will wait for you to finish logging in.")
        
        if success_indicator:
            print(f"Looking for login success indicator: {success_indicator}")
        else:
            print("Press Enter in this console when you've successfully logged in...")
            
        print("="*50)
        
        if success_indicator:
            # Wait for specific element that indicates successful login
            try:
                print(f"⏳ Waiting for login completion (timeout: {timeout}s)...")
                WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, success_indicator))
                )
                print("✅ Login detected successfully!")
                return True
            except TimeoutException:
                print("⏰ Timeout waiting for login. Continuing anyway...")
                return False
        else:
            # Wait for user confirmation
            input("⏳ Press Enter after you've completed the login process...")
            print("✅ Continuing with scraping...")
            return True
            
    def scrape_generic_data(self):
        """
        Generic scraper that extracts common data types from any website
        """
        print("\n🔍 Starting data scraping...")
        
        scraped_data = {
            'timestamp': datetime.now().isoformat(),
            'url': self.driver.current_url,
            'title': self.driver.title,
            'data': {}
        }
        
        # Get page source and parse with BeautifulSoup
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        
        # Extract different types of data
        data_types = {
            'headings': self.extract_headings(soup),
            'paragraphs': self.extract_paragraphs(soup),
            'links': self.extract_links(soup),
            'images': self.extract_images(soup),
            'tables': self.extract_tables(soup),
            'forms': self.extract_forms(soup),
            'lists': self.extract_lists(soup)
        }
        
        # Filter out empty data
        for data_type, data_content in data_types.items():
            if data_content:
                scraped_data['data'][data_type] = data_content
                print(f"✅ Extracted {len(data_content)} {data_type}")
            else:
                print(f"⚠️  No {data_type} found")
                
        return scraped_data
        
    def extract_headings(self, soup):
        """Extract all headings (h1-h6)"""
        headings = []
        for i in range(1, 7):
            for heading in soup.find_all(f'h{i}'):
                text = heading.get_text(strip=True)
                if text:
                    headings.append({
                        'level': i,
                        'text': text
                    })
        return headings
        
    def extract_paragraphs(self, soup):
        """Extract paragraph text"""
        paragraphs = []
        for p in soup.find_all('p'):
            text = p.get_text(strip=True)
            if text and len(text) > 10:  # Filter out very short paragraphs
                paragraphs.append(text)
        return paragraphs
        
    def extract_links(self, soup):
        """Extract all links"""
        links = []
        for link in soup.find_all('a', href=True):
            text = link.get_text(strip=True)
            href = link['href']
            if text and href:
                links.append({
                    'text': text,
                    'url': href
                })
        return links
        
    def extract_images(self, soup):
        """Extract image information"""
        images = []
        for img in soup.find_all('img'):
            src = img.get('src')
            alt = img.get('alt', '')
            if src:
                images.append({
                    'src': src,
                    'alt': alt
                })
        return images
        
    def extract_tables(self, soup):
        """Extract table data"""
        tables = []
        for table in soup.find_all('table'):
            rows = []
            for row in table.find_all('tr'):
                cells = [cell.get_text(strip=True) for cell in row.find_all(['td', 'th'])]
                if cells:
                    rows.append(cells)
            if rows:
                tables.append(rows)
        return tables
        
    def extract_forms(self, soup):
        """Extract form information"""
        forms = []
        for form in soup.find_all('form'):
            form_data = {
                'action': form.get('action', ''),
                'method': form.get('method', ''),
                'fields': []
            }
            
            for input_field in form.find_all(['input', 'textarea', 'select']):
                field_info = {
                    'type': input_field.get('type', input_field.name),
                    'name': input_field.get('name', ''),
                    'id': input_field.get('id', ''),
                    'placeholder': input_field.get('placeholder', '')
                }
                form_data['fields'].append(field_info)
                
            if form_data['fields']:
                forms.append(form_data)
        return forms
        
    def extract_lists(self, soup):
        """Extract list items"""
        lists = []
        for ul in soup.find_all(['ul', 'ol']):
            items = [li.get_text(strip=True) for li in ul.find_all('li')]
            if items:
                lists.append({
                    'type': ul.name,
                    'items': items
                })
        return lists
        
    def save_to_text_file(self, data, filename_prefix="scraped_data"):
        """Save scraped data to text file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{filename_prefix}_{timestamp}.txt"
        filepath = os.path.join(self.data_folder, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"Scraped Data Report\n")
            f.write(f"==================\n\n")
            f.write(f"URL: {data['url']}\n")
            f.write(f"Title: {data['title']}\n")
            f.write(f"Timestamp: {data['timestamp']}\n\n")
            
            for data_type, content in data['data'].items():
                f.write(f"\n{data_type.upper()}\n")
                f.write("-" * len(data_type) + "\n")
                
                if data_type == 'headings':
                    for heading in content:
                        f.write(f"H{heading['level']}: {heading['text']}\n")
                        
                elif data_type == 'paragraphs':
                    for i, paragraph in enumerate(content, 1):
                        f.write(f"Paragraph {i}: {paragraph}\n\n")
                        
                elif data_type == 'links':
                    for link in content:
                        f.write(f"Link: {link['text']} -> {link['url']}\n")
                        
                elif data_type == 'images':
                    for img in content:
                        f.write(f"Image: {img['src']} (Alt: {img['alt']})\n")
                        
                elif data_type == 'tables':
                    for i, table in enumerate(content, 1):
                        f.write(f"Table {i}:\n")
                        for row in table:
                            f.write(f"  {' | '.join(row)}\n")
                        f.write("\n")
                        
                elif data_type == 'forms':
                    for i, form in enumerate(content, 1):
                        f.write(f"Form {i} - Action: {form['action']}, Method: {form['method']}\n")
                        for field in form['fields']:
                            f.write(f"  Field: {field['type']} - {field['name']}\n")
                        f.write("\n")
                        
                elif data_type == 'lists':
                    for i, lst in enumerate(content, 1):
                        f.write(f"List {i} ({lst['type']}):\n")
                        for item in lst['items']:
                            f.write(f"  - {item}\n")
                        f.write("\n")
                        
                f.write("\n")
                
        print(f"💾 Data saved to: {filepath}")
        return filepath
        
    def save_to_json(self, data, filename_prefix="scraped_data"):
        """Save scraped data to JSON file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{filename_prefix}_{timestamp}.json"
        filepath = os.path.join(self.data_folder, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
        print(f"💾 JSON data saved to: {filepath}")
        return filepath
        
    def save_to_csv(self, data, filename_prefix="scraped_data"):
        """Save scraped data to CSV file (for tabular data)"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{filename_prefix}_{timestamp}.csv"
        filepath = os.path.join(self.data_folder, filename)
        
        # Extract tables for CSV format
        if 'tables' in data['data']:
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Table', 'Row', 'Data'])
                
                for table_idx, table in enumerate(data['data']['tables']):
                    for row_idx, row in enumerate(table):
                        writer.writerow([f"Table_{table_idx+1}", f"Row_{row_idx+1}", ' | '.join(row)])
                        
            print(f"💾 CSV data saved to: {filepath}")
            return filepath
        else:
            print("⚠️  No table data found for CSV export")
            return None
            
    def custom_scraper(self, selectors):
        """
        Custom scraper for specific elements
        
        Args:
            selectors: Dictionary of CSS selectors to scrape
                      Example: {'prices': '.price', 'titles': '.title'}
        """
        print("\n🎯 Running custom scraper...")
        
        custom_data = {}
        
        for name, selector in selectors.items():
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                data = [elem.text.strip() for elem in elements if elem.text.strip()]
                custom_data[name] = data
                print(f"✅ Found {len(data)} {name}")
            except Exception as e:
                print(f"❌ Error scraping {name}: {str(e)}")
                custom_data[name] = []
                
        return custom_data
        
    def run_scraper(self, url, success_indicator=None, custom_selectors=None):
        """
        Main method to run the complete scraping process
        
        Args:
            url: Website URL to scrape
            success_indicator: CSS selector that indicates successful login
            custom_selectors: Dictionary of custom CSS selectors to scrape
        """
        try:
            # Open website
            self.open_website(url)
            
            # Wait for manual login
            login_success = self.wait_for_manual_login(success_indicator)
            
            if not login_success:
                print("⚠️  Login may not have completed successfully, but continuing...")
                
            # Wait a bit for page to load after login
            time.sleep(3)
            
            # Scrape generic data
            scraped_data = self.scrape_generic_data()
            
            # Run custom scraper if provided
            if custom_selectors:
                custom_data = self.custom_scraper(custom_selectors)
                scraped_data['custom_data'] = custom_data
                
            # Save data in multiple formats
            self.save_to_text_file(scraped_data)
            self.save_to_json(scraped_data)
            self.save_to_csv(scraped_data)
            
            print(f"\n✅ Scraping completed successfully!")
            print(f"📁 All files saved in: {self.data_folder}")
            
            return scraped_data
            
        except Exception as e:
            print(f"❌ Error during scraping: {str(e)}")
            return None
            
    def keep_browser_open(self):
        """Keep browser open for manual inspection"""
        print("\n🔍 Browser will remain open for manual inspection...")
        input("Press Enter to close browser and exit...")
        
    def close(self):
        """Close the browser"""
        print("🔧 Closing browser...")
        self.driver.quit()
        print("✅ Browser closed!")


def main():
    """Main function with user interaction"""
    print("🤖 Manual Login + Auto Scraper")
    print("=" * 40)
    
    # Get URL from user
    url = input("Enter the website URL: ").strip()
    if not url:
        print("❌ No URL provided!")
        return
        
    # Optional: success indicator
    success_indicator = input("Enter CSS selector for login success (optional): ").strip()
    if not success_indicator:
        success_indicator = None
        
    # Optional: custom selectors
    print("\n📝 Custom selectors (optional):")
    print("Enter CSS selectors for specific data you want to scrape.")
    print("Format: name:selector (e.g., prices:.price)")
    print("Enter 'done' when finished, or press Enter to skip.")
    
    custom_selectors = {}
    while True:
        selector_input = input("Enter selector (or 'done'): ").strip()
        if selector_input.lower() == 'done' or not selector_input:
            break
            
        if ':' in selector_input:
            name, selector = selector_input.split(':', 1)
            custom_selectors[name.strip()] = selector.strip()
            print(f"✅ Added: {name.strip()} -> {selector.strip()}")
        else:
            print("❌ Invalid format. Use: name:selector")
            
    # Create scraper instance
    scraper = ManualLoginScraper()
    
    try:
        # Run the scraper
        result = scraper.run_scraper(
            url=url,
            success_indicator=success_indicator,
            custom_selectors=custom_selectors if custom_selectors else None
        )
        
        if result:
            # Ask if user wants to keep browser open
            keep_open = input("\nKeep browser open for inspection? (y/n): ").strip().lower()
            if keep_open == 'y':
                scraper.keep_browser_open()
                
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    finally:
        scraper.close()


if __name__ == "__main__":
    main()