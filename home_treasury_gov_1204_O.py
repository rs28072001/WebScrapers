# Importing necessary modules
import requests,os,logging,traceback,time,datetime
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup

# Initializing variables
masterUrl = 'https://ofac.treasury.gov/civil-penalties-and-enforcement-information'
baseURL = 'https://ofac.treasury.gov'
savedFile_directory = r''


# Emptying root.handlers before calling basicConfig() method
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

# Logging implement settings
logfile = "C:/Users/AshishMishra/Desktop/OFAC/ofac_130423.log"
logging.basicConfig(filename=logfile, filemode='w', format='%(asctime)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Function to extract desired data from the soup object
def scrape_website(url):
    logger.info('Working On ',url)
    response = requests.get(url)        # Make a GET request to the website URL
    if response.status_code == 200:     # Check the response status code
        soup = BeautifulSoup(response.text, 'html.parser')   # Parse the HTML using BeautifulSoup
        return soup
    else:
        logger.error(f"Failed to scrape website: {response.status_code}")
        logger.error(f"Response content: {response.content}")
        logger.error(f"Response headers: {response.headers}")
        return None

# Function to create a new directory to store downloaded PDFs
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

# Function to download PDFs
def download_pdfs(link):
    pdf_url = urljoin(baseURL, link)   # Get the absolute URL of the PDF File
    pdf_name = link.split('/download?inline')[0].split('/media/')[1] + '.pdf'   # Get the filename portion of the URL
    folder_name = directory_path
    pdf_path = os.path.join(folder_name, pdf_name)   # Create the full path to save the PDF file in the website folder
    if not os.path.exists(pdf_path):   # Check if the PDF file already exists in the website folder
        pdf_response = requests.get(pdf_url)   # Make a GET request to the PDF file URL
        with open(pdf_path, 'wb') as f:   # Open a file in binary write mode to save the PDF file
            f.write(pdf_response.content)   # Write the PDF content to the file
        logger.info(f"Downloaded PDF: {pdf_name}")
    else:
        logger.info(f"PDF already exists: {pdf_name}")

def mainpage():
    current_year = datetime.datetime.now().year #Detect the Current Year    
    create_website_folder(masterUrl, str(current_year)) # Func to Create Directory for particular Year
    soup = scrape_website(masterUrl)   # Parse the HTML using BeautifulSoup
    table = soup.find("table") #Selecting only Table From OFAC 
    links = table.find_all("a")# Scraping all the links from Table Section
    # Loop through the links and extract PDF links
    for link in links:
        href = link.get("href") # Ittrate each link in the particular Year
        #Filter Each link and pass the Download PDFs fucn for download each PDF file
        if href and href.endswith("download?inline") and href.startswith(baseURL):
            pdf_links = href.split(baseURL)[1]
            download_pdfs(pdf_links)
        if href and href.endswith("download?inline") and not href.startswith(baseURL):
            pdf_links = href
            download_pdfs(pdf_links)

def YeariNation():
    current_year = datetime.datetime.now().year #Detect the Current Year   
    for year in range(2003, current_year): # Loop for Ittrate from 2008 to 2022 Pages of OFAC
        create_website_folder(baseURL, str(year)) # Func to Create Directory for particular Year
        yearURL = f'/civil-penalties-and-enforcement-information/{year}-enforcement-information' # Formated Link for Parsing the Year URL
        soup = scrape_website(url = baseURL + yearURL)   # Parse the HTML using BeautifulSoup
        if year >  2008: # Table Add From 2008 and so on in the OFAC
            table = soup.find("table")#Selecting only Table From OFAC 
            links = table.find_all("a")# Scraping all the links from Table Section
        else:
            links = soup.find_all("a")
        # Loop through the links and extract PDF links
        for link in links:
            href = link.get("href")
            if href and href.endswith("download?inline") and href.startswith(baseURL):
                pdf_links = href.split(baseURL)[1]
                download_pdfs(pdf_links)
            if href and href.endswith("download?inline") and not href.startswith(baseURL):
                pdf_links = href
                download_pdfs(pdf_links)

def download_pdfs(link):
    pdf_url = urljoin(baseURL, link)   # Get the absolute URL of the PDF File
    # Get the filename portion of the URL
    pdf_name = link.split('/download?inline')[0].split('/media/')[1] + '.pdf'
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
    logger.info('Starting script- OFAChometreasurygov.py')
    t1 = time.time()
    try:
        #Calling Func to Fetch Data from the Websites
        YeariNation()
        mainpage()
        logger.info('Script Completed')
        logging.info('Total time took for complete run is {}'.format(time.time() - t1))
    except Exception as e:
        logger.error("Master Page urls couldn't be fetched, PDF conditions does not meet")
        traceback.print_exc()
