#! python3
# -*- coding: utf-8 -*-
"""Job Portal Daily update - Using Chrome"""

import io
import logging
import os
import sys
import time
from datetime import datetime
from random import choice, randint
from string import ascii_uppercase, digits

from pypdf import PdfReader, PdfWriter
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException

from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager as CM

import boto3
from dotenv import load_dotenv

load_dotenv()

# Add folder Path of your resume
originalResumePath = os.getenv("INPUT_FILE")
# Add Path where modified resume should be saved
modifiedResumePath = os.getenv("OUTPUT_FILE")

# Update your username and password here before running
username = os.getenv("USER_NAME")
password = os.getenv("PWD")
mob = os.getenv("MOBILE")  # Type your mobile number here

# False if you dont want to add Random HIDDEN chars to your resume
UPDATE_PDF = True

# If Headless = True, script runs Chrome in headless mode without visible GUI
HEADLESS = True

# ----- No other changes required -----

# Set login URL
URL = "https://www.naukri.com/nlogin/login"

logging.basicConfig(
    level=logging.INFO, filemode="w", filename="logs.log", format="%(asctime)s    : %(message)s"
)
# logging.disable(logging.CRITICAL)
os.environ["WDM_LOCAL"] = "1"
os.environ["WDM_LOG_LEVEL"] = "0"


def log_msg(message):
    """Print to console and store to Log"""
    print(message)
    logging.info(message)


def catch(error):
    """Method to catch errors and log error details"""
    _, _, exc_tb = sys.exc_info()
    line_no = str(exc_tb.tb_lineno)
    msg = "%s : %s at Line %s." % (type(error), error, line_no)
    print(msg)
    logging.error(msg)


def get_obj(locator_type):
    """This map defines how elements are identified"""
    identifier_map = {
        "ID": By.ID,
        "NAME": By.NAME,
        "XPATH": By.XPATH,
        "TAG": By.TAG_NAME,
        "CLASS": By.CLASS_NAME,
        "CSS": By.CSS_SELECTOR,
        "LINKTEXT": By.LINK_TEXT,
    }
    return identifier_map[locator_type.upper()]


def get_element(driver, element_tag, locator="ID"):
    """Wait max 15 secs for element and then select when it is available"""
    try:

        def _get_element(_tag, _locator):
            _by = get_obj(_locator)
            if is_element_present(driver, _by, _tag):
                return WebDriverWait(driver, 15).until(
                    lambda d: driver.find_element(_by, _tag)
                )

        element = _get_element(element_tag, locator.upper())
        if element:
            return element
        else:
            log_msg("Element not found with %s : %s" % (locator, element_tag))
            return None
    except Exception as e:
        catch(e)
    return None


def is_element_present(driver, how, what):
    """Returns True if element is present"""
    try:
        driver.find_element(by=how, value=what)
    except NoSuchElementException:
        return False
    return True


def wait_till_element_present(driver, element_tag, locator="ID", timeout=30):
    """Wait till element present. Default 30 seconds"""
    result = False
    driver.implicitly_wait(0)
    locator = locator.upper()

    for _ in range(timeout):
        time.sleep(0.99)
        try:
            if is_element_present(driver, get_obj(locator), element_tag):
                result = True
                break
        except Exception as e:
            log_msg("Exception when wait_till_element_present : %s" % e)
            pass

    if not result:
        log_msg("Element not found with %s : %s" % (locator, element_tag))
    driver.implicitly_wait(3)
    return result


def tear_down(driver):
    try:
        driver.close()
        log_msg("Driver Closed Successfully")
    except Exception as e:
        catch(e)
        pass

    try:
        driver.quit()
        log_msg("Driver Quit Successfully")
    except Exception as e:
        catch(e)
        pass


def random_text():
    return "".join(choice(ascii_uppercase + digits) for _ in range(randint(1, 5)))


def load_website(headless):
    """Open Chrome to load website"""
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-notifications")
    options.add_argument("--start-maximized")  # ("--kiosk") for MAC
    options.add_argument("--disable-popups")
    options.add_argument("--disable-gpu")
    if headless:
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--headless=new")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--no-sandbox")
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--allow-running-insecure-content')
        user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.50 Safari/537.36'
        options.add_argument(f'user-agent={user_agent}')
        
    # updated to use ChromeDriverManager to match correct chromedriver automatically
    driver = None
    try:
        driver = webdriver.Chrome(options, service=ChromeService(
            CM(driver_version="130.0.6723.69").install()))
        # driver = webdriver.Remote(command_executor='http://3.110.37.99:4444/wd/hub',options=options)
    except:
        driver = webdriver.Chrome(options)
    log_msg("Google Chrome Launched!: %s" %driver.capabilities['chrome']['chromedriverVersion'].split(' ')[0])

    driver.implicitly_wait(3)
    driver.get(URL)
    return driver


def site_login(headless=False):
    """Open Chrome browser and Login to site"""
    status = False
    driver = None
    username_locator = "usernameField"
    password_locator = "passwordField"
    login_btn_locator = "//*[@type='submit' and normalize-space()='Login']"
    skip_locator = "//*[text() = 'SKIP AND CONTINUE']"

    try:
        driver = load_website(headless)
        # driver.get_screenshot_as_file("screen.png")
        if "naukri" in driver.title.lower():
            log_msg("Website Loaded Successfully.")

        email_field_element = None
        if is_element_present(driver, By.ID, username_locator):
            email_field_element = get_element(
                driver, username_locator, locator="ID")
            time.sleep(1)
            pass_field_element = get_element(
                driver, password_locator, locator="ID")
            time.sleep(1)
            login_button = get_element(
                driver, login_btn_locator, locator="XPATH")
        else:
            log_msg("Login Form Elements Not Found")

        if email_field_element is not None:
            email_field_element.clear()
            email_field_element.send_keys(username)
            time.sleep(1)
            pass_field_element.clear()
            pass_field_element.send_keys(password)
            time.sleep(1)
            login_button.send_keys(Keys.ENTER)
            time.sleep(1)

            # Added click to Skip button
            print("Checking Skip button")

            if wait_till_element_present(driver, skip_locator, "XPATH", 10):
                get_element(driver, skip_locator, "XPATH").click()

            # CheckPoint to verify login
            if wait_till_element_present(driver, "ff-inventory", locator="ID", timeout=40):
                check_point = get_element(driver, "ff-inventory", locator="ID")
                if check_point:
                    log_msg("Site Login Successful")
                    status = True
                    return (status, driver)
                else:
                    log_msg("Unknown Login Error")
                    return (status, driver)
            else:
                log_msg("Unknown Login Error")
                return (status, driver)
        else:
            log_msg("Email Element Not Found")

    except Exception as e:
        catch(e)
    return (status, driver)


def UpdateProfile(driver):
    try:
        mobXpath = "//*[@name='mobile'] | //*[@id='mob_number']"
        saveXpath = "//button[@ type='submit'][@value='Save Changes'] | //*[@id='saveBasicDetailsBtn']"
        view_profile_locator = "//*[contains(@class, 'view-profile')]//a"
        edit_locator = "(//*[contains(@class, 'icon edit')])[1]"
        save_confirm = "//*[text()='today' or text()='Today']"
        close_locator = "//*[contains(@class, 'crossIcon')]"

        wait_till_element_present(driver, view_profile_locator, "XPATH", 20)
        profElement = get_element(driver, view_profile_locator, locator="XPATH")
        profElement.click()
        driver.implicitly_wait(2)

        if wait_till_element_present(driver, close_locator, "XPATH", 10):
            get_element(driver, close_locator, locator="XPATH").click()
            time.sleep(2)

        wait_till_element_present(driver, edit_locator +
                               " | " + saveXpath, "XPATH", 20)
        if is_element_present(driver, By.XPATH, edit_locator):
            editElement = get_element(driver, edit_locator, locator="XPATH")
            editElement.click()

            wait_till_element_present(driver, mobXpath, "XPATH", 20)
            mobFieldElement = get_element(driver, mobXpath, locator="XPATH")
            if mobFieldElement:
                mobFieldElement.clear()
                mobFieldElement.send_keys(mob)
                driver.implicitly_wait(2)

                saveFieldElement = get_element(
                    driver, saveXpath, locator="XPATH")
                saveFieldElement.send_keys(Keys.ENTER)
                driver.implicitly_wait(3)
            else:
                log_msg("Mobile number element not found in UI")

            wait_till_element_present(driver, save_confirm, "XPATH", 10)
            if is_element_present(driver, By.XPATH, save_confirm):
                log_msg("Profile Update Successful")
            else:
                log_msg("Profile Update Failed")

        elif is_element_present(driver, By.XPATH, saveXpath):
            mobFieldElement = get_element(driver, mobXpath, locator="XPATH")
            if mobFieldElement:
                mobFieldElement.clear()
                mobFieldElement.send_keys(mob)
                driver.implicitly_wait(2)

                saveFieldElement = get_element(
                    driver, saveXpath, locator="XPATH")
                saveFieldElement.send_keys(Keys.ENTER)
                driver.implicitly_wait(3)
            else:
                log_msg("Mobile number element not found in UI")

            wait_till_element_present(
                driver, "confirmMessage", locator="ID", timeout=10)
            if is_element_present(driver, By.ID, "confirmMessage"):
                log_msg("Profile Update Successful")
            else:
                log_msg("Profile Update Failed")

        time.sleep(5)

    except Exception as e:
        catch(e)


def UpdateSkills(driver):
    try:
        view_profile_locator = "//*[contains(@class, 'view-profile')]//a"
        close_locator = "//*[contains(@class, 'crossIcon')]"
        skill_edit_locator = "(//span[@class='edit icon'])[2]"
        modal_close_icon_locator = "//div[@class='lightbox profileEditDrawer keySkillsEdit model_open flipOpen']//span[@class='icon'][normalize-space()='CrossLayer']"
        skill_locator = "//div[@title='YARN']"
        skill_remove_locator = "//div[@title='YARN']//a[@class='material-icons close'][normalize-space()='Cross']"
        skill_field_locator = "//input[@id='keySkillSugg']"
        skill_drop_down_locator = "(//div[@class='Sbtn sAct'])[1]"
        skill_save_locator = "//button[@id='saveKeySkills']"
        save_confirm = "//i[normalize-space()='GreenTick']"

        wait_till_element_present(driver, view_profile_locator, "XPATH", 20)
        profElement = get_element(driver, view_profile_locator, locator="XPATH")
        profElement.click()

        if wait_till_element_present(driver, close_locator, "XPATH", 10):
            get_element(driver, close_locator, locator="XPATH").click()
            time.sleep(2)

        wait_till_element_present(driver, skill_edit_locator, "XPATH", 20)
        if is_element_present(driver, By.XPATH, skill_edit_locator):
            skillEditElement = get_element(
                driver, skill_edit_locator, locator="XPATH")
            skillEditElement.click()
            time.sleep(2)

            if is_element_present(driver, By.XPATH, modal_close_icon_locator):

                # if skillElement:
                #     #if skill present then remove
                #     print("Skill Found")
                #     remove_icon = get_element(driver, skill_remove_locator, locator="XPATH")
                #     remove_icon.click()
                #     time.sleep(2)
                # else:
                #     #if skill absent then add
                #     print("Skill not Found")
                #     skill_field = get_element(driver, skill_field_locator, locator="XPATH")
                #     time.sleep(2)
                #     skill_field.clear()
                #     skill_field.send_keys("YARN")
                #     skill_item = get_element(driver, skill_drop_down_locator, locator="XPATH")
                #     time.sleep(2)
                #     skill_item.click()

                save_button = get_element(
                    driver, skill_save_locator, locator="XPATH")
                save_button.click()

            wait_till_element_present(driver, save_confirm, "XPATH", 10)
            if is_element_present(driver, By.XPATH, save_confirm):
                log_msg("Profile Update Successful")
            else:
                log_msg("Profile Update Failed")

    except Exception as e:
        catch(e)


def UpdateResume():
    try:
        # random text with with random location and size
        txt = random_text()
        xloc = randint(700, 1000)  # this ensures that text is 'out of page'
        fsize = randint(1, 10)

        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=letter)
        can.setFont("Helvetica", fsize)
        can.drawString(xloc, 100, "lon")
        can.save()

        packet.seek(0)
        new_pdf = PdfReader(packet)
        existing_pdf = PdfReader(open(originalResumePath, "rb"))
        pagecount = len(existing_pdf.pages)
        log_msg("Found %s pages in PDF" % pagecount)

        output = PdfWriter()
        # Merging new pdf with last page of my existing pdf
        # Updated to get last page for pdf files with varying page count
        for pageNum in range(pagecount - 1):
            output.add_page(existing_pdf.pages[pageNum])
        page = existing_pdf.pages[pagecount - 1]
        page.merge_page(new_pdf.pages[0])
        output.add_page(page)
        # save the new resume file
        with open(modifiedResumePath, "wb") as outputStream:
            output.write(outputStream)
        log_msg("Saved modified PDF : %s" % modifiedResumePath)
        return os.path.abspath(modifiedResumePath)
    except Exception as e:
        catch(e)
    return os.path.abspath(originalResumePath)


def UploadResume(driver, resumePath):
    try:
        attachCVID = "attachCV"
        CheckPointXpath = "//*[contains(@class, 'updateOn')]"
        saveXpath = "//button[@type='button']"
        close_locator = "//*[contains(@class, 'crossIcon')]"

        driver.get("https://www.naukri.com/mnjuser/profile")

        time.sleep(2)
        if wait_till_element_present(driver, close_locator, "XPATH", 10):
            get_element(driver, close_locator, locator="XPATH").click()
            time.sleep(2)

        wait_till_element_present(driver, attachCVID, locator="ID", timeout=10)
        AttachElement = get_element(driver, attachCVID, locator="ID")
        AttachElement.send_keys(os.path.abspath(resumePath))

        if wait_till_element_present(driver, saveXpath, locator="ID", timeout=5):
            saveElement = get_element(driver, saveXpath, locator="XPATH")
            saveElement.click()

        wait_till_element_present(driver, CheckPointXpath,
                               locator="XPATH", timeout=30)
        CheckPoint = get_element(driver, CheckPointXpath, locator="XPATH")
        if CheckPoint:
            LastUpdatedDate = CheckPoint.text
            todaysDate1 = datetime.today().strftime("%b %d, %Y")
            todaysDate2 = datetime.today().strftime("%b %#d, %Y")
            print("LastUpdatedDate",LastUpdatedDate)
            print("todaysDate1",todaysDate1)
            print("todaysDate2",todaysDate2)
            if todaysDate1 in LastUpdatedDate or todaysDate2 in LastUpdatedDate:
                log_msg(
                    "Resume Document Upload Successful. Last Updated date = %s"
                    % LastUpdatedDate
                )
            else:
                log_msg(
                    "Resume Document Upload failed. Last Updated date = %s"
                    % LastUpdatedDate
                )
        else:
            log_msg("Resume Document Upload failed. Last Updated date not found.")

    except Exception as e:
        catch(e)
    time.sleep(2)


def mail_logs():
    sns_client = boto3.client(
        'sns',
        region_name=os.getenv("AWS_REGION"),
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
    )
    # Read log file content
    with open('logs.log', 'r') as file:
        log_content = file.read()

    # Publish the message
    response = sns_client.publish(
        TopicArn=os.getenv("SNS_TOPIC"),
        Message=log_content
    )
    print("Message sent! Message ID:", response['MessageId'])


def main():
    log_msg("-----main.py Script Run Begin-----")
    driver = None
    try:
        status, driver = site_login(HEADLESS)
        if status:
            # UpdateProfile(driver)
            UpdateSkills(driver)
            if os.path.exists(originalResumePath):
                if UPDATE_PDF:
                    resume_path = UpdateResume()
                    UploadResume(driver, resume_path)
                else:
                    UploadResume(driver, originalResumePath)
            else:
                log_msg("Resume not found at %s " % originalResumePath)
        else:
            log_msg("Site Login Failed")

    except Exception as e:
        catch(e)

    finally:
        mail_logs()
        tear_down(driver)

    log_msg("-----main.py Script Run Ended-----\n")


if __name__ == "__main__":
    main()
