from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time

# Define the test data
first_name = "Test"
last_name = "User"
email = "test.user@example.com"
password = "password123"
user_type = "customer"  # Change to "barber" if needed

# Initialize the WebDriver (Make sure to replace 'path/to/msedgedriver' with the actual path if necessary)
driver = webdriver.Edge()  # Replace with the correct path

try:
    # Step 1: Navigate to the registration page
    driver.get("http://127.0.0.1:5000/")  # Replace with the actual URL if different

    # Step 2-8: Fill in the registration form
    driver.find_element(By.ID, "first_name").send_keys(first_name)
    driver.find_element(By.ID, "last_name").send_keys(last_name)
    driver.find_element(By.ID, "email").send_keys(email)
    driver.find_element(By.ID, "password").send_keys(password)
    driver.find_element(By.ID, "confirm_password").send_keys(password)
    user_type_dropdown = driver.find_element(By.ID, "user_type")
    for option in user_type_dropdown.find_elements(By.TAG_NAME, 'option'):
        if option.text == user_type.capitalize():
            option.click()
            break

    # Submit the form
    driver.find_element(By.XPATH, "//button[text()='Submit']").click()

    # Wait for the page to load and check for the success message
    time.sleep(2)  # Adjust sleep time if necessary

    # Check if the success message is displayed
    success_message = driver.find_element(By.XPATH,
                                          "//div[contains(text(), 'Account created successfully. Please sign in.')]")
    assert success_message.is_displayed(), "Success message not displayed"

    print("Test Passed: User registration was successful")

except Exception as e:
    print(f"Test Failed: {e}")

finally:
    # Close the browser
    driver.quit()
