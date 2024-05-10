import requests, os, logging, traceback, time
from urllib.parse import urlparse
from urllib.parse import urljoin
from urllib.parse import unquote
from bs4 import BeautifulSoup

masterUrl = 'https://www.cms.gov/Medicare/Compliance-and-Audits/Part-C-and-Part-D-Compliance-and-Audits/PartCandPartDEnforcementActions-'
baseURL = 'https://www.cms.gov'
savedFile_directory = r'C:\Users\HOME\Downloads\add\123\New folder'

# Emptying root.handlers before calling basicConfig() method
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

log_path = ""   #Set Your Path for Log File  
log_name = 'cms_LOG_Part_D_C.logs' # Log file name 
logfile = log_path+log_name

# Logging implement settings
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
        print(f"Failed to scrape website: {response.status_code}")
        print(f"Response content: {response.content}")
        print(f"Response headers: {response.headers}")
        return None
    
def create_website_folder(url):
    global folder_name
    domain_name = urlparse(url).netloc   # Get the domain name from the URL using urlparse
    folder_ = domain_name.replace(".", "_") + 'Part_C_D'   # Replace any periods in the domain name with underscores
    folder_name = os.path.join(savedFile_directory, folder_)   # Create a new path with the original directory and the new directory
    if not os.path.exists(folder_name):   # Check if the folder already exists
        os.makedirs(folder_name)   # Create the folder if it doesn't exist
        print(f"Created folder: {folder_name}")
    else:
        print(f"Folder already exists: {folder_name}")

def anotherdownloads():
    soup = scrape_website(masterUrl) # Parse the HTML using BeautifulSoup
    links = soup.find_all("li", class_ = 'field__item')
    #Loop through the links and extract PDF links
    for link in links:
        href = link.find('a').get("href")
        if href and href.endswith(".pdf") and href.startswith(baseURL):
            pdf_links = href.split(baseURL)[1]
            download_pdfs(pdf_links)
        if href and href.endswith(".pdf") and not href.startswith(baseURL):
            pdf_links = href
            download_pdfs(pdf_links)

def getpagenumbers():
    global pageno
    soup = scrape_website(masterUrl)   # Parse the HTML using BeautifulSoup
    # Find the div element containing the desired class
    div = soup.find("div", class_="ds-l-row ds-u-margin-bottom--3")
    # Find the span element within the div
    span = div.find("span")
    # Extract the string from the span element, if it exists
    if span is not None:
        string = span.get_text(strip=True).split(' entries')[0].split('of ')[-1]
        getpage = int(string)/100
        if int(getpage) < float(getpage):
            pageno = int(getpage + 1)
            # print(pageno)
        if int(getpage) == float(getpage):
            pageno = int(getpage)
            # print(pageno)
    else:
        print("Website Elements not found.")

def extracting_pdfwebpage():
    for ittrate in range(pageno):
        paging = f'?combine=&items_per_page=100&page={ittrate}'
        # Create a BeautifulSoup object to parse the HTML content
        soup = scrape_website(masterUrl+paging)   # Parse the HTML using BeautifulSoup
        # Find the div element containing the view content
        div = soup.find("div", class_="view-content")
        # Find all the tbody elements within the div
        tbody_list = div.find_all("tbody")
        # Loop through all the tbody elements
        for tbody in tbody_list:
            # Find all the a elements within the tbody
            link_list = tbody.find_all("a")
            # Loop through all the a elements and print their href attribute
            for link in link_list:
                href = link.get("href")
                pdf_page = (baseURL + href)
                scracepdfpage(pdf_page)            

def scracepdfpage(pdf_page):
    soup = scrape_website(pdf_page) # Parse the HTML using BeautifulSoup
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
        print(f"Downloaded PDF: {pdf_name}")
    else:
        print(f"PDF already exists: {pdf_name}")

#Execution starts here
if __name__ == '__main__':
    logger.info('Starting script- CMS_gov_D_C.py')
    t1 = time.time()
    try:
        print('Working On ',masterUrl)
        getpagenumbers()
        create_website_folder(masterUrl)
        anotherdownloads()
        #Calling Func to Fetch Data from the Websites
        extracting_pdfwebpage()

        logger.info('Script Completed')
        logging.info('Total time took for complete run is {}'.format(time.time() - t1))

    except Exception as e:
        logger.error("Master Page urls couldn't be fetched, PDF conditions does not meet")
        traceback.print_exc()
