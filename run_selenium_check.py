import os
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException


print("RUNNING FILE:", os.path.abspath(__file__))


BASE_URL = "http://localhost:8000"
TARGET_PART = "001PN001"
EXPECTED_YIELD = "60%"


TEST_ROWS = [
    ("AUTO-SN-001", True),
    ("AUTO-SN-002", True),
    ("AUTO-SN-003", True),
    ("AUTO-SN-004", False),
    ("AUTO-SN-005", False),
]


def log(message):
    print(f"[INFO] {message}")


def insert_record(driver, wait, serial_number, passed):

    log(f"Inserting record {serial_number} | Passed={passed}")

    wait.until(
        EC.element_to_be_clickable((By.ID, "manual-test-btn"))
    ).click()

    serial_input = wait.until(
        EC.visibility_of_element_located((By.ID, "serial_number"))
    )

    serial_input.clear()
    serial_input.send_keys(serial_number)

    Select(driver.find_element(By.ID, "part_number")).select_by_value(TARGET_PART)

    status_checkbox = driver.find_element(By.ID, "status")

    if status_checkbox.is_selected() != passed:
        status_checkbox.click()

    driver.find_element(By.ID, "add-test-btn").click()

    wait.until(
        EC.invisibility_of_element_located((By.ID, "modal-overlay"))
    )


def select_part(driver, wait):

    log(f"Selecting part {TARGET_PART}")

    element = wait.until(
        EC.element_to_be_clickable(
            (By.CSS_SELECTOR, f'[data-part-number="{TARGET_PART}"]')
        )
    )

    element.click()


def read_yield(driver, wait):

    log("Waiting for yield to update")

    wait.until(
        lambda d: d.find_element(By.ID, "yield-value").text != "0%"
    )

    value = driver.find_element(By.ID, "yield-value").text.strip()

    log(f"Yield value detected: {value}")

    return value


def main():

    log("Starting Selenium test")

    driver = webdriver.Chrome()
    wait = WebDriverWait(driver, 15)

    driver.maximize_window()

    try:

        driver.get(BASE_URL)

        wait.until(
            EC.visibility_of_element_located((By.ID, "manual-test-btn"))
        )

        log("Page loaded successfully")

        for serial_number, passed in TEST_ROWS:
            insert_record(driver, wait, serial_number, passed)

        select_part(driver, wait)

        yield_value = read_yield(driver, wait)

        print("\n----------- TEST RESULT -----------")
        print("Expected:", EXPECTED_YIELD)
        print("Actual:  ", yield_value)

        if yield_value == EXPECTED_YIELD:
            print("RESULT: PASS")
        else:
            print("RESULT: FAIL")

        print("-----------------------------------\n")

        time.sleep(2)

    except TimeoutException:
        print("ERROR: UI element did not appear in time")

    finally:
        driver.quit()
        log("Browser closed")


if __name__ == "__main__":
    main()