import requests, os, logging, traceback, time
from urllib.parse import urlparse
from urllib.parse import urljoin
from urllib.parse import unquote
from bs4 import BeautifulSoup

masterUrl = 'https://www.energy.gov/ea/enforcement-infocenter'
baseURL = 'https://www.energy.gov'
pageFunc = '/ea/listings/'
savedFile_directory = r'C:\Users\HOME\Downloads\add\123\New folder'

maincontent = ['worker-safety-health-documents',
            'nuclear-safety-enforcement-documents',
            'security-enforcement-documents']

ENFORCEMENT_DOC = ['enforcement-letters',
                'notices-violation',
                'notice-investigation-letters-0',
                'compliance-and-special-report-orders',
                'consent-orders-and-settlement-agreements']

# Emptying root.handlers before calling basicConfig() method
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

# Logging implement settings
logfile = ""#C:/Users/AshishMishra/Desktop/energy/doe_enf.log
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
    
def create_website_folder(url, sub_folder):
    global directory_path
    domain_name = urlparse(url).netloc   # Get the domain name from the URL using urlparse
    folder_name = domain_name.replace(".", "_")   # Replace any periods in the domain name with underscores
    directory_path = os.path.join(savedFile_directory, folder_name, sub_folder)   # Create a new path with the original directory and the new directory
    if not os.path.exists(directory_path):   # Check if the directory already exists
        os.makedirs(directory_path)   # Create the directory if it doesn't exist
        logger.info(f"Created directory: {directory_path}")
    else:
        logger.info(f"Directory already exists: {directory_path}")

def getpagenumber(url):
    logger.info(url)
    soup = scrape_website(url)   # Parse the HTML using BeautifulSoup baseURL + pageFunc
    # Find the li tag with the class pagination-item pagination-last
    li_element = soup.find("li", {"class": "pagination-item pagination-last"})
    # Extract the link from the li tag
    link = li_element.find("a")["href"].split('=')[1]
    pageno= int(link) + 1
    return (pageno)


def extract_maincontent():
    for elements in maincontent:
        logger.info(f'\n\n\n Working On {baseURL+pageFunc+elements} \n\n\n')
        create_website_folder(masterUrl, elements)
        pagination = getpagenumber(url=baseURL+pageFunc+elements)
        for paging in range(pagination):
            soup = scrape_website(url = baseURL+ pageFunc + elements + f"?page={paging}")   # Parse the HTML using BeautifulSoup
            contents = soup.find(class_="search-results")
            links = contents.find_all('a')
            # Loop through the links and extract PDF links
            for link in links:
                href = link.get("href")
                pdf_surffing(href)


def extract_ENFORCEMENT_DOC(): 
    for elements in maincontent:
        logger.info(f'\n\n\n Working On {baseURL+pageFunc+elements} \n\n\n')
        create_website_folder(masterUrl, elements)
        pagination = getpagenumber(url=baseURL+pageFunc+elements)
        for paging in range(pagination):
            soup = scrape_website(url = baseURL+ pageFunc + elements + f"?page={paging}")   # Parse the HTML using BeautifulSoup
            contents = soup.find(class_="search-results")
            links = contents.find_all('a')
            # Loop through the links and extract PDF links
            for link in links:
                href = link.get("href")
                pdf_surffing(href)


def pdf_surffing(href):
    soup = scrape_website(url = baseURL+href)   # Parse the HTML using BeautifulSoup
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


def download_pdfs(link):
    pdf_url = urljoin(baseURL, link)   # Get the absolute URL of the PDF File
    # Get the filename portion of the URL
    filename = os.path.basename(pdf_url)
    # Decode percent-encoded characters in the filename
    pdf_name = unquote(unquote(filename))
    folder_name = directory_path
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
    logger.info('Starting script- energy_gov.py')
    t1 = time.time()
    try:
        #Calling Func to Fetch Data from the Websites
        extract_maincontent()
        extract_ENFORCEMENT_DOC

        logger.info('Script Completed')
        logging.info('Total time took for complete run is {}'.format(time.time() - t1))

    except Exception as e:
        logger.error("Master Page urls couldn't be fetched, PDF conditions does not meet")
        traceback.print_exc()
