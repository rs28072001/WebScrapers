# Creator: D&I
# This script downloads Federal Energy Regulatory Commission (FERC) Audit Reports.
# The audit reports cover fiscal year 2015 to current.The audit reports detail audit 
# findings of noncompliance and audit staff recommendations for corrective actions 
# in which jurisdictional companies developed robust compliance plans to implement. 
# Audit staff monitors implementation of all of these recommendations until they are properly implemented. 


# required imports
import os,logging,traceback,time,datetime
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from sys import platform
import selenium
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service


# source url
masterUrl = 'https://www.ferc.gov/audits'
everylink = []  
savedFile_directory = r''


log_path = "FERC.log"
# Logging implement settings
logging.basicConfig(filename=log_path, filemode='a', format='%(asctime)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


chrome_version='112.0.5615.121'
'''
get respective user agent depending upon the platform
'''


def get_user_agent():
    if platform == 'linux' or platform == 'linux2':
        user_agent = '--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/' + chrome_version + ' Safari/537.36'
    elif platform == 'win32':
        user_agent = '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/' + chrome_version + ' Safari/537.36'
    
    return (user_agent)
    

def get_driver(url):
    if platform == 'linux' or platform == 'linux2':
        driver_path = r'/usr/local/bin/chromedriver'
    elif platform == 'win32':
        driver_path = r'C:/chrome driver/chromedriver.exe'
    logger.info("chrome driver initiated !")
    ser = Service(driver_path)
    # configure Chrome Options
    options = Options()
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-extensions')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument(get_user_agent())
    options.add_argument('--run-all-compositor-stages-before-draw')
    options.add_argument('--disable-impl-side-painting')
    options.add_argument('--disable-gpu-sandbox')
    options.add_argument('--run-all-compositor-stages-before-draw')
    options.add_argument('--disable-accelerated-2d-canvas')
    options.add_argument('--disable-accelerated-jpeg-decoding')
    options.add_argument('--test-type=ui')
    options.add_argument('--allow-insecure-localhost')
    # chrome_options = webdriver.ChromeOptions()
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--disable-infobars")
    options.add_experimental_option("prefs", {
    "download.default_directory": os.path.abspath(directory_path),
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "plugins.always_open_pdf_externally": True
        })

    try:
        driver = webdriver.Chrome(
            service=ser, options=options)
        time.sleep(2)
        return driver
    except Exception as e:
        errmsg = str(e)
        logging.error(
            'Exception Occurred for {}, (Chrome webdriver issue - Crash) in 1st try: {}'.format(url, errmsg))
        time.sleep(5)
        try:
            driver = webdriver.Chrome(
                service=ser, options=options)
            time.sleep(2)
            return driver
        except Exception as e:
            errmsg = str(e)
            logging.error(
                'Exception Occurred for {}, (Chrome webdriver issue - Crash) in 2nd try: {}'.format(url, errmsg))

# function to create folder per source name.
def create_website_folder(url, sub_folder):
    global directory_path
    domain_name = urlparse(url).netloc   # Get the domain name from the URL using urlparse
    folder_name = domain_name.replace(".", "_") + '_Audits'   # Replace any periods in the domain name with underscores
    directory_path = os.path.join(savedFile_directory, folder_name, sub_folder)   # Create a new path with the original directory and the new directory
    if not os.path.exists(directory_path):   # Check if the directory already exists
        os.makedirs(directory_path)   # Create the directory if it doesn't exist
        logger.info(f"Created directory: {directory_path}")
    else:
        logger.info(f"Directory already exists: {directory_path}")

create_website_folder(masterUrl, str('PDF Files'))


def process_audit():
    try:
        logging.info('Opening the URL in the Chrome Browser')
        driver = get_driver(masterUrl)
        if driver:
            driver.get(masterUrl)
            logging.info('Collecting HTML Source from the Webpage')
            element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="audit-page-tabs---new-tab-content-0"]')))
            def GetPageSource():
                html = driver.page_source
                soup = BeautifulSoup(html, 'html.parser')   # Parse the HTML using BeautifulSoup
                if soup != '':
                    toggle_content_links = soup.find_all("div", class_="toggle__content toggle__content--show")
                    for toggle_content in toggle_content_links:
                        links = toggle_content.find_all("a")
                        for link in links:
                            pdflink = (link.get("href"))
                            everylink.append(pdflink)

            for year in range(5):
                if year == 0:
                    makeSubF = 2023
                elif year == 1:
                    makeSubF = 2022
                elif year == 2:
                    makeSubF = 2021
                elif year == 3:
                    makeSubF = 2020
                elif year == 4:
                    makeSubF = 2019
                # create_website_folder(masterUrl, str(makeSubF))
                logger.info(f'Working On {makeSubF} ')
                time.sleep(1)
                GetPageSource()
                generatePDF(driver)
                everylink.clear()
                if year == 3:
                    break
                driver.find_element(By.XPATH,f'//*[@id="audit-page-tabs---new-tab-{year+1}"]').click()
            time.sleep(2)
            driver.close()
    except:
        logger.error("Press releases urls couldn't be fetched from master page url : " + masterUrl)
        traceback.print_exc()

def generatePDF(driver):
    download_btn = '//*[@id="main"]/app-filelist/section/div[1]/table/tbody/tr/td[1]/div/a'
    
    # Open a new window
    driver.execute_script("window.open('');")
    # Switch to the new window and open new URL
    driver.switch_to.window(driver.window_handles[1])
    count = 1
    for url in everylink:
        driver.get(url)
        element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, download_btn)))
        driver.find_element(By.XPATH,download_btn).click()
        # wait for downloads to complete
        logger.info("Waiting for downloads to complete...")
        wait = WebDriverWait(driver, 30)  # wait up to 30 seconds for downloads to complete
        download_path = os.path.abspath(directory_path)
        downloaded_files = os.listdir(directory_path)
        count = len(downloaded_files)
        while True:
            if count < len((os.listdir(directory_path))):
                break
        count = count + 1        
        # check if PDF files have been downloaded
        for filename in downloaded_files:
            if filename.endswith(".pdf"):
                logger.info(f"Downloaded: {filename}")
            else:
                logger.info(f"Not downloaded: {filename}")
        logger.info(f"PDF files have been downloaded...Total Files:{count}")
    driver.close()
    driver.switch_to.window(driver.window_handles[0])

#Execution starts here
if __name__ == '__main__':
    logger.info('Starting script- FERC_gov.py')
    t1 = time.time()
    try:
        #Calling Func to Fetch Data from the Websites
        process_audit()
        logger.info('Script Completed')
        logging.info('Total time took for complete run is {}'.format(time.time() - t1))

    except Exception as e:
        logger.error("Master Page urls couldn't be fetched, PDF conditions does not meet")
        traceback.print_exc()
