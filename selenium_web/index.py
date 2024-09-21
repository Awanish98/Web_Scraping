from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime, timedelta

# Setup the WebDriver (assuming Chrome, adjust as needed)
driver = webdriver.Chrome()

# Navigate to the website (replace with the actual URL)
driver.get("https://oyorooms.com")


# Function to select location
def select_location(location):
    location_input = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, "input[placeholder='Enter a city, hotel, airport, address or landmark']"))
    )
    location_input.clear()
    location_input.send_keys(location)
    location_input.send_keys(Keys.RETURN)


# Function to select dates
def select_dates(check_in_date, check_out_date):
    date_input = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-testid='date-display-field-start']"))
    )
    date_input.click()

    # Select check-in date
    check_in_element = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, f"td[data-date='{check_in_date.strftime('%Y-%m-%d')}']"))
    )
    check_in_element.click()

    # Select check-out date
    check_out_element = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, f"td[data-date='{check_out_date.strftime('%Y-%m-%d')}']"))
    )
    check_out_element.click()


# Function to set number of guests
def set_guests(num_guests):
    guest_input = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-testid='occupancy-config']"))
    )
    guest_input.click()

    # Assuming there's a way to increment/decrement guests
    # This part may need adjustment based on the actual implementation
    current_guests = int(guest_input.text.split()[0])
    difference = num_guests - current_guests

    if difference > 0:
        increment_button = driver.find_element(By.CSS_SELECTOR, "button[aria-label='Increase number of adults']")
        for _ in range(difference):
            increment_button.click()
    elif difference < 0:
        decrement_button = driver.find_element(By.CSS_SELECTOR, "button[aria-label='Decrease number of adults']")
        for _ in range(abs(difference)):
            decrement_button.click()


# Function to perform search
def perform_search():
    search_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']"))
    )
    search_button.click()


# Main execution
try:
    select_location("Delhi, India")

    today = datetime.now()
    check_in = today + timedelta(days=1)  # Tomorrow
    check_out = check_in + timedelta(days=1)  # Day after tomorrow
    select_dates(check_in, check_out)

    set_guests(1)

    perform_search()

    # Wait for results page to load
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-testid='property-card']"))
    )
    print("Search completed successfully!")

except Exception as e:
    print(f"An error occurred: {e}")

finally:
    # Uncomment the next line to keep the browser open
    # input("Press Enter to close the browser...")
    driver.quit()