import re
import json
import os
import logging

# Ensure the output directory exists
os.makedirs("validation", exist_ok=True)

# Setup the main logger format
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# Helper function to set up individual loggers
def setup_logger(log_file):
    handler = logging.FileHandler(log_file)
    handler.setFormatter(formatter)
    logger = logging.getLogger(log_file)
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    return logger

class Validation:
    def __init__(self, product, website):
        self.product = product
        self.website = website

    def validate_sale_price(self):
        """Ensure that sale price is less than or equal to the original price."""
        if self.website == "Foreign Fortune":
            original_prices = self.product.get("prices", [])
            sale_prices = self.product.get("sale_prices", [])
            
            if not sale_prices:
                return True, "No sale price, skipping sale price validation."
            if not original_prices:
                return True, "No original prices, skipping sale price validation."
            
            for sale, original in zip(sale_prices, original_prices):
                if sale > original:
                    return False, f"Sale price {sale} is greater than the original price {original}."
        # No sale price check for Trader Joe's and Le Chocolat
        return True, "Sale price validation passed."

    def validate_mandatory_fields(self):
        """Check that mandatory fields like title, title_id, and category are present."""
        if self.website == "Le Chocolat":
            mandatory_fields = ['title', 'title_id', 'price', 'category', 'weight']
        elif self.website == "Trader Joe's":
            mandatory_fields = ['title', 'price', 'category', 'ingredients']
        else:  # Foreign Fortune
            mandatory_fields = ['title', 'product_id', 'models', 'category']

        for field in mandatory_fields:
            if not self.product.get(field):
                return False, f"Missing mandatory field: {field}"
        return True, "Mandatory fields validation passed."

    def validate_variants(self):
        """Ensure that each product variant has images and prices (For Foreign Fortune)."""
        if self.website == "Foreign Fortune":
            models = self.product.get("models", [])
            if not models:
                return False, "No models found."
            
            for model in models:
                for variant in model.get("variants", []):
                    if not variant.get("image") or not variant.get("price"):
                        return False, f"Variant missing image or price: {variant}"
        return True, "Variant validation passed."

    def validate_positive_price(self):
        """Check that all prices are positive numbers."""
        if self.website == "Le Chocolat" or self.website == "Foreign Fortune":
            price = self.product.get("price", None)
            prices = self.product.get("prices", [])

            # Handle if `price` is a single value
            if price is not None and isinstance(price, (int, float)):
                if price <= 0:
                    return False, f"Invalid price: {price}. Price must be positive."

            # Handle `prices` list if present
            if prices:
                for p in prices:
                    if p <= 0:
                        return False, f"Invalid price in list: {p}. Price must be positive."
            elif price is None and not prices:
                return False, "Prices are missing."

        else:  # Trader Joe's - price is a string, needs parsing
            price_str = self.product.get("price", "")
            try:
                price = float(price_str.replace("$", "").replace(",", "").strip())
                if price <= 0:
                    return False, f"Invalid price: {price}. Price must be positive."
            except ValueError:
                return False, "Price parsing failed."
        
        return True, "Price validation passed."

    def validate_url(self):
        """Check that the product URL is valid."""
        url = self.product.get("url", "")
        if not re.match(r'https?://', url):
            return False, f"Invalid URL: {url}"
        return True, "URL validation passed."

    def validate_weight(self):
        """Ensure that the product has a valid weight (For Le Chocolat and Foreign Fortune)."""
        if self.website == "Le Chocolat" or self.website == "Foreign Fortune":
            weight = self.product.get("weight", None)
            if weight is None or weight == 0:
                return True, "No weight provided, skipping validation."
            elif weight < 0:
                return False, f"Invalid weight: {weight}. Weight must be positive."
        return True, "Weight validation passed."

    def run_all_validations(self):
        """Run all validation methods and return the results."""
        validations = [
            self.validate_sale_price(),
            self.validate_mandatory_fields(),
            self.validate_variants(),
            self.validate_positive_price(),
            self.validate_url(),
            self.validate_weight()
        ]
        
        for validation, message in validations:
            if not validation:
                return False, message
        return True, "All validations passed."

def log_validation_results(products, log_file, summary_file, website_name):
    """Log validation results for each product and count total pass and fail."""
    total_pass = 0
    total_fail = 0

    # Set up individual log file for each dataset
    logger = setup_logger(log_file)

    # Log individual product results
    for product in products:
        validator = Validation(product, website_name)
        is_valid, message = validator.run_all_validations()
        if is_valid:
            total_pass += 1
        else:
            total_fail += 1

        logger.info(f"Product: {product.get('title', 'Unnamed')}")
        logger.info(f"Product ID: {product.get('title_id', product.get('product_id', 'N/A'))}")
        logger.info(f"Validation Status: {'Valid' if is_valid else 'Invalid'}")
        logger.info(f"Message: {message}")
        logger.info("-" * 50)

    # Write summary log
    with open(summary_file, 'a') as summary_log:
        summary_log.write(f"{website_name} - Total Products Passed: {total_pass}\n")
        summary_log.write(f"{website_name} - Total Products Failed: {total_fail}\n\n")

    print(f"Validation results logged to {log_file} and summary in {summary_file}")

def validate_product_count(count_file, summary_file):
    """Validate product count from the count file."""
    total_pass = 0
    total_fail = 0

    # Read the product count file
    with open(count_file, 'r') as file:
        for line in file:
            try:
                category, count = line.strip().split(':')
                count = int(count.split()[0])
                total_pass += count
            except Exception as e:
                total_fail += 1
                logging.error(f"Error parsing count line: {line} | Error: {e}")

    # Write the result in the summary log
    with open(summary_file, 'a') as summary_log:
        summary_log.write(f"Trader Joe's - Total Products Passed: {total_pass}\n")
        summary_log.write(f"Trader Joe's - Total Products Failed: {total_fail}\n\n")
        
    print(f"Product count validation logged to 'validation/traderjoes_count_validation_summary.log'")

def load_products(file_path):
    """Load products from a JSON file."""
    with open(file_path, 'r') as file:
        return json.load(file)

if __name__ == "__main__":
    # Summary log file for all validations
    summary_file = "validation/summary_validation.log"

    # Validate Le Chocolat
    lechocolat_products = load_products('output/lechocolat.json')
    log_validation_results(lechocolat_products, 'validation/lechocolat_validation_log.log', summary_file, "Le Chocolat")

    # Validate Foreign Fortune
    foreignfortune_products = load_products('output/foreignfortune.json')
    log_validation_results(foreignfortune_products, 'validation/foreignfortune_validation_log.log', summary_file, "Foreign Fortune")

    # Validate Trader Joe's count
    validate_product_count('output/traderjoes_count.txt', summary_file)

    # Remove the total log file if it exists
    total_log_file = "validation/total_products_log.log"
    if os.path.exists(total_log_file):
        os.remove(total_log_file)
        print(f"Removed {total_log_file}")
    else:
        print(f"{total_log_file} does not exist.")
