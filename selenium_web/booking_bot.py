from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class BookingBot:
    def __init__(self):
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
        self.wait = WebDriverWait(self.driver, 10)

    def open_site(self, url):
        self.driver.get(url)

    def select_date(self):
        # Wait for the date picker to be clickable and click on it
        checkin_date = self.wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "span.datePickerDesktop__checkInOutText")))
        checkin_date.click()

        # Wait for the date to be clickable and click on the desired date
        desired_date = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//span[text()='20']")))
        desired_date.click()

    def search_city(self, city):
        # Wait for the search field to be visible and enter the city name
        search_field = self.wait.until(EC.visibility_of_element_located((By.ID, "ss")))
        search_field.send_keys(city)

        # Click the search button
        search_button = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.sb-searchbox__button")))
        search_button.click()

    def scrape_hotels(self):
        # Wait for hotel names and prices to load and then scrape them
        hotels = self.wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "span.sr-hotel__name")))
        prices = self.wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.bui-price-display__value")))

        for hotel, price in zip(hotels, prices):
            print(f"Hotel: {hotel.text}, Price: {price.text}")

    def close(self):
        self.driver.quit()
