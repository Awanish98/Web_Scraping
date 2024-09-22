import asyncio
from pyppeteer import launch
from parsel import Selector
from typing import List, Dict
import json
import os

# Ensure the output directory exists
os.makedirs("output", exist_ok=True)

# URLs for different categories to scrape
categories = {
    "flowers_and_plants": "https://www.traderjoes.com/home/products/category/flowers-and-plants-203",
    "beverages": "https://www.traderjoes.com/home/products/category/beverages-182",
    "everything_else": "https://www.traderjoes.com/home/products/category/everything-else-215",
    #"food": "https://www.traderjoes.com/home/products/category/food-8"
}

# Function to launch the browser
async def launch_browser():
    browser = await launch(
        headless=False,  # Set to False to see browser interaction
        executablePath='D:/chromium/chrome.exe',  # Adjust path to your Chromium/Chrome executable
        args=['--no-sandbox']  # Avoids permission issues in certain environments
    )
    return browser

# Function to extract product links from the current page
async def extract_product_links(page, current_page_url: str) -> List[str]:
    try:
        await page.waitForXPath("//a[contains(@class, 'Link_link__1AZfr') and contains(@class, 'ProductCard_card__title__301JH')]", timeout=15000)
        content = await page.content()
        sel = Selector(text=content)
        product_links = sel.xpath("//a[contains(@class, 'Link_link__1AZfr') and contains(@class, 'ProductCard_card__title__301JH')]/@href").getall()
        product_links = [f"https://www.traderjoes.com{link}" for link in product_links]

        # Debugging statement to show number of products and the current page URL
        print(f"Found {len(product_links)} product links on page {current_page_url}.")
        
        return product_links
    except Exception as e:
        print(f"Error extracting product links from page {current_page_url}: {e}")
        return []

# Function to scrape product details, including ingredients
async def scrape_product_details(page, product_url: str, category: str, retries=3) -> Dict[str, any]:
    for attempt in range(retries):
        try:
            await page.goto(product_url, timeout=60000)
            await page.waitForXPath('//h1[contains(@class, "ProductDetails_main__title")]', timeout=20000)
            content = await page.content()
            sel = Selector(text=content)

            # Extract product details
            product_data = {
                'title': sel.xpath('//h1[contains(@class, "ProductDetails_main__title")]/text()').get() or sel.xpath('//h1/text()').get(),
                'price': sel.xpath('//div[contains(@class, "ProductPrice_productPrice")]//span[1]/text()').get(),
                'image': sel.xpath('//picture[contains(@class, "HeroImage_heroImage")]//img/@src').get(),
                'details': sel.xpath('//div[contains(@class, "ProductDetails_main__description")]//p/text()').getall(),
                'url': product_url,
                'category': category  # Include category in the product data
            }

            # Extract ingredients
            ingredients = sel.xpath("//div[@class='Section_section__oNcdC']//div[contains(@class, 'Section_section__header__R8aD_')]/following-sibling::div/text()").getall()
            product_data['ingredients'] = ingredients if ingredients else "NA"  # Set "NA" if no ingredients found

            await asyncio.sleep(1)  # Small sleep between requests
            return product_data
        except Exception as e:
            print(f"Error scraping {product_url}: {e} (Attempt {attempt + 1} of {retries})")
            if attempt < retries - 1:
                await asyncio.sleep(1)  # Wait before retrying
            else:
                return {}

# Function to scrape all products from the current page's product links
async def scrape_all_products(page, product_links: List[str], total_products: List[Dict[str, any]], category: str, category_count: Dict[str, int]):
    for link in product_links:
        product_details = await scrape_product_details(page, link, category)
        if product_details:
            total_products.append(product_details)
            category_count[category] += 1  # Increment the count for the current category
            print(f"Scraped product: {product_details['title']}")
        await asyncio.sleep(1)  # Small delay between products to prevent too many requests

# Function to click the "Next" button on the category page to load the next set of products
async def go_to_next_page(page):
    try:
        # Check if 'Next' button is disabled
        disabled_button_check = await page.xpath("//button[@class='Pagination_pagination__arrow__3TJf0 Pagination_pagination__arrow_side_right__9YUGr Pagination_pagination__arrow_disabled__1Dx6c']")
        if disabled_button_check:
            print("Last page reached (button disabled).")
            return False
        
        # Wait for the 'Next' button to be clickable and not disabled
        next_button = await page.waitForXPath("//button[@class='Pagination_pagination__arrow__3TJf0 Pagination_pagination__arrow_side_right__9YUGr']", {'visible': True, 'timeout': 10000})
        if next_button:
            await next_button.click()
            await page.waitForNavigation({'waitUntil': 'networkidle0'})  # Wait until the network is idle
            print("Moved to the next page.")
            return True
        else:
            print("No 'Next' button found or it's disabled, possibly last page.")
            return False
    except Exception as e:
        print(f"Error moving to the next page: {e}")
        return False

# Function to scrape all products and navigate pages for a given category
async def scrape_all_pages(page, category_url: str, category: str, total_products: List[Dict[str, any]], category_count: Dict[str, int]):
    current_page_number = 1  # Track the current page number

    while True:
        # Get current page URL to return after scraping
        current_page_url = page.url
        print(f"Scraping product links from page {current_page_url}")

        # Extract product links from the current page
        product_links = await extract_product_links(page, current_page_url)
        if product_links:
            # Scrape all product details from the current page's product links
            await scrape_all_products(page, product_links, total_products, category, category_count)
        
        # After scraping all products from the current page, return to the saved page URL (before "Next")
        await page.goto(current_page_url)  # Return to the page before trying to click "Next"
        print(f"Returned to page {current_page_url}. Ready to click 'Next' button.")

        await asyncio.sleep(1)  # Ensure the page reloads completely
        
        # Try clicking the "Next" button to move to the next page
        if not await go_to_next_page(page):
            break
        
        # Increment the page number for debugging and continue
        current_page_number += 1

# Main function to scrape all categories
async def scrape_categories():
    browser = await launch(headless=False, executablePath='/usr/bin/google-chrome')
    page = await browser.newPage()
    
    total_products = []  # Store all products from all categories
    category_count = {category: 0 for category in categories.keys()}  # Initialize count per category

    for category, url in categories.items():
        print(f"Starting scraping for category: {category}")
        await page.goto(url)
        await scrape_all_pages(page, url, category, total_products, category_count)
    
    # Save the scraped data to a JSON file
    with open('output/traderjoes.json', 'w') as f:
        json.dump(total_products, f, indent=4)

    # Save the product count details to a text file
    total_count = sum(category_count.values())
    with open('output/traderjoes_count.txt', 'w') as f:
        for category, count in category_count.items():
            f.write(f"{category}: {count} products\n")
        f.write(f"\nTotal products scraped across all categories: {total_count}\n")
    
    await browser.close()
    print(f"Total {total_count} products scraped across all categories.")
    print("Browser closed.")

# Run the scraper
asyncio.run(scrape_categories())
