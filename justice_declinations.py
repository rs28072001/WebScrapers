import requests, os, logging, traceback, time
from urllib.parse import urlparse
from urllib.parse import urljoin
from urllib.parse import unquote
from bs4 import BeautifulSoup

masterUrl = 'https://www.justice.gov/criminal-fraud/corporate-enforcement-policy/declinations'
baseURL = 'https://www.justice.gov'
PDFs_directory = r''
# Emptying root.handlers before calling basicConfig() method
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

# Logging implement settings
logfile = "C:/Users/AshishMishra/Desktop/doj/doj_decl_160423.log"
logging.basicConfig(filename=logfile, filemode='w', format='%(asctime)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Extract the desired data from the soup object using BeautifulSoup methods
# and return it in a format that is appropriate for your needs
def scrape_website(url):
    logger.info('Working On ',url)
    response = requests.get(url)        # Make a GET request to the website URL
    if response.status_code == 200:     # Check the response status code
        soup = BeautifulSoup(response.text, 'html.parser')   # Parse the HTML using BeautifulSoup
        return soup
    else:
        logger.info(f"Failed to scrape website: {response.status_code}")
        logger.info(f"Response content: {response.content}")
        logger.info(f"Response headers: {response.headers}")
        return None


def create_website_folder(url):
    global folder_name
    domain_name = urlparse(url).netloc   # Get the domain name from the URL using urlparse
    # Replace any periods in the domain name with underscores
    folder = domain_name.replace(".", "_") + '_declinations'
    folder_name = os.path.join(PDFs_directory, folder)   # Create a new path with the original directory and the new directory
    if not os.path.exists(folder_name):   # Check if the folder already exists
        os.makedirs(folder_name)   # Create the folder if it doesn't exist
        logger.info(f"Created folder: {folder_name}")
    else:
        logger.info(f"Folder already exists: {folder_name}")

def extraction():
    create_website_folder(masterUrl)
    soup = scrape_website(masterUrl)   # Parse the HTML using BeautifulSoup
    links = soup.find_all("a")
    # Loop through the links and extract PDF links
    for link in links:
        href = link.get("href")
        if href and href.endswith("download") :
            pdf_links = href
            download_pdfs(pdf_links)

def download_pdfs(link):
    pdf_url = urljoin(baseURL, link)   # Get the absolute URL osf the PDF File
    # Get the filename portion of the URL
    filename = os.path.basename(pdf_url.split('/download')[0])
    # Decode percent-encoded characters in the filename
    pdf_name = unquote(unquote(filename))+'.pdf'
    pdf_path = os.path.join(folder_name, pdf_name)   # Create the full path to save the PDF file in the website folder
    if not os.path.exists(pdf_path):   # Check if the PDF file already exists in the website folder
        pdf_response = requests.get(pdf_url)   # Make a GET request to the PDF file URL
        with open(pdf_path, 'wb') as f:   # Open a file in binary write mode to save the PDF file
            f.write(pdf_response.content)   # Write the PDF content to the file
        logger.info(f"Downloaded PDF: {pdf_name}")
    else:
        logger.info(f"PDF already exists: {pdf_name}")


#Execution starts here
if __name__ == '__main__':
    logger.info('Starting script- justice_gov.py')
    t1 = time.time()
    try:
        #Calling Func to Fetch Data from the Websites
        extraction()

        logger.info('Script Completed')
        logging.info('Total time took for complete run is {}'.format(time.time() - t1))

    except Exception as e:
        logger.error("Master Page urls couldn't be fetched, PDF conditions does not meet")
        traceback.print_exc()
