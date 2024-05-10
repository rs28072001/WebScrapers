# Creator: D&I, ALQIMI
# This script downloads the Consent Agreement, Charging letter and Order documents(pdfs) 
# in order to be used as part of Violation Tracker. The Department of State’s Directorate 
# of Defense Trade Controls (DDTC) is charged with controlling the export and temporary
# import of defense articles and defense services, in accordance with the AECA-
# Arms Export Control Act and the ITAR- International Traffic in Arms Regulations.  
# Dependency: pip install beautifulsoup4,selenium,requests,elasticsearch~=7.6.0

# importing libraries
import requests,os,logging,traceback,time,datetime
from urllib.parse import urlparse
from urllib.parse import urljoin
from urllib.parse import unquote
from bs4 import BeautifulSoup
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# source url
masterUrl = 'https://www.pmddtc.state.gov/ddtc_public?id=ddtc_kb_article_page&sys_id=384b968adb3cd30044f9ff621f961941'
baseURL = 'https://www.pmddtc.state.gov'
PDFs_directory = r'' # Set your PDFs file saving directory

PDFs = []

# Emptying root.handlers before calling basicConfig() method
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

# Logging implement settings  
log_path = "pmddtc.log" # Set your log file path
logging.basicConfig(filename=log_path, filemode='w', format='%(asctime)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# function to create folder per source name
def create_website_folder():
    global folder_name
    domain_name = urlparse(baseURL).netloc   # Get the domain name from the URL using urlparse
    folder = domain_name.replace(".", "_")   # Replace any periods in the domain name with underscores
    folder_name = os.path.join(PDFs_directory, folder)   # Create a new path with the original directory and the new directory
    if not os.path.exists(folder_name):   # Check if the folder already exists
        os.makedirs(folder_name)   # Create the folder if it doesn't exist
        logger.info(f"Created folder: {folder_name}")
    else:
        logger.info(f"Folder already exists: {folder_name}")

# function to download pdfs
def download_pdfs(link):
    pdf_url = urljoin(baseURL, link)                 # Get the absolute URL of the PDF File
    pdf_name = f"{link.split('id=')[-1]}.pdf"
    pdf_path = os.path.join(folder_name, pdf_name)   # Create the full path to save the PDF file in the website folder
    if not os.path.exists(pdf_path):                 # Check if the PDF file already exists in the website folder
        while True:
            try:
                pdf_response = requests.get(pdf_url)         # Make a GET request to the PDF file URL
                break
            except Exception as e:
                logger.info('some issue while Downloading: Trying To Reconnecting')
                time.sleep(1)
        with open(pdf_path, 'wb') as f:              # Open a file in binary write mode to save the PDF file
            f.write(pdf_response.content)            # Write the PDF content to the file
        logger.info(f"Downloaded PDF: {pdf_name}")
    else:
        logger.info(f"PDF already exists: {pdf_name}")

#This function processes each each articles and Extract the date,title,link of the press_releases.
def process_webpages(masterUrl):
    try:
        logging.info('Collecting All Information from the Webpage')
        web = webdriver.Chrome(ChromeDriverManager().install())#Initiating Your Chorme 
        web.get(masterUrl)
        time.sleep(4)
        total_article_xpath = '//*[@id="maincontent"]/div/div/div/div/div[2]/div/div[2]/div/div[2]/div[2]'
        btnxpath = '//*[@id="maincontent"]/div/div/div/div/div[2]/div/div[2]/div/div[2]/div[1]/div[3]'
        def GetPageSource():
            html = web.page_source
            soup = BeautifulSoup(html, 'html.parser')   # Parse the HTML using BeautifulSoup
            links = soup.find_all("a")
            for link in links:
                href = link.get("href")
                if href and href.startswith('/sys'):
                    pdf_links = href
                    PDFs.append(pdf_links)
        while True:
            getdetails = web.find_element(By.XPATH, total_article_xpath).text.split(' of ')
            totalpages = int(getdetails[-1])
            currentitr = int(getdetails[0].split(' - ')[-1])
            logger.info(f'Articles Details Fetched {currentitr}: Total Articles:{totalpages}')
            GetPageSource()
            pagination_button = web.find_element(By.XPATH, btnxpath).click()
            time.sleep(5)
            if totalpages-currentitr==0:
                break
        logger.info('Webpage Source Completely Fetched')
        web.close()
    except:
        logger.error("Press releases urls couldn't be fetched from master page url : " + masterUrl)
        traceback.print_exc()

#Execution starts here
if __name__ == '__main__':
    logger.info('Starting script- PMDDTC__gov.py')
    t1 = time.time()
    try:
        #Calling Func to Fetch Data from the Websites
        process_webpages(masterUrl)
        create_website_folder()
        for pdf in PDFs:
            download_pdfs(pdf)

        logger.info('Script Completed')
        logging.info('Total time took for complete run is {}'.format(time.time() - t1))
    except Exception as e:
        logger.error("Master Page urls couldn't be fetched, PDF conditions does not meet")
        traceback.print_exc()
