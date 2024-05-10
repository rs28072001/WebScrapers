import requests, os, logging, traceback, time
from urllib.parse import urlparse
from urllib.parse import urljoin
from urllib.parse import unquote
from bs4 import BeautifulSoup

masterUrl = 'https://www.faa.gov/about/office_org/headquarters_offices/agc/practice_areas/enforcement/reports'
baseURL = 'https://www.faa.gov'
savedFile_directory = r'C:\Users\HOME\Downloads\add\123\New folder'

# Emptying root.handlers before calling basicConfig() method
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

# Logging implement settings
logfile = "C:/Users/AshishMishra/Desktop/faa/faa_160423.log"
logging.basicConfig(filename=logfile, filemode='w', format='%(asctime)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Extract the desired data from the soup object using BeautifulSoup methods
# and return it in a format that is appropriate for your needs
def scrape_website(url):
    response = requests.get(url)        # Make a GET request to the website URL
    if response.status_code == 200:     # Check the response status code
        soup = BeautifulSoup(response.text, 'html.parser')   # Parse the HTML using BeautifulSoup
        return soup
    else:
        logger.error(f"Failed to scrape website: {response.status_code}")
        logger.error(f"Response content: {response.content}")
        logger.error(f"Response headers: {response.headers}")
        return None
    
def create_website_folder(url):
    global folder_name
    domain_name = urlparse(url).netloc              # Get the domain name from the URL using urlparse
    folder_ = domain_name.replace(".", "_")     # Replace any periods in the domain name with underscores
    folder_name = os.path.join(savedFile_directory, folder_)   # Create a new path with the original directory and the new directory
    if not os.path.exists(folder_name):             # Check if the folder already exists
        os.makedirs(folder_name)                    # Create the folder if it doesn't exist
        logger.info(f"Created folder: {folder_name}")
    else:
        logger.info(f"Folder already exists: {folder_name}")

def extracting_pdfwebpage():
    logger.info(f'\n\n\n\nWorking On {masterUrl}\n\n\n\n')
    # Create a BeautifulSoup object to parse the HTML content
    soup = scrape_website(masterUrl)   # Parse the HTML using BeautifulSoup
    # Find the div element containing the view content
    links = soup.find_all("a")
    # Loop through the links and extract PDF links
    for link in links:
        href = link.get("href")
        if href and href.endswith(".pdf") and href.startswith(baseURL):
            pdf_links = href.split(baseURL)[1]
            download_pdfs(pdf_links)
        if href and href.endswith(".pdf") and not href.startswith(baseURL):
            pdf_links = href
            download_pdfs(pdf_links)
    Srape_another_years()         

def Srape_another_years():
    logger.info(f'\n\n\n\nWorking On {masterUrl}/archives\n\n\n\n')
    soup = scrape_website(url = masterUrl+'/archives')   # Parse the HTML using BeautifulSoup
    links = soup.find_all("a")
    #Loop through the links and extract PDF links
    for link in links:
        href = link.get("href")
        if href and href.endswith(".pdf") and href.startswith(baseURL):
            pdf_links = href.split(baseURL)[1]
            download_pdfs(pdf_links)
        if href and href.endswith(".pdf") and not href.startswith(baseURL):
            pdf_links = href
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
        logger.info(f"Downloaded PDF: {pdf_name}")
    else:
        logger.info(f"PDF already exists: {pdf_name}")



#Execution starts here
if __name__ == '__main__':
    logger.info('Starting script- FAA_gov.py')
    t1 = time.time()
    try:
        create_website_folder(masterUrl)
        #Calling Func to Fetch Data from the Websites
        extracting_pdfwebpage()
        logger.info('Script Completed')
        logging.info('Total time took for complete run is {}'.format(time.time() - t1))

    except Exception as e:
        logger.error("Master Page urls couldn't be fetched, PDF conditions does not meet")
        traceback.print_exc()
