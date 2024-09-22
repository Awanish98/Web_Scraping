import asyncio
from pyppeteer import launch
from parsel import Selector
import json

# Utility function to handle popups
async def close_popup(page):
    try:
        popup_button_xpath = '/html/body/div[6]/div/div[2]/div/div/div/div/div/form/div/div[5]/div[1]/button'
        await page.waitForXPath(popup_button_xpath, timeout=10000)
        popup_button = await page.xpath(popup_button_xpath)
        if popup_button:
            await popup_button[0].click()
            print("Popup closed")
        else:
            print("No popup appeared")
    except Exception as e:
        print(f"No popup appeared: {str(e)}")

# Function to scrape variant data (id, price, image) for a specific combination of color and size
async def get_variant_id(page, color, size):
    try:
        # Select color and size from dropdowns
        await page.select('select#SingleOptionSelector-0', size)
        await page.select('select#SingleOptionSelector-1', color)

        # Wait for the variant to load after selecting the combination
        await page.waitForXPath('//*[@id="ProductPrice-product-template"]')

        # Extract variant id from URL
        current_url = page.url
        variant_id = current_url.split('?variant=')[-1] if '?variant=' in current_url else None


        # Extract price and image
        content = await page.content()
        sel = Selector(text=content)
        price = sel.xpath('//*[@id="ProductPrice-product-template"]/text()').get()
        if price:
            price = float(price.replace("$", "").replace(",", "").strip())
        else:
            print(f"Warning: Missing price for color: {color}, size: {size}")
            price = 0.0  # Assign a default value if price is missing
        image = sel.xpath('//*[@id="FeaturedImage-product-template"]/@src').get()
        image = f"https:{image}" if image else "N/A"
        if image == "N/A":
            print(f"Warning: Missing image for color: {color}, size: {size}")

        return {
            'id': variant_id,
            'price': price,
            'image': image,
            'size': size
        }

    except Exception as e:
        print(f"Error scraping variant for {color} {size}: {str(e)}")
        return None

# Function to scrape product details
async def scrape_product_details(page, product_url, category_name):
    try:
        print(f"Scraping product details for: {product_url}")
        await page.goto(product_url)
        await asyncio.sleep(2)  # Adding delay after navigating to a new product page
        await page.waitForSelector('h1')
        content = await page.content()
        sel = Selector(text=content)

        # Scraping relevant product details
        title = sel.xpath('//*[@id="ProductSection-product-template"]/div/div[2]/div/h1/text()').get()

        # Clean description by removing newline characters and extra spaces
        description = sel.xpath('//*[@id="ProductSection-product-template"]/div/div[2]/div/div[2]/text()').get() or "N/A"
        description = description.strip().replace("\n", "").replace("\r", "").strip()  # Clean description

        print(f"Title: {title}, Description: {description[:50]}...")  # Log the product title and description

        # Scraping available sizes and colors
        sizes = sel.xpath('//*[@id="SingleOptionSelector-0"]/option/text()').getall() or []
        colors = sel.xpath('//*[@id="SingleOptionSelector-1"]/option/text()').getall() or []
        if not sizes and not colors:
            print(f"Info: No sizes or colors for product: {title}")

        # Scraping all product images
        images = sel.xpath('//*[@id="ProductSection-product-template"]/div/div[1]//img/@src').getall()
        images = [f"https:{img}" for img in images]  # Add https prefix if needed
        print(f"Images found: {len(images)}")  # Log number of images found

        # Extract base price in case there are no sizes or colors
        base_price = sel.xpath('//*[@id="ProductPrice-product-template"]/text()').get()
        if base_price:
            base_price = float(base_price.replace("$", "").replace(",", "").strip())
            print(f"Base price found: {base_price}")
        else:
            print(f"Warning: No base price found for product: {title}")
            base_price = None

        # Structuring the model data (loop through colors and sizes)
        models = []
        if colors and sizes:
            for color in colors:
                color_variants = []
                for size in sizes:
                    variant_data = await get_variant_id(page, color, size)
                    if variant_data:
                        color_variants.append(variant_data)

                models.append({
                    'color': color,
                    'variants': color_variants
                })
        else:
            print(f"Info: No sizes or colors found for product: {title}")

        # Log if no variants were found
        if not models and base_price:
            # Use the base price if no variants are available
            models.append({
                'color': 'N/A',
                'variants': [{
                    'id': None,
                    'price': base_price,
                    'image': images[0] if images else "N/A",
                    'size': 'One Size'
                }]
            })

        # Return structured product data with category included
        return {
            'product_id': product_url.split('/')[-1],  # Assuming the product ID is part of the URL
            'title': title,
            'description': description,  # Cleaned description
            'sale_prices': list(set([variant['price'] for model in models for variant in model['variants'] if variant])),  # Remove duplicates from sale_prices
            'prices': list(set([variant['price'] for model in models for variant in model['variants'] if variant])),  # Remove duplicates from prices
            'images': images,
            'url': product_url,
            'brand': "Foreign Fortune Clothing",  # Add the brand
            'category': category_name,  # Include the category name
            'models': models
        }

    except Exception as e:
        print(f"Failed to scrape product details from {product_url}: {str(e)}")
        return None

# Function to scrape all products in a category
async def scrape_category(page, category_url, category_name):
    try:
        print(f"Scraping category: {category_url}")
        # Open the first page of the category
        await page.goto(category_url)
        await asyncio.sleep(2)  # Adding delay after navigating to category page
        await close_popup(page)

        # Detect the total number of pages
        try:
            total_pages_text = await page.querySelectorEval('li.pagination__text', 'el => el.innerText')
            total_pages = int(total_pages_text.split()[-1])  # Get the last word (total number of pages)
        except Exception as e:
            print(f"Failed to extract total pages, defaulting to 1: {str(e)}")
            total_pages = 1

        print(f"Total pages: {total_pages}")

        all_products = []
        # Loop through all pages in the category
        for page_number in range(1, total_pages + 1):
            print(f"Scraping page {page_number} of {total_pages} in category {category_url}")
            # If it's not the first page, navigate to the corresponding page URL
            if page_number > 1:
                await page.goto(f"{category_url}?page={page_number}")
                await asyncio.sleep(2)  # Delay after navigating to a new page
                await close_popup(page)  # Close popup if it reappears

            # Get the page content and parse it with Parsel
            content = await page.content()
            sel = Selector(text=content)

            # Extract product links from the current page
            product_links = sel.xpath('//*[@id="Collection"]/div/div/div/a/@href').getall()
            for product_link in product_links:
                product_url = f"https://foreignfortune.com{product_link}"
                product_data = await scrape_product_details(page, product_url, category_name)
                if product_data:
                    print(f"Scraped product: {product_data['title']}")
                    all_products.append(product_data)

        return all_products
    except Exception as e:
        print(f"Failed to scrape category: {category_url}, error: {str(e)}")
        return []

# Main function to run the scraper
async def main():
    browser = await launch(headless=False, executablePath='/usr/bin/google-chrome')
    page = await browser.newPage()

    categories = [
        {"url": "https://foreignfortune.com/collections/men-unisex", "name": "Men/Unisex"},
        {"url": "https://foreignfortune.com/collections/women", "name": "Women"},
        {"url": "https://foreignfortune.com/collections/kids", "name": "Infant/Kid"},
        {"url": "https://foreignfortune.com/collections/coats-hats", "name": "Coats/Hats"},
        {"url": "https://foreignfortune.com/collections/small-logo-embroidery-t-shirts-1", "name": "TrackSuits"},
        {"url": "https://foreignfortune.com/collections/frontpage", "name": "Foreign Rovalf"},
        {"url": "https://foreignfortune.com/collections/foreign-accesories", "name": "Accessories"}
    ]

    all_products = []
    for category in categories:
        print(f"Scraping category: {category['name']}")
        products = await scrape_category(page, category['url'], category['name'])
        all_products.extend(products)

    # Save scraped data to a JSON file
    with open('output/foreignfortune.json', 'w') as f:
        json.dump(all_products, f, indent=4)

    # Save total product count to a file
    total_count = len(all_products)
    with open('output/foreignfortune_count.txt', 'w') as f:
        f.write(f"Total products scraped: {total_count}")

    # Print total product count in JSON format
    print(json.dumps({"total_products_scraped": total_count}, indent=4))

    # Close browser
    await browser.close()
    print(f"Total products scraped: {total_count}")

# Run the script
if __name__ == '__main__':
    asyncio.run(main())
