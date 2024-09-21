from selenium.webdriver.common.by import By

class BookingLocators:
    CHECKIN_DATE = (By.CLASS_NAME, "fb314b6ca4")
    DATE_PICKER_DAY = (By.XPATH, "//span[text()='20']")  # Example day
    SEARCH_FIELD = (By.ID, "ss")
    SEARCH_BUTTON = (By.CSS_SELECTOR, "button.sb-searchbox__button")
    HOTEL_NAMES = (By.CSS_SELECTOR, "span.sr-hotel__name")
    HOTEL_PRICES = (By.CSS_SELECTOR, "div.bui-price-display__value")
