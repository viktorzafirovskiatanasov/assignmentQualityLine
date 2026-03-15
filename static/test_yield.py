from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC

BASE_URL = "http://localhost:8000"
EXPECTED_YIELD = "60%"


def insert_record(driver, serial_number: str, passed: bool):
    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "manual-test-btn"))
    ).click()

    serial_input = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.ID, "serial_number"))
    )
    serial_input.clear()
    serial_input.send_keys(serial_number)

    Select(driver.find_element(By.ID, "part_number")).select_by_value("001PN001")

    status_checkbox = driver.find_element(By.ID, "status")
    if status_checkbox.is_selected() != passed:
        status_checkbox.click()

    driver.find_element(By.ID, "add-test-btn").click()

    WebDriverWait(driver, 10).until(
        EC.invisibility_of_element_located((By.ID, "modal-overlay"))
    )


def main():
    driver = webdriver.Chrome()
    driver.maximize_window()

    try:
        driver.get(BASE_URL)
        test_rows = [
            ("AUTO-SN-001", True),
            ("AUTO-SN-002", True),
            ("AUTO-SN-003", True),
            ("AUTO-SN-004", False),
            ("AUTO-SN-005", False),
        ]

        for serial_number, passed in test_rows:
            insert_record(driver, serial_number, passed)

        target_part = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-part-number="001PN001"]'))
        )
        target_part.click()

        yield_value = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.ID, "yield-value"))
        ).text.strip()

        if yield_value == EXPECTED_YIELD:
            print(f"PASS - expected {EXPECTED_YIELD}, got {yield_value}")
        else:
            print(f"FAIL - expected {EXPECTED_YIELD}, got {yield_value}")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
