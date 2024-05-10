import io
from PyPDF2 import PdfReader  # Note the import change
import requests, os, logging, traceback, time,datetime
from urllib.parse import urlparse
from urllib.parse import urljoin
from urllib.parse import unquote
from bs4 import BeautifulSoup

masterUrl = 'https://www.onrr.gov/compliance-enforcement/enforcement?tabs=civil-penalties'
baseURL   = 'https://www.onrr.gov'

savedFile_directory = r''

# Emptying root.handlers before calling basicConfig() method
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

logfile = 'onrr_LOG.logs' # Log file name 

# Logging implement settings
logging.basicConfig(filename=logfile, filemode='w', format='%(asctime)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

def create_website_folder(url):
    global folder_name
    domain_name = urlparse(url).netloc                       # Get the domain name from the URL using urlparse
    folder_ = domain_name.replace(".", "_")                  # Replace any periods in the domain name with underscores
    folder_name = os.path.join(savedFile_directory, folder_) # Create a new path with the original directory and the new directory
    if not os.path.exists(folder_name):                      # Check if the folder already exists
        os.makedirs(folder_name)                             # Create the folder if it doesn't exist
        print(f"Created folder: {folder_name}")
    else:
        print(f"Folder already exists: {folder_name}")


def scracepdfpage():
    current_year = datetime.datetime.now().year
    #Loop through the links and extract PDF links
    for year in range(2017, current_year):
        if year == 2017:
            pdf_links = baseURL + f'/document/Penalty.Collections.pdf'
        elif year >= 2018 and year <= 2021:
            pdf_links = baseURL + f'/document/{year}.pdf'
        elif year == 2022:
            pdf_links = baseURL + f'/document/{year}_Penalties.pdf'
        else:
            pdf_links = baseURL + f'/document/{year}_Penalties.pdf'
        download_pdfs(pdf_links)


def download_pdfs(link):
    pdf_url = urljoin(baseURL, link)   # Get the absolute URL of the PDF File
    # Get the filename portion of the URL
    filename = os.path.basename(pdf_url)
    # Decode percent-encoded characters in the filename
    pdf_name = unquote(unquote(filename))
    pdf_path = os.path.join(folder_name, pdf_name)   # Create the full path to save the PDF file in the website folder
    if not os.path.exists(pdf_path):                 # Check if the PDF file already exists in the website folder
        pdf_response = requests.get(pdf_url)         # Make a GET request to the PDF file URL
        # If you want to parse the PDF content, use PdfReader
        pdf_reader = PdfReader(io.BytesIO(pdf_response.content))
        
        # Extract and print the text from the first page (change the page number as needed)
        page = pdf_reader.pages[0]  # Note the change in accessing pages
        pdf_text = page.extract_text()
        print((pdf_url))
        exit()
        # with open(pdf_path, 'wb') as f:              # Open a file in binary write mode to save the PDF file
        #     f.write(pdf_response.content)            # Write the PDF content to the file
        print(f"Downloaded PDF: {pdf_name}")
    else:
        print(f"PDF already exists: {pdf_name}")

def download_ppt():
    FILES = ['/document/OE-STRAC-Presentation-2021.pptx','/document/RMMLF-OE-Presentation-2021.pptx']
    for link in FILES:
        # Get the absolute URL of the PDF File
        pdf_url = urljoin(baseURL, link)   
        # Get the filename portion of the URL
        filename = os.path.basename(pdf_url)
        # Decode percent-encoded characters in the filename
        pdf_name = unquote(unquote(filename))
        pdf_path = os.path.join(folder_name, pdf_name)   # Create the full path to save the PDF file in the website folder
        if not os.path.exists(pdf_path):                 # Check if the PDF file already exists in the website folder
            pdf_response = requests.get(pdf_url)         # Make a GET request to the PDF file URL
            with open(pdf_path, 'wb') as f:              # Open a file in binary write mode to save the PDF file
                f.write(pdf_response.content)            # Write the PDF content to the file
            print(f"Downloaded PPT: {pdf_name}")
        else:
            print(f"PPT already exists: {pdf_name}")


#Execution starts here
if __name__ == '__main__':
    t1 = time.time()
    logger.info(f'Starting script Time:- {t1}')
    try:
        create_website_folder(masterUrl)
        #Calling Func to Fetch Data from the Websites
        scracepdfpage()
        # download_ppt()
        logger.info('Script Completed')
        logging.info('Total time took for complete run is {}'.format(time.time() - t1))
    except Exception as e:
        logger.error("Master Page urls couldn't be fetched, PDF conditions does not meet")
        traceback.print_exc()