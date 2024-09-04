from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.edge.options import Options
from time import sleep
from captcha_reader import read_captcha
from PIL import Image
from io import BytesIO
import csv

def config(username, password, browser):
    global conf_username, conf_password, conf_browser
    conf_username = username
    conf_password = password
    conf_browser = browser

def driver_init(self):
    # Initialize the WebDriver
    driver_options = Options()
    driver_options.add_argument("--headless")
    driver_options.add_argument("--disable-gpu")

    if conf_browser == "Chrome":
        driver = webdriver.Chrome(options=driver_options)
    elif conf_browser == "Firefox":
        driver = webdriver.Firefox(options=driver_options)
    elif conf_browser == "Edge":
        driver = webdriver.Edge(options=driver_options)

    self.log_message("[Initialized WebDriver: " + conf_browser + "]")
    return driver

def check_abort(self, action):
    """ Helper function to check if the abort flag is set, and exit the process if true. """
    global abort_flag
    if abort_flag:
        self.log_message(f"[Aborting {action}]")
        return True
    return False

def login(self, driver):
    # Global abort flag
    global abort_flag
    abort_flag = False

    self.log_message("[LOGGING IN]")

    # Go to the login page
    driver.get("https://students.unpad.ac.id/pacis/mhs_login")
    self.log_message("Navigated to the login page.")

    # Enter the username
    username_input = driver.find_element(By.NAME, "username")
    username_input.send_keys(conf_username)
    self.log_message("Entered username.")

    while True:
        if check_abort(self, "login"):
            return False

        # Enter the password
        password_input = driver.find_element(By.NAME, "password")
        password_input.send_keys(conf_password)
        self.log_message("Entered password.")
        
        # Get the CAPTCHA image element
        sleep(0.2)  # Wait for captcha image to load
        captcha_img = driver.find_element(By.XPATH, '//img[@alt="  [150x50]"]')
        captcha_src = captcha_img.get_attribute("src")
        
        # Screenshot the CAPTCHA image
        captcha_screenshot = captcha_img.screenshot_as_png
        captcha_image = Image.open(BytesIO(captcha_screenshot))
        self.log_message("Captured CAPTCHA image from session.")
        captcha_text = read_captcha(captcha_image)
        
        # Enter the CAPTCHA text
        captcha_input = driver.find_element(By.NAME, "captcha")
        captcha_input.send_keys(captcha_text)
        self.log_message("Entered CAPTCHA text.")
        
        # Press the login button
        login_button = driver.find_element(By.XPATH, '//button[contains(@class, "ui blue fluid huge compact button")]')
        login_button.click()
        self.log_message("Clicked login button.")
        
        # Check if the login was successful or if CAPTCHA was incorrect
        try:
            # Wait for the authorization page to load, which means login was successful
            WebDriverWait(driver, 1).until(EC.url_contains("https://paus.unpad.ac.id/oauth/authorize"))
            self.log_message("Login successful.")
            
            # Click the "Izinkan" button
            izinkan_button = driver.find_element(By.XPATH, '//button[contains(@class, "btn-approve ui blue button")]')
            izinkan_button.click()
            self.log_message("Clicked 'Izinkan' button.")
            
            # Wait for the homepage to load
            WebDriverWait(driver, 10).until(EC.url_contains("https://students.unpad.ac.id/pacis/mhs_home"))
            self.log_message("Navigated to the homepage.")
            
            break  # Exit the loop as the login was successful
        
        except Exception as e:
            self.log_message("Login failed, likely due to incorrect CAPTCHA. Retrying...")
            if check_abort(self, "login retry"):
                return False
            continue

def generate_schedule(self):
    # Global abort flag
    global abort_flag
    abort_flag = False
    
    self.log_message("[GENERATING JADWAL TO 'schedule.csv']")

    # Initialize the WebDriver
    driver = driver_init(self)

    # Login to the web
    login(self, driver)
    
    if check_abort(self, "schedule generation"):
        driver.quit()
        return False

    # Open the page
    driver.get("https://students.unpad.ac.id/pacis/akademik/jadwal")
    self.log_message("Navigated to the jadwal page.")

    # Locate the table rows
    rows = driver.find_elements(By.XPATH, "//table[@id='tbl2']/tbody/tr")

    # Prepare the CSV file
    with open('schedule.csv', mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        # Write the header
        writer.writerow(["No", "Hari", "Jam Absen", "Matkul", "ID Matkul"])

        # Iterate over each row in the table
        for row in rows[1:]:
            # Extract the data
            no = row.find_element(By.XPATH, "./td[1]").text.strip()
            hari = row.find_element(By.XPATH, "./td[2]").text.strip()
            waktu = row.find_element(By.XPATH, "./td[3]").text.strip()
            matkul = row.find_element(By.XPATH, "./td[5]").text.strip()
            
            # Extract the start time
            jam_absen = waktu.split(" - ")[0]
            
            # Extract the "ID Matkul" from the attendance detail link
            attendance_detail_link = row.find_element(By.XPATH, "./td[10]/a").get_attribute("href")
            id_matkul = attendance_detail_link.split("/")[-1]

            # Write the row to the CSV
            writer.writerow([no, hari, jam_absen, matkul, id_matkul])
        
        self.log_message("Data extraction complete. Check 'schedule.csv' for the output.")

    # Close the WebDriver
    driver.quit()

def absent(self, id):
    # Global abort flag
    global abort_flag
    abort_flag = False
    
    self.log_message(f"[PROCESSING ATTEND FOR MATKUL ID {id}]")

    while True:
        if check_abort(self, f"attend for Matkul ID {id}"):
            return False

        try:
            # Initialize the WebDriver
            driver = driver_init(self)

            # Login to the web
            login(self, driver)
            if check_abort(self, "login during attend"):
                driver.quit()
                return False

            # Go to matkul attendance page
            driver.get(f"https://students.unpad.ac.id/pacis/akademik/jadwal/detail/{id}")
            self.log_message("Navigated to the matkul attendance page.")

            # Locate the form element
            form = driver.find_element(By.TAG_NAME, "form")
            self.log_message("Form element found.")

            # Get the value of the 'action' attribute
            form_attend_url = form.get_attribute("action")

            # Go to form_attend_url to attend
            driver.get(form_attend_url)

            # Check for abort before waiting for the URL to load
            if check_abort(self, "before attending"):
                driver.quit()
                return False

            try:
                # Wait for absent process to be successful and return to matkul attendance page
                WebDriverWait(driver, 10).until(EC.url_contains(f"https://students.unpad.ac.id/pacis/akademik/jadwal/detail/{id}"))
                self.log_message("Attend absent successful.")
                
                # Close the WebDriver
                driver.quit()
                return True

            except Exception as e:
                self.log_message(f"Attend absent failed. Error: {str(e)}")

        except Exception as e:
            driver.quit()
            
            # Handle the case where the form is not found
            total_seconds = 600  # 10 minutes

            while total_seconds > 0:
                if check_abort(self, f"retry for Matkul ID {id}"):
                    return False
                
                minutes, seconds = divmod(total_seconds, 60)
                countdown_time = f"{minutes:02d}:{seconds:02d}"

                # Update the log message with the countdown
                self.log_message(f"Absent form element not found. Retrying in {countdown_time}")
                
                # Wait for 1 second
                sleep(1)
                
                # Decrement the total seconds
                total_seconds -= 1

def abort(self):
    global abort_flag
    abort_flag = True
    self.log_message("Abort signal sent.")