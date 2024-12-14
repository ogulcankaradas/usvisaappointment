import time
import random
import requests
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains

# Telegram Bot API Token and Chat ID
BOT_API_TOKEN = "YOUR_TELEGRAM_BOT_API_TOKEN"  # Write your Telegram bot's API token here
CHAT_ID = "YOUR_CHAT_ID"   # Write your Telegram chat ID here

# Function that sends a message to the Telegram API
def send_telegram_notification(message):
    try:
        url = f"https://api.telegram.org/bot{BOT_API_TOKEN}/sendMessage"
        params = {
            "chat_id": CHAT_ID,
            "text": message
        }
        response = requests.get(url, params=params)
        if response.status_code == 200:
            print("Telegram notification sent!")
        else:
            print(f"Error sending notification: {response.status_code}")
    except Exception as e:
        print(f"Error sending notification: {e}")

# ChromeDriver path (update this path to your actual ChromeDriver location)
service = Service("YOUR_CHROMEDRIVER_PATH") 

# Brave Browser setup
brave_path = "YOUR_BRAVE_BROWSER_PATH"  # Type the Brave browser path here 
options = Options()
options.binary_location = brave_path
options.add_argument("--disable-blink-features=AutomationControlled")


url = "YOUR_API_URL"  # Insert the appointment control URL here

# Target Date: blablabla
target_date = "2029-09-09"  

# Function to get CSRF token and cookies from the browser
def get_csrf_token_and_cookies(driver):
    cookies = driver.get_cookies()
    csrf_token = driver.execute_script("return window._csrf_token;")  
    cookies_dict = {cookie['name']: cookie['value'] for cookie in cookies}
    return csrf_token, cookies_dict


def check_appointments():
    driver = None
    try:
      
        driver = webdriver.Chrome(service=service, options=options)

        # Target URL
        driver.get("https://ais.usvisa-info.com/{EmbassyLocationCode}/niv/users/sign_in") #  Embassy location code = Like en-ca / tr-tr 
        print("Loading the login page...")

        # Login process
        print("Waiting for the login form...")
        email_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "user_email"))  
        )
        password_field = driver.find_element(By.ID, "user_password")
        terms_checkbox = driver.find_element(By.ID, "policy_confirmed")  # Tick the checkbox
        login_button = driver.find_element(By.NAME, "commit")

       
        print("Entering credentials...")
        email_field.send_keys("YOUR_EMAIL")  # US Embassy account details
        password_field.send_keys("YOUR_PASSWORD")  # US Embassy password

        print("Ticking the terms and conditions checkbox...")
        driver.execute_script("document.getElementById('policy_confirmed').click();")

        print("Submitting the login form...")
        login_button.click()

        print("Login successful. Navigating to the continue actions page...")
        driver.get("https://ais.usvisa-info.com/{EmbassyLocationCode/niv/schedule/{SCHEDULE_ID}/continue_actions") # Schedule ID and Embassy location code inside the URL
        print("Continue actions page loaded.")

        # Navigate to the appointment page
        driver.get("https://ais.usvisa-info.com/{EmbassyLocationCode}r/niv/schedule/{SCHEDULE_ID}/appointment")  # Schedule ID and Embassy location code inside the URL
        print("Appointment page loaded. Checking appointments...")

        # Click on the facility dropdown and select the desired option (City)
        driver.execute_script("document.querySelector('#appointments_consulate_appointment_facility_id > option:nth-child(3)').click();")
        print("Embassy selected.")

        WebDriverWait(driver, 30).until(
            lambda driver: driver.execute_script('return document.readyState') == 'complete'
        )
        print("Page is fully loaded.")

        date_field = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "#appointments_consulate_appointment_date"))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", date_field)
        driver.execute_script("arguments[0].click();", date_field)

       
        csrf_token, cookies_dict = get_csrf_token_and_cookies(driver)

        headers = {                                  # For this section you need to take your own API headers you can easily take it from Network section on when you login your account.
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "{EmbassyLocationCode},{EmbassyLocationCode};q=0.7",         # Like en-CA  ,  #en                       
            "Connection": "keep-alive",
            "Referer": "https://ais.usvisa-info.com/{EmbassyLocationCode}/niv/schedule/{SCHEDULE_ID}/appointment", # Schedule ID and Embassy location code inside the URL
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "Sec-GPC": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "X-CSRF-Token": csrf_token,
            "X-Requested-With": "XMLHttpRequest",
        }

        print("Fetching available dates from API...")
        response = requests.get(url, headers=headers, cookies=cookies_dict)

        if response.status_code == 200:
            available_dates = response.json() 
            
            if available_dates and len(available_dates) > 0:
                # Filter dates before the target date (2029-09-09)
                filtered_dates = [date for date in available_dates if datetime.strptime(date['date'], '%Y-%m-%d') <= datetime.strptime(target_date, '%Y-%m-%d')]
                
                if filtered_dates:
                    print(f"Appointment available on {filtered_dates[0]['date']}.")

                    # Send Telegram notification for the first available appointment
                    send_telegram_notification(f"An available appointment has been found on {filtered_dates[0]['date']}. Please check it out.")
                    print("First available appointment found. Closing browser...")

                    # Only process the first available appointment and stop further checks
                    return
                else:
                    print(f"No available dates found before {target_date}.")
            else:
                print("No available dates found.")
        else:
            print("Failed to fetch available dates from API. Status code:", response.status_code)

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        # Ensure the browser is closed after the operation
        if driver:
            print("Closing the browser...")
            driver.quit()


while True:
    check_appointments()

    # Wait for a random time between 10 to 15 minutes ( This section important for web site security otherwise you might be banned from the site )
    wait_time = random.randint(600, 900)  # Random time in seconds (10-15 minutes)
    print(f"Waiting for {wait_time // 60} minutes before the next check...")
    time.sleep(wait_time)
