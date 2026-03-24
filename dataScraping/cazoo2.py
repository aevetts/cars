import asyncio
import random
import os
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import pandas as pd

# --- CONFIG ---
PROXY = {
    "server": "",  # Put your details in here
    "username": "",
    "password": ""
}

BASE_URL = "https://www.cazoo.co.uk/cars/?page="
MAX_PAGES = 4000
PAGES_PER_BROWSER = 25
PAGES_PER_CONTEXT = 5
SAVE_INTERVAL = 10  # Save to CSV every 10 pages, in case of crashes or blocks
OUTPUT_FILE = "cazoo2_data.csv"

# Some user agents to randomly choose from
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
]

def save_to_csv(data_list, filename):
    """Appends data to CSV. Writes header only if file doesn't exist."""
    if not data_list:
        return
    
    df = pd.DataFrame(data_list)
    file_exists = os.path.isfile(filename)
    
    # mode='a' appends; header=not file_exists only writes columns if it's the first time
    df.to_csv(filename, mode='a', index=False, header=not file_exists)
    print(f"Saved {len(data_list)} rows to {filename}")

async def extract_data(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    listings = soup.find_all('li', {'data-testid': 'search-result'})
    data = []
    for item in listings:
        try:
            data.append({
                'Title': item.find('p', {'data-testid': 'vehicle-title'}).get_text(strip=True),
                'Price': item.find('span', {'class': 'c-text-lg-medium lg:c-heading-xl'}).get_text(strip=True),
                'Year': item.find('div', {'data-testid': 'year-badge'}).get_text(strip=True),
                'Miles': item.find('div', {'data-testid': 'mileage-badge'}).get_text(strip=True),
                'Fuel': item.find('div', {'data-testid': 'fuel-badge'}).get_text(strip=True)
            })
        except: continue
    return data



async def scrape_cazoo():
    batch_data = []
    current_page = 1 # Start page. Go back and update this if the script was interrupted and you want to start where you left off.

    async with async_playwright() as p:
        while current_page <= MAX_PAGES:
            browser = await p.chromium.launch(headless=False) 
            
            for _ in range(PAGES_PER_BROWSER // PAGES_PER_CONTEXT):
                if current_page > MAX_PAGES: break
                
                context = await browser.new_context(
                    # proxy=PROXY, # Uncomment if using a proxy
                    user_agent=random.choice(USER_AGENTS)
                )

                for _ in range(PAGES_PER_CONTEXT):
                    if current_page > MAX_PAGES: break
                    page = await context.new_page()

                    url = f"{BASE_URL}{current_page}"
                    
                    # --- RETRY LOGIC FOR TUNNEL ERRORS ---
                    success = False
                    for attempt in range(3): # Try 3 times before giving up on the page
                        try:
                            print(f"Scraping Page {current_page} (Attempt {attempt+1})...")
                            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                            
                            content = await page.content()
                            if "search-result" in content:
                                page_data = await extract_data(content)
                                batch_data.extend(page_data)
                                
                                if current_page % SAVE_INTERVAL == 0:
                                    save_to_csv(batch_data, OUTPUT_FILE)
                                    batch_data = []
                                
                                current_page += 1
                                success = True
                                break # Success! Exit the retry loop
                            else:
                                print("Content check failed. Proxy might be throttled.")
                                await asyncio.sleep(10)

                        except Exception as e:
                            # Catching Tunnel/Proxy errors specifically
                            if "ERR_TUNNEL_CONNECTION_FAILED" in str(e) or "net::ERR" in str(e):
                                print(f"Tunnel failed on page {current_page}. Cooling down...")
                                await asyncio.sleep(20) # Give the proxy gateway time to reset
                            else:
                                print(f"Unexpected Error: {e}")
                                break # Exit retry on unknown errors

                    await page.close()
                    if not success:
                        print(f"Skipping page {current_page} after 3 failed attempts.")
                        current_page += 1 # Or keep it same to try again with a new context
                    
                    await asyncio.sleep(random.uniform(2, 4))

                await context.close()
            await browser.close()
            
    save_to_csv(batch_data, OUTPUT_FILE)

if __name__ == "__main__":
    asyncio.run(scrape_cazoo())