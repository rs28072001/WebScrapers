import requests, os, logging, traceback, time
from urllib.parse import urlparse
from urllib.parse import urljoin
from urllib.parse import unquote
from bs4 import BeautifulSoup

masterUrl = 'https://www.ams.usda.gov/services/enforcement/psd'
baseURL = 'https://www.ams.usda.gov'

# Emptying root.handlers before calling basicConfig() method
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

log_path = ""   #Set Your Path for Log File  
log_name = 'fincenLog.logs' # Log file name 
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


def create_website_folder(url):
    global folder_name
    domain_name = urlparse(url).netloc   # Get the domain name from the URL using urlparse
    folder_name = domain_name.replace(".", "_")   # Replace any periods in the domain name with underscores
    if not os.path.exists(folder_name):   # Check if the folder already exists
        os.makedirs(folder_name)   # Create the folder if it doesn't exist
        print(f"Created folder: {folder_name}")
    else:
        print(f"Folder already exists: {folder_name}")

def extraction():
    create_website_folder(masterUrl)
    soup = scrape_website(masterUrl)   # Parse the HTML using BeautifulSoup
    links = soup.find_all("a")
    # Loop through the links and extract PDF links
    for link in links:
        href = link.get("href")
        if href and href.endswith(".pdf") :
            pdf_links = href
            print(pdf_links)
            download_pdfs(pdf_links)

def download_pdfs(link):
    pdf_url = urljoin(baseURL, link)   # Get the absolute URL of the PDF File
    # Get the filename portion of the URL
    filename = os.path.basename(pdf_url)
    # Decode percent-encoded characters in the filename
    pdf_name = unquote(unquote(filename))
    pdf_path = os.path.join(folder_name, pdf_name)   # Create the full path to save the PDF file in the website folder
    if not os.path.exists(pdf_path):   # Check if the PDF file already exists in the website folder
        pdf_response = requests.get(pdf_url)   # Make a GET request to the PDF file URL
        with open(pdf_path, 'wb') as f:   # Open a file in binary write mode to save the PDF file
            f.write(pdf_response.content)   # Write the PDF content to the file
        print(f"Downloaded PDF: {pdf_name}")
    else:
        print(f"PDF already exists: {pdf_name}")


#Execution starts here
if __name__ == '__main__':
    logger.info('Starting script- ams_usda_gov.py')
    t1 = time.time()
    try:
        #Calling Func to Fetch Data from the Websites
        extraction()

        logger.info('Script Completed')
        logging.info('Total time took for complete run is {}'.format(time.time() - t1))

    except Exception as e:
        logger.error("Master Page urls couldn't be fetched, PDF conditions does not meet")
        # traceback.print_exc()
