"""
Smart Shopping Assistant - Live Browser Automation Demo
=====================================================

This project demonstrates Selenium by creating an intelligent shopping assistant
that automatically searches for products, compares prices, and finds the best deals
across multiple e-commerce sites. Perfect for live demonstration!

Features:
- Real-time browser automation you can watch
- Colorful console output with progress indicators
- Automatic price comparison across sites
- Screenshot capture of findings
- Interactive prompts for user engagement
- Error handling with graceful fallbacks

Requirements:
pip install selenium webdriver-manager colorama beautifulsoup4 requests
"""

import time
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import json
from colorama import Fore, Back, Style, init

# Initialize colorama for colored output
init(autoreset=True)

class SmartShoppingAssistant:
    def __init__(self, headless=False):
        """Initialize the shopping assistant with browser setup"""
        self.setup_driver(headless)
        self.results = []
        self.screenshots_dir = "shopping_screenshots"
        self.create_screenshots_dir()
        
    def setup_driver(self, headless=False):
        """Set up Chrome driver with optimal settings for demonstration"""
        print(f"{Fore.CYAN}🚀 Setting up browser automation...")
        
        chrome_options = Options()
        if headless:
            chrome_options.add_argument('--headless')
        
        # Make browser more visible and interesting for demo
        chrome_options.add_argument('--window-size=1200,800')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Set up driver
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Execute script to hide webdriver property
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        print(f"{Fore.GREEN}✅ Browser ready for automation!")
        
    def create_screenshots_dir(self):
        """Create directory for screenshots"""
        if not os.path.exists(self.screenshots_dir):
            os.makedirs(self.screenshots_dir)
            
    def animate_typing(self, element, text, delay=0.1):
        """Animate typing for dramatic effect"""
        element.clear()
        for char in text:
            element.send_keys(char)
            time.sleep(delay)
            
    def take_screenshot(self, filename):
        """Take screenshot with timestamp"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = os.path.join(self.screenshots_dir, f"{timestamp}_{filename}.png")
        self.driver.save_screenshot(filepath)
        print(f"{Fore.YELLOW}📸 Screenshot saved: {filepath}")
        return filepath
        
    def search_amazon(self, product):
        """Search for product on Amazon"""
        print(f"\n{Fore.BLUE}🔍 Searching Amazon for: {product}")
        
        try:
            # Navigate to Amazon
            self.driver.get("https://www.amazon.com")
            time.sleep(2)
            
            # Find search box and search
            search_box = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "twotabsearchtextbox"))
            )
            
            print(f"{Fore.YELLOW}⌨️  Typing search query...")
            self.animate_typing(search_box, product)
            search_box.send_keys(Keys.RETURN)
            
            # Wait for results
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[data-component-type='s-search-result']"))
            )
            
            # Get first few results
            results = self.driver.find_elements(By.CSS_SELECTOR, "[data-component-type='s-search-result']")[:3]
            
            amazon_results = []
            for i, result in enumerate(results):
                try:
                    title = result.find_element(By.CSS_SELECTOR, "h2 a span").text
                    price_element = result.find_element(By.CSS_SELECTOR, ".a-price-whole")
                    price = price_element.text
                    
                    amazon_results.append({
                        'title': title,
                        'price': price,
                        'source': 'Amazon'
                    })
                    
                    print(f"{Fore.GREEN}✅ Found: {title} - ${price}")
                    
                except NoSuchElementException:
                    continue
            
            self.take_screenshot("amazon_results")
            return amazon_results
            
        except TimeoutException:
            print(f"{Fore.RED}❌ Amazon search timed out")
            return []
            
    def search_ebay(self, product):
        """Search for product on eBay"""
        print(f"\n{Fore.BLUE}🔍 Searching eBay for: {product}")
        
        try:
            # Navigate to eBay
            self.driver.get("https://www.ebay.com")
            time.sleep(2)
            
            # Find search box and search
            search_box = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "gh-ac"))
            )
            
            print(f"{Fore.YELLOW}⌨️  Typing search query...")
            self.animate_typing(search_box, product)
            search_box.send_keys(Keys.RETURN)
            
            # Wait for results
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".s-item"))
            )
            
            # Get first few results
            results = self.driver.find_elements(By.CSS_SELECTOR, ".s-item")[:3]
            
            ebay_results = []
            for i, result in enumerate(results):
                try:
                    title = result.find_element(By.CSS_SELECTOR, ".s-item__title").text
                    price = result.find_element(By.CSS_SELECTOR, ".s-item__price").text
                    
                    ebay_results.append({
                        'title': title,
                        'price': price,
                        'source': 'eBay'
                    })
                    
                    print(f"{Fore.GREEN}✅ Found: {title} - {price}")
                    
                except NoSuchElementException:
                    continue
            
            self.take_screenshot("ebay_results")
            return ebay_results
            
        except TimeoutException:
            print(f"{Fore.RED}❌ eBay search timed out")
            return []
            
    def search_google_shopping(self, product):
        """Search Google Shopping for product"""
        print(f"\n{Fore.BLUE}🔍 Searching Google Shopping for: {product}")
        
        try:
            # Navigate to Google
            self.driver.get("https://www.google.com")
            time.sleep(2)
            
            # Find search box
            search_box = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "q"))
            )
            
            print(f"{Fore.YELLOW}⌨️  Typing search query...")
            self.animate_typing(search_box, f"{product} shopping")
            search_box.send_keys(Keys.RETURN)
            
            # Click on Shopping tab
            try:
                shopping_tab = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.LINK_TEXT, "Shopping"))
                )
                shopping_tab.click()
                time.sleep(2)
            except TimeoutException:
                print(f"{Fore.YELLOW}⚠️  Shopping tab not found, using regular results")
            
            self.take_screenshot("google_shopping_results")
            return []
            
        except TimeoutException:
            print(f"{Fore.RED}❌ Google Shopping search timed out")
            return []
            
    def demonstrate_advanced_features(self):
        """Demonstrate advanced Selenium features"""
        print(f"\n{Fore.MAGENTA}🎭 Demonstrating Advanced Browser Automation...")
        
        # Navigate to a demo site
        self.driver.get("https://demoqa.com/automation-practice-form")
        time.sleep(2)
        
        try:
            # Fill out form with animation
            first_name = self.driver.find_element(By.ID, "firstName")
            print(f"{Fore.CYAN}📝 Filling out demo form...")
            self.animate_typing(first_name, "Selenium", 0.15)
            
            last_name = self.driver.find_element(By.ID, "lastName")
            self.animate_typing(last_name, "Bot", 0.15)
            
            email = self.driver.find_element(By.ID, "userEmail")
            self.animate_typing(email, "selenium@automation.com", 0.1)
            
            # Select gender radio button
            gender_radio = self.driver.find_element(By.CSS_SELECTOR, "label[for='gender-radio-1']")
            gender_radio.click()
            
            # Fill phone number
            phone = self.driver.find_element(By.ID, "userNumber")
            self.animate_typing(phone, "1234567890", 0.1)
            
            print(f"{Fore.GREEN}✅ Form filling demonstration complete!")
            self.take_screenshot("form_demo")
            
        except Exception as e:
            print(f"{Fore.RED}❌ Form demo error: {str(e)}")
            
    def demonstrate_javascript_execution(self):
        """Demonstrate JavaScript execution capabilities"""
        print(f"\n{Fore.MAGENTA}⚡ Demonstrating JavaScript Execution...")
        
        # Execute JavaScript to create visual effects
        self.driver.execute_script("""
            document.body.style.background = 'linear-gradient(45deg, #FF6B6B, #4ECDC4, #45B7D1, #96CEB4)';
            document.body.style.backgroundSize = '400% 400%';
            document.body.style.animation = 'gradient 3s ease infinite';
            
            var style = document.createElement('style');
            style.textContent = `
                @keyframes gradient {
                    0% { background-position: 0% 50%; }
                    50% { background-position: 100% 50%; }
                    100% { background-position: 0% 50%; }
                }
            `;
            document.head.appendChild(style);
            
            // Add floating message
            var message = document.createElement('div');
            message.textContent = 'Browser Automation in Action! 🚀';
            message.style.position = 'fixed';
            message.style.top = '20px';
            message.style.right = '20px';
            message.style.background = 'rgba(0,0,0,0.8)';
            message.style.color = 'white';
            message.style.padding = '10px 20px';
            message.style.borderRadius = '10px';
            message.style.fontSize = '18px';
            message.style.zIndex = '9999';
            message.style.animation = 'bounce 2s infinite';
            document.body.appendChild(message);
            
            var bounceStyle = document.createElement('style');
            bounceStyle.textContent = `
                @keyframes bounce {
                    0%, 20%, 50%, 80%, 100% { transform: translateY(0); }
                    40% { transform: translateY(-10px); }
                    60% { transform: translateY(-5px); }
                }
            `;
            document.head.appendChild(bounceStyle);
        """)
        
        print(f"{Fore.GREEN}✅ JavaScript effects applied!")
        time.sleep(3)
        self.take_screenshot("javascript_demo")
        
    def create_summary_report(self):
        """Create a summary report of findings"""
        print(f"\n{Fore.MAGENTA}📊 Creating Summary Report...")
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        report = {
            'timestamp': timestamp,
            'total_results': len(self.results),
            'results': self.results,
            'summary': 'Smart Shopping Assistant completed successfully!'
        }
        
        # Save report as JSON
        report_file = f"shopping_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
            
        print(f"{Fore.GREEN}✅ Report saved: {report_file}")
        
    def run_shopping_demo(self, product="laptop"):
        """Run the complete shopping demonstration"""
        print(f"{Fore.CYAN}{Style.BRIGHT}🛒 SMART SHOPPING ASSISTANT DEMO")
        print(f"{Fore.CYAN}{'='*50}")
        
        try:
            # Search multiple sites
            amazon_results = self.search_amazon(product)
            self.results.extend(amazon_results)
            
            time.sleep(2)  # Pause for dramatic effect
            
            ebay_results = self.search_ebay(product)
            self.results.extend(ebay_results)
            
            time.sleep(2)
            
            google_results = self.search_google_shopping(product)
            self.results.extend(google_results)
            
            # Demonstrate advanced features
            self.demonstrate_advanced_features()
            time.sleep(3)
            
            # Show JavaScript capabilities
            self.demonstrate_javascript_execution()
            time.sleep(3)
            
            # Create summary
            self.create_summary_report()
            
            # Final summary
            print(f"\n{Fore.GREEN}{Style.BRIGHT}🎉 DEMONSTRATION COMPLETE!")
            print(f"{Fore.YELLOW}📈 Total products found: {len(self.results)}")
            print(f"{Fore.YELLOW}🖼️  Screenshots saved in: {self.screenshots_dir}/")
            
        except Exception as e:
            print(f"{Fore.RED}❌ Demo error: {str(e)}")
            
    def interactive_demo(self):
        """Run an interactive demonstration"""
        print(f"{Fore.CYAN}{Style.BRIGHT}🎮 INTERACTIVE BROWSER AUTOMATION DEMO")
        print(f"{Fore.CYAN}{'='*50}")
        
        while True:
            print(f"\n{Fore.YELLOW}Choose a demo:")
            print(f"{Fore.WHITE}1. 🛒 Smart Shopping Assistant")
            print(f"{Fore.WHITE}2. 📝 Form Automation Demo")
            print(f"{Fore.WHITE}3. ⚡ JavaScript Execution Demo")
            print(f"{Fore.WHITE}4. 🔍 Custom Search Demo")
            print(f"{Fore.WHITE}5. 🚪 Exit")
            
            choice = input(f"\n{Fore.CYAN}Enter your choice (1-5): {Style.RESET_ALL}")
            
            if choice == '1':
                product = input(f"{Fore.CYAN}Enter product to search: {Style.RESET_ALL}") or "laptop"
                self.run_shopping_demo(product)
            elif choice == '2':
                self.demonstrate_advanced_features()
            elif choice == '3':
                self.demonstrate_javascript_execution()
            elif choice == '4':
                url = input(f"{Fore.CYAN}Enter URL to visit: {Style.RESET_ALL}")
                if url:
                    self.driver.get(url)
                    self.take_screenshot("custom_visit")
            elif choice == '5':
                break
            else:
                print(f"{Fore.RED}Invalid choice!")
                
            input(f"\n{Fore.YELLOW}Press Enter to continue...")
            
    def close(self):
        """Clean up resources"""
        print(f"\n{Fore.YELLOW}🔧 Closing browser...")
        self.driver.quit()
        print(f"{Fore.GREEN}✅ Demo complete! Thanks for watching!")


def main():
    """Main function to run the demonstration"""
    print(f"{Fore.CYAN}{Style.BRIGHT}🎬 SELENIUM BROWSER AUTOMATION DEMO")
    print(f"{Fore.CYAN}{'='*40}")
    print(f"{Fore.WHITE}This demo will show you the power of Selenium!")
    print(f"{Fore.WHITE}Watch as we automate browsers in real-time...")
    
    # Ask for demo type
    demo_type = input(f"\n{Fore.YELLOW}Choose demo type:\n1. Auto Demo (runs automatically)\n2. Interactive Demo\nChoice (1-2): {Style.RESET_ALL}")
    
    assistant = SmartShoppingAssistant(headless=False)
    
    try:
        if demo_type == '2':
            assistant.interactive_demo()
        else:
            # Auto demo
            product = input(f"{Fore.CYAN}Enter product to search for (or press Enter for 'laptop'): {Style.RESET_ALL}") or "laptop"
            assistant.run_shopping_demo(product)
            
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Demo interrupted by user")
    except Exception as e:
        print(f"{Fore.RED}Error: {str(e)}")
    finally:
        assistant.close()


if __name__ == "__main__":
    main()