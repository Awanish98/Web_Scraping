from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

driver = webdriver.Chrome()
driver.get("https://www.booking.com")

try:
    place = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "/html/body/div[3]/div[2]/div/form/div[1]/div[2]/div/div[2]/div/nav/div[2]/div/div[1]/div/div[1]/table/tbody/tr[3]/td[4]/span"))
    )
    place.send_keys("Mumbai")
except Exception as e:
    print(f"An error occurred: {e}")
finally:
    driver.implicitly_wait(20)
