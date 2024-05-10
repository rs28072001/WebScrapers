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


masterUrl = 'https://www.ferc.gov/civil-penalties'
baseURL = 'https://www.ferc.gov'
OrderURL = '/orders-show-cause-proceedings'
Civil_PDFs= []
Order_PDFs= []

# Emptying root.handlers before calling basicConfig() method
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

log_path = ""   #Set Your Path for Log File  
log_name = 'FERC_log.logs' # Log file name 
logfile = log_path+log_name

# Logging implement settings
logging.basicConfig(filename=logfile, filemode='w', format='%(asctime)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Extract the desired data from the soup object using BeautifulSoup methods
# and return it in a format that is appropriate for your needs
def scrape_website(url):
    print('Working On ',url)
    response = requests.get(url)        # Make a GET request to the website URL
    if response.status_code == 200:     # Check the response status code
        soup = BeautifulSoup(response.text, 'html.parser')   # Parse the HTML using BeautifulSoup
        return soup
    else:
        print(f"Failed to scrape website: {response.status_code}")
        print(f"Response content: {response.content}")
        print(f"Response headers: {response.headers}")
        return None

def create_website_folder(url, sub_folder):
    global directory_path
    domain_name = urlparse(url).netloc   # Get the domain name from the URL using urlparse
    folder_name = domain_name.replace(".", "_")   # Replace any periods in the domain name with underscores
    directory_path = os.path.join(os.getcwd(), folder_name, sub_folder)   # Create a new path with the original directory and the new directory
    if not os.path.exists(directory_path):   # Check if the directory already exists
        os.makedirs(directory_path)   # Create the directory if it doesn't exist
        print(f"Created directory: {directory_path}")
    else:
        print(f"Directory already exists: {directory_path}")

def folder_create_with_year(url, sub_folder,year):
    global directory_path
    domain_name = urlparse(url).netloc   # Get the domain name from the URL using urlparse
    folder_name = domain_name.replace(".", "_")   # Replace any periods in the domain name with underscores
    directory_path = os.path.join(os.getcwd(), folder_name, sub_folder,year)   # Create a new path with the original directory and the new directory
    if not os.path.exists(directory_path):   # Check if the directory already exists
        os.makedirs(directory_path)   # Create the directory if it doesn't exist
        print(f"Created directory: {directory_path}")
    else:
        print(f"Directory already exists: {directory_path}")

def OrderProceeding():
    create_website_folder(masterUrl, 'Order Proceedings')
    soup = scrape_website(Orderurl='https://www.ferc.gov/orders-show-cause-proceedings')   # Parse the HTML using BeautifulSoup
    # Find the <div class="col content__body--main"> tag
    col_content = soup.find("div", {"class": "col content__body--main"})

    # Find the <div class="table--responsive"> tag within the <div class="col content__body--main"> tag
    table_responsive = col_content.find("div", {"class": "table--responsive"})

    # Find the <tbody> tag within the <div class="table--responsive"> tag
    tbody = table_responsive.find("tbody")

    # Extract all the links in the <tbody> tag
    links = tbody.find_all("a")
    for link in links:
        print(link.get("href"))
        href = link.get("href")
        if href and href.endswith(".pdf") and href.startswith(baseURL):
            pdf_links = href.split(baseURL)[1]
            print(pdf_links)
        if href and href.endswith(".pdf") and not href.startswith(baseURL):
            pdf_links = href
            print(pdf_links)

def YeariNation_Civil_Penalty():
    current_year = datetime.datetime.now().year
    create_website_folder(baseURL, ('Civil Penalty Actions'))
    for year in range(2007, current_year + 1):
        # print(f'Working On {year} ',baseURL)
        yearURL = f'/all-civil-penalty-actions-{year}'
        soup = scrape_website(url = baseURL + yearURL)   # Parse the HTML using BeautifulSoup
        links = soup.find_all("a")
        # Loop through the links and extract PDF links
        for link in links:
            href = link.get("href")
            if href and href.endswith(".pdf") and href.startswith(baseURL):
                pdf_links = href.split(baseURL)[1]
                print(pdf_links)
            if href and href.endswith(".pdf") and not href.startswith(baseURL):
                pdf_links = href
                print(pdf_links)


def download_pdfs(link):
    pdf_url = urljoin(baseURL, link)   # Get the absolute URL of the PDF File
    print(pdf_url)
    filename = os.path.basename(pdf_url)# Get the filename portion of the URL
    pdf_name = unquote(unquote(filename))# Decode percent-encoded characters in the filename
    folder_name = directory_path
    pdf_path = os.path.join(folder_name, pdf_name)   # Create the full path to save the PDF file in the website folder
    if not os.path.exists(pdf_path):   # Check if the PDF file already exists in the website folder
        pdf_response = requests.get(pdf_url)   # Make a GET request to the PDF file URL
        with open(pdf_path, 'wb') as f:   # Open a file in binary write mode to save the PDF file
            f.write(pdf_response.content)   # Write the PDF content to the file
        print(f"Downloaded PDF: {pdf_name}")
    else:
        print(f"PDF already exists: {pdf_name}")



def OrderPro_web_Process():
    try:
        logging.info('Collecting All Information from the Webpage of Civil Penalty Actions')
        web = webdriver.Chrome(ChromeDriverManager().install())#Initiating Your Chorme 
        create_website_folder(masterUrl, 'Order Proceedings')

        def GetPageSource():
            html = web.page_source
            soup = BeautifulSoup(html, 'html.parser')   # Parse the HTML using BeautifulSoup
            links = soup.find_all("a")
            for link in links:
                href = link.get("href")
                if href and href.endswith(".pdf"):
                    pdf_links = href
                    if pdf_links not in Order_PDFs:
                        Order_PDFs.append(pdf_links)

        web.get(baseURL + OrderURL)
        element = WebDriverWait(web, 10).until(
        EC.presence_of_element_located((By.XPATH, '//*[@id="block-ferc-content"]/section/article/div/div[1]/table/tbody')))
        GetPageSource()

    except:
        logger.error("Press releases urls couldn't be fetched from master page url : " + masterUrl)
        traceback.print_exc()

def process_civil_penalty():
    try:
        logging.info('Collecting All Information from the Webpage of Civil Penalty Actions')
        web = webdriver.Chrome(ChromeDriverManager().install())#Initiating Your Chorme 
        current_year = datetime.datetime.now().year

        def GetPageSource():
            html = web.page_source
            soup = BeautifulSoup(html, 'html.parser')   # Parse the HTML using BeautifulSoup
            links = soup.find_all("a")
            for link in links:
                href = link.get("href")
                if href and href.endswith(".pdf"):
                    pdf_links = href
                    if pdf_links not in Civil_PDFs:
                        Civil_PDFs.append(pdf_links)


        for year in range(2007, current_year + 1):
            folder_create_with_year(baseURL,('Civil Penalty Actions'),str(year))
            print(f'Working On {year} ')
            yearURL = f'/all-civil-penalty-actions-{year}'
            web.get(baseURL + yearURL)
            element = WebDriverWait(web, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="block-ferc-content"]/section/article/div[1]/div/table/tbody/tr[2]/td[1]')))
            GetPageSource()
            web.close()
            for pdf in Civil_PDFs:
                download_pdfs(pdf)
            Civil_PDFs.clear()
        
    except:
        logger.error("Press releases urls couldn't be fetched from master page url : " + masterUrl)
        traceback.print_exc()


#Execution starts here
if __name__ == '__main__':
    logger.info('Starting script- FERC_gov.py')
    t1 = time.time()
    try:
        #Calling Func to Fetch Data from the Websites
        process_civil_penalty()
        OrderPro_web_Process()
        for pdf in Order_PDFs:
            download_pdfs(pdf)

        logger.info('Script Completed')
        logging.info('Total time took for complete run is {}'.format(time.time() - t1))

    except Exception as e:
        logger.error("Master Page urls couldn't be fetched, PDF conditions does not meet")
        traceback.print_exc()
