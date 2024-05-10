import requests,os,logging,traceback,time,datetime
from urllib.parse import urlparse
from urllib.parse import urljoin
from urllib.parse import unquote
from bs4 import BeautifulSoup
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from sys import platform
import selenium
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

masterUrl = 'https://pcaobus.org/oversight/enforcement/enforcement-actions?pg=1&mpp=96'
baseURL = 'https://assets.pcaobus.org'
PDFs = []

PDFs_Saving_dir = r''

# Emptying root.handlers before calling basicConfig() method
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

# Logging implement settings
log_path = "pcao.log"   #Set Your Path for Log File  
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
    

def get_driver(url):
    if platform == 'linux' or platform == 'linux2':
        driver_path = r'/usr/local/bin/chromedriver'
    elif platform == 'win32':
        driver_path = r"C:\Users\HOME\Desktop\Script By Ashish\chromedriverFDA Script\chromedriver.exe"
    logger.info("chrome driver instantiated !")
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

def create_website_folder(url):
    global folder_name
    domain_name = urlparse(url).netloc   # Get the domain name from the URL using urlparse
    folder = domain_name.replace(".", "_")   # Replace any periods in the domain name with underscores
    folder_name = os.path.join(PDFs_Saving_dir, folder)   # Create a new path with the original directory and the new directory
    if not os.path.exists(folder_name):   # Check if the folder already exists
        os.makedirs(folder_name)   # Create the folder if it doesn't exist
        logger.info(f"Created folder: {folder_name}")
    else:
        logger.info(f"Folder already exists: {folder_name}")


def download_pdfs(link):
    pdf_url = urljoin(baseURL, link)                 # Get the absolute URL of the PDF File
    url_without_query_string = link.split('?')[0]
    filename = os.path.basename(url_without_query_string)
    pdf_name = unquote(unquote(filename))
    pdf_path = os.path.join(folder_name, pdf_name)   # Create the full path to save the PDF file in the website folder
    if not os.path.exists(pdf_path):                 # Check if the PDF file already exists in the website folder
        while True:
            try:
                pdf_response = requests.get(link)         # Make a GET request to the PDF file URL
                break
            except Exception as e:
                logger.error('some Problem while Downloading: trying To Reconnecting')

        with open(pdf_path, 'wb') as f:              # Open a file in binary write mode to save the PDF file
            f.write(pdf_response.content)            # Write the PDF content to the file
        logger.info(f"Downloaded PDF: {pdf_name}")
    else:
        logger.error(f"PDF already exists: {pdf_name}")

#This function processes each each articles and Extract the date,title,link of the press_releases.
def process_webpages(masterUrl):
    try:
        logging.info('Opening the URL in the Chrome Browser')
        driver = get_driver(masterUrl)
        if driver:
            driver.get(masterUrl)
            logging.info('Collecting HTML Source from the Webpage')
            total_article_xpath = '//*[@id="Main_C003_Col00"]/div/div/div[2]/div[2]/div[2]/p'
            btnxpath = '//*[@id="Main_C003_Col00"]/div/div/div[2]/div[2]/div[2]/div/div[2]/div/div[1]/button[2]'
            def GetPageSource():
                html = driver.page_source
                soup = BeautifulSoup(html, 'html.parser')   # Parse the HTML using BeautifulSoup
                if soup != '':
                    links = soup.find_all("a")
                    for link in links:
                        href = link.get("href")
                        if href and href.startswith('https://assets.pcaobus.org/pcaob-dev/docs/default-source/enforcement/decisions/documents/'):
                            pdf_links = href
                            if pdf_links not in PDFs:
                                PDFs.append(pdf_links)
            
            element = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.XPATH, total_article_xpath)))
            getdetails = driver.find_element(By.XPATH, total_article_xpath).text.split(': ')
            TotalArticles = int(getdetails[-1])
            Totalpage = TotalArticles/96
            if Totalpage > int(Totalpage):
                Totalpage = Totalpage+1
            logger.info(Totalpage)
            logger.info(f'Website has Total: {TotalArticles} Articles')
            for i in range(1,int(Totalpage+1)):
                logging.info('Working on Page Number: ',i)
                element = WebDriverWait(driver, 35).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="Main_C003_Col00"]/div/div/div[2]/div[2]/div[3]/div/div[1]/div/div/h3/a')))
                GetPageSource()
                driver.find_element(By.XPATH, btnxpath).click()
    except:
        logger.error("Press releases urls couldn't be fetched from master page url : " + masterUrl)
        traceback.print_exc()

#Execution starts here
if __name__ == '__main__':
    logger.info('Starting script- pcaobus_org.py')
    t1 = time.time()
    try:
        #Calling Func to Fetch Data from the Websites
        process_webpages(masterUrl)
        create_website_folder(masterUrl)
        for pdf in PDFs:
            download_pdfs(pdf)

        logger.info('Script Completed')
        logging.info('Total time took for complete run is {}'.format(time.time() - t1))
    except Exception as e:
        logger.error("Master Page urls couldn't be fetched, PDF conditions does not meet")
        traceback.print_exc()
