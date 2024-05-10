import requests, os, logging, traceback, time,datetime
from urllib.parse import urlparse
from urllib.parse import urljoin
from urllib.parse import unquote
from bs4 import BeautifulSoup

masterUrl = 'https://www.fcc.gov/news-events/headlines/510'
baseURL = 'https://www.fcc.gov'
savedFile_directory = r''

# Emptying root.handlers before calling basicConfig() method
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

# Logging implement settings
logfile = r'fcc_3004.log'
logging.basicConfig(filename=logfile, filemode='w', format='%(asctime)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Extract the desired data from the soup object using BeautifulSoup methods
# and return it in a format that is appropriate for your needs
# and return it in a format that is appropriate for your needs
def scrape_website(url):
    while True:
        try:
            response = requests.get(url)        # Make a GET request to the website URL
            if response.status_code == 200:     # Check the response status code
                soup = BeautifulSoup(response.text, 'html.parser')   # Parse the HTML using BeautifulSoup
                return soup
            else:
                print(f"Failed to scrape website: {response.status_code}")
                print(f"Response content: {response.content}")
                print(f"Response headers: {response.headers}")
                return None
        except Exception as e:
            logger.error('\n\nNetwork Error Occur, Reconnceting...\n\n')


# function to create folder per source name.
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



def webpageprocessing():
    current_year = datetime.datetime.now().year 
    for year in range(2002, current_year + 1):
        create_website_folder(baseURL, str(year))
        YearURL = f'?year_released={year}&items_per_page=All'
        logger.info(f'\n\nWorking On {year}\n\n')
        soup = scrape_website(url = masterUrl + YearURL)   # Parse the HTML using BeautifulSoup
        # find the element with class "view-content"
        view_content = soup.find(class_="view-content")
        # extract all the links inside the "view-content" element
        links = view_content.find_all('a')
        for link in links:
            href = link.get("href")
            if href.startswith('/document'):
                Srape_PDF_Links(href)
        break


def Srape_PDF_Links(Article_Link):
    try:        
        soup = scrape_website(url = baseURL + Article_Link)   # Parse the HTML using BeautifulSoup
        # find the element with class "document-content"
        doc_content = soup.find(class_="documents")
        # extract all the links inside the "documents" element
        links = doc_content.find_all('a')
        #Loop through the links and extract PDF links
        for link in links:
            href = link.get("href")
            if href and href.endswith(".pdf") and href.startswith(baseURL):
                pdf_links = href.split(baseURL)[1]
                download_pdfs(pdf_links)
            if href and href.endswith(".pdf") and not href.startswith(baseURL):
                pdf_links = href
                download_pdfs(pdf_links)
    except AttributeError:
        logger.error(f'No pdf found on this link: {baseURL + Article_Link}')


def download_pdfs(link):
    pdf_url = urljoin(baseURL, link)   # Get the absolute URL of the PDF File
    # Get the filename portion of the URL
    filename = os.path.basename(pdf_url)
    # Decode percent-encoded characters in the filename
    pdf_name = unquote(unquote(filename))
    pdf_path = os.path.join(directory_path, pdf_name)   # Create the full path to save the PDF file in the website folder
    if not os.path.exists(pdf_path):   # Check if the PDF file already exists in the website folder
        pdf_response = requests.get(pdf_url)   # Make a GET request to the PDF file URL
        with open(pdf_path, 'wb') as f:   # Open a file in binary write mode to save the PDF file
            f.write(pdf_response.content)   # Write the PDF content to the file
        logger.info(f"Downloaded PDF: {pdf_name}")
    else:
        logger.info(f"PDF already exists: {pdf_name}")



#Execution starts here
if __name__ == '__main__':
    logger.info('Starting script- FCC_gov.py')
    t1 = time.time()
    try:
        #Calling Func to Fetch Data from the Websites
        webpageprocessing()
        logger.info('Script Completed')
        logging.info('Total time took for complete run is {}'.format(time.time() - t1))

    except Exception as e:
        logger.error("Master Page urls couldn't be fetched, PDF conditions does not meet")
        traceback.print_exc()
