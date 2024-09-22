import os
import asyncio
from pyppeteer import launch
from parsel import Selector
import json
import re

# Function to scrape product details
async def scrape_product_details(page, product_url, category):
    try:
        await page.goto(product_url)
        await page.waitForSelector('h1')  
        content = await page.content()
        sel = Selector(text=content)

        # Scrape title and description
        description = sel.xpath("//div[@class='productAccordion__content js-tab-content']/p/text()").get() or "N/A"
        description = description.strip()

        # Scrape price per kilo
        price_text = sel.xpath('//h3[text()="Price per kilo"]/following-sibling::p[1]/text()').get()

        # Extract only numerical values from the price per kilo
        if price_text:
            price_match = re.search(r'[\d,]+(?:\.\d{2})?', price_text)
            if price_match:
                price_per_kg = price_match.group(0).replace(",", "") 
                price_per_kg = float(price_per_kg)  
            else:
                price_per_kg = "Price not available"
        else:
            price_per_kg = "Price not available"

        # Scraping all images based on the provided XPath
        image_urls = sel.xpath('/html/body/main/article[1]/section[1]/div/ul/li/a/picture/img/@src').getall()
        image_urls = [f"https://www.lechocolat-alainducasse.com{img}" if not img.startswith("http") else img for img in image_urls]

        # Scrape weight using the class name `productCard__weight`
        weight = sel.xpath('//p[contains(@class, "productCard__weight")]/text()').get().replace("g","") or "N/A"
        weight = float(weight) if weight != "N/A" else 0

        selling_price = weight * (price_per_kg / 1000) if isinstance(price_per_kg, float) else "N/A"
        selling_price = round(selling_price, 2) if isinstance(selling_price, float) else selling_price

        # Scrape the product title using new XPath and strip the extra spaces and newlines
        title = sel.xpath("//h1[@class='productCard__title']/text()").get() or "N/A"
        title = title.strip()

        # Structured product data
        product_data = {
            'title_id': product_url.split('/')[-1],  # title ID based on URL
            'title': title,  # cleaned title
            'description': description,
            'price_per_kg': price_per_kg,  # Added price per kg
            'price': selling_price,
            'images': image_urls,
            'weight': weight,  # Storing the weight
            'url': product_url,
            'brand': "Le Chocolat Alain Ducasse",
            'category': category  # Added category
        }

        # Print product data in JSON format
        print(json.dumps(product_data, indent=4))

        return product_data

    except Exception as e:
        print(f"Failed to scrape product details from {product_url}: {str(e)}")
        return None

# Function to scrape all products in a category
async def scrape_category(page, category_url, category_name):
    try:
        # Open the first page of the category
        await page.goto(category_url)

        all_products = []
        # Get the page content and parse it with Parsel
        content = await page.content()
        sel = Selector(text=content)

        # Extract product links from the current page (fine-tuned the XPath selector)
        product_links = sel.xpath('//div[contains(@class, "product-miniature")]//a/@href').getall()

        for product_link in product_links:
            # Check if the link is absolute or relative
            if not product_link.startswith('http'):
                product_url = f"https://www.lechocolat-alainducasse.com{product_link}"
            else:
                product_url = product_link

            product_data = await scrape_product_details(page, product_url, category_name)
            if product_data:
                all_products.append(product_data)

        # Print all products in the category in JSON format
        print(json.dumps(all_products, indent=4))

        return all_products
    except Exception as e:
        print(f"Failed to scrape category: {category_url}, error: {str(e)}")
        return []

# Main function to run the scraper
async def main():
    browser = await launch(headless=False, executablePath='/usr/bin/google-chrome')
    page = await browser.newPage()

    categories = {
        "Gifts": "https://www.lechocolat-alainducasse.com/uk/chocolate-gift",
        "Boxes": "https://www.lechocolat-alainducasse.com/uk/chocolates",
        "Bars": "https://www.lechocolat-alainducasse.com/uk/chocolate-bar",
        "Simple Pleasures": "https://www.lechocolat-alainducasse.com/uk/simple-pleasures",
        "Breakfast & Snacks": "https://www.lechocolat-alainducasse.com/uk/simple-pleasures"
    }

    all_products = []
    for category_name, category_url in categories.items():
        print(f"Scraping category: {category_name} - {category_url}")
        products = await scrape_category(page, category_url, category_name)
        all_products.extend(products)

    # Ensure the output directory exists
    os.makedirs('output', exist_ok=True)

    # Save scraped data to a JSON file in 'output/lechocolat.json'
    with open('output/lechocolat.json', 'w') as f:
        json.dump(all_products, f, indent=4)

    # Save total product count to a text file in 'output/traderjoes_count.txt'
    total_count = len(all_products)
    with open('output/output/traderjoes_count.txt.', 'w') as f:
        f.write(f"Total products scraped: {total_count}")

    # Print total product count in JSON format
    print(json.dumps({"total_products_scraped": total_count}, indent=4))

    # Close browser
    await browser.close()
    print(f"Total products scraped: {total_count}")

# Run the script
if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())
