import requests,os,logging,traceback,time
from urllib.parse import urlparse
from urllib.parse import urljoin
from urllib.parse import unquote
from bs4 import BeautifulSoup

BaseUrl = 'https://www.transportation.gov'
masterUrl = 'https://www.transportation.gov/airconsumer/enforcement-orders?field_subject_target_id=13771&items_per_page=All'
PDFs_directory = r'' # Set Your PDFs File Path
# Emptying root.handlers before calling basicConfig() method
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)
 
log_path="trans.log" # Log file Path
# Logging implement settings
logging.basicConfig(filename=log_path, filemode='w', format='%(asctime)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


def scrape_website(masterUrl):
    response = requests.get(masterUrl)        # Make a GET request to the website URL
    if response.status_code == 200:     # Check the response status code
        soup = BeautifulSoup(response.text, 'html.parser')   # Parse the HTML using BeautifulSoup
        # Extract the desired data from the soup object using BeautifulSoup methods
        # and return it in a format that is appropriate for your needs
        return soup
    else:
        logger.info(f"Failed to scrape website: {response.status_code}")
        logger.info(f"Response content: {response.content}")
        logger.info(f"Response headers: {response.headers}")
        return None

def create_website_folder(masterUrl):
    global folder_name
    domain_name = urlparse(masterUrl).netloc   # Get the domain name from the URL using urlparse
    folder = domain_name.replace(".", "_")   # Replace any periods in the domain name with underscores
    folder_name = os.path.join(PDFs_directory, folder)   # Create a new path with the original directory and the new directory
    if not os.path.exists(folder_name):   # Check if the folder already exists
        os.makedirs(folder_name)   # Create the folder if it doesn't exist
        logger.info(f"Created folder: {folder_name}")
    else:
        logger.info(f"Folder already exists: {folder_name}")
    return folder_name

def sequential_pagination():
    try:
        create_website_folder(masterUrl)
        soup = scrape_website(masterUrl)   # Parse the HTML using BeautifulSoup
        maincontent = soup.find(class_='table-responsive')
        tbody = maincontent.find_all('tbody')
        for i in tbody:# Loop through all links on the page
            allpdfclass = (i.find_all(class_="views-field views-field-title"))
            for i in allpdfclass:
                extactlinks= (i.find('a'))
                filelink = (extactlinks.get('href'))
                download_pdfs(filelink)
    except Exception as e:
        logger.error("Pagination Per Page Urls Couldn't be fetched, PDF Connection Failed")
        traceback.print_exc()

def download_pdfs(filelink):
    try:    
        soup = scrape_website(masterUrl=BaseUrl+filelink)   # Parse the HTML of Per PDF Page Using BeautifulSoup
        pdf_link = soup.find('div', {'class': 'document--set file--attachment field field--name-field-document field--type-file field--label-hidden clearfix field__item'}).find('a')['href']
        pdf_url = urljoin(BaseUrl, pdf_link)   # Get the absolute URL of the PDF File
        # Get the filename portion of the URL
        filename = os.path.basename(pdf_url)
        # Decode percent-encoded characters in the filename
        pdf_name = unquote(unquote(filename))
        pdf_path = os.path.join(folder_name, pdf_name)   # Create the full path to save the PDF file in the website folder
        if not os.path.exists(pdf_path):                 # Check if the PDF file already exists in the website folder
            pdf_response = requests.get(pdf_url)         # Make a GET request to the PDF file URL
            with open(pdf_path, 'wb') as f:              # Open a file in binary write mode to save the PDF file
                f.write(pdf_response.content)            # Write the PDF content to the file
            logger.info(f"Downloaded PDF: {pdf_name}")
        else:
            logger.info(f"PDF already exists: {pdf_name}")
    except Exception as e:
        logger.info(e)

#Execution starts here
if __name__ == '__main__':
    logger.info('Starting script- transportation_gov.py')
    t1 = time.time()
    try:
        #Calling Func to Fetch Data from the Websites
        logger.info('Working On ',BaseUrl)
        sequential_pagination()
        logger.info('Script Completed')
        logging.info('Total time took for complete run is {}'.format(time.time() - t1))
    except Exception as e:
        logger.error("Master Page urls couldn't be fetched, PDF conditions does not meet")
        # traceback.print_exc()
