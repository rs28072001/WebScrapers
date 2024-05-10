import logging,traceback,time,os
from selenium import webdriver
from urllib.parse import urlparse
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

masterUrl = 'https://apps.occ.gov/EASearch'
ExportUrl = 'https://apps.occ.gov/EASearch/Search/ExportToPdf?Search=&Category=&ItemsPerPage=1000&Sort=&AutoCompleteSelection='
savedFile_directory = r''# Set You PDFs File Directory

# Emptying root.handlers before calling basicConfig() method
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

# Logging implement settings
log_path = "occ.log"   #Set Your Path for Log File  
logging.basicConfig(filename=log_path, filemode='w', format='%(asctime)s - %(levelname)s - %(message)s',
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

def create_website_folder(url, sub_folder):
    global directory_path
    domain_name = urlparse(url).netloc   # Get the domain name from the URL using urlparse
    folder_name = domain_name.replace(".", "_")  # Replace any periods in the domain name with underscores
    directory_path = os.path.join(savedFile_directory, folder_name, sub_folder)   # Create a new path with the original directory and the new directory
    if not os.path.exists(directory_path):   # Check if the directory already exists
        os.makedirs(directory_path)   # Create the directory if it doesn't exist
        logger.info(f"Created directory: {directory_path}")
    else:
        logger.info(f"Directory already exists: {directory_path}")

create_website_folder(masterUrl, str('PDF Files'))    

def get_driver(url):
    if platform == 'linux' or platform == 'linux2':
        driver_path = r'/usr/local/bin/chromedriver'
    elif platform == 'win32':
        driver_path = r"C:\Users\HOME\Desktop\Script By Ashish\chromedriverFDA Script\chromedriver.exe"
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



#This function processes each each articles and Extract the date,title,link of the press_releases.
def process_webpages():
    try:
        logging.info('Opening the URL in the Chrome Browser')
        driver = get_driver(masterUrl)
        if driver:
            driver.get(ExportUrl)
            logging.info('Collecting HTML Source from the Webpage')
            logger.info("Waiting for downloads to complete...")
            downloaded_files = os.listdir(directory_path)
            count = len(downloaded_files)
            while True:
                for filename in os.listdir(directory_path):
                        print(f"File Name: {filename}")
                        if filename.endswith(".pdf"):
                            logger.info(f"Downloaded: {filename}")
                            fileload = True
                        else:
                            fileload = False
                if fileload:
                        break
            # check if PDF files have been downloaded
            for filename in downloaded_files:
                if filename.endswith(".pdf"):
                    logger.info(f"Downloaded: {filename}")
                else:
                    logger.info(f"Not downloaded: {filename}")
            logger.info(f"PDF files have been downloaded...Total Files:{count}")
        driver.close()
    except:
        logger.error("Press releases urls couldn't be fetched from master page url : " + masterUrl)
        traceback.print_exc()

#Execution starts here
if __name__ == '__main__':
    logger.info('Starting script- occ__gov.py')
    t1 = time.time()
    try:
        #Calling Func to Fetch Data from the Websites
        process_webpages()
        logger.info('Script Completed')
        logging.info('Total time took for complete run is {}'.format(time.time() - t1))
    except Exception as e:
        logger.error("Master Page urls couldn't be fetched, PDF conditions does not meet")
        traceback.print_exc()
