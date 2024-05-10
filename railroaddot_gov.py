import requests, os, logging, traceback, time
from urllib.parse import urlparse
from urllib.parse import urljoin
from urllib.parse import unquote
from bs4 import BeautifulSoup

masterUrl = 'https://railroads.dot.gov/elibrary-search?sort_by=field_effective_date&items_per_page=50&page=0'
baseURL = 'https://railroads.dot.gov'
pageFunc = '/ea/listings/'


# Emptying root.handlers before calling basicConfig() method
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

log_path = ""   #Set Your Path for Log File  
log_name = 'RailRoad_LOG.logs' # Log file name 
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
    # Replace any periods in the domain name with underscores
    folder_name = domain_name.replace(".", "_") 
    if not os.path.exists(folder_name):   # Check if the folder already exists
        os.makedirs(folder_name)   # Create the folder if it doesn't exist
        print(f"Created folder: {folder_name}")
    else:
        print(f"Folder already exists: {folder_name}")

def getpagenumber():
    # Create a BeautifulSoup object to parse the HTML content
    soup = scrape_website(masterUrl)
    # Find all <a> tags within the <li> tags with class "page-item"
    page_links = soup.find_all("li", {"class": "page-item"})
    # Loop through each link and find the link with title "Go to last page"
    for link in page_links:
        if link.find("a") is not None and link.find("a").get("title") == "Go to last page":
            # Extract the href attribute from the anchor tag and get the page number
            pageno = int(link.find("a")["href"].split("=")[-1])
            page_number = pageno + 1
            return page_number
    # If we haven't found a link with title "Go to last page", return None
    return None


def pdf_pagingnation():
    PageNumbers= getpagenumber()
    for perpage in range(PageNumbers):
        pageURL = f'/elibrary-search?sort_by=field_effective_date&items_per_page=50&page={perpage}'
        print(f'\n\n\n Working On {baseURL+pageURL} \n\n\n')
        soup = scrape_website(url = baseURL+pageURL)   # Parse the HTML using BeautifulSoup
        # find the div tag with class name "views-field views-field-nothing"
        div_tag = soup.find('div', {'class': 'views-field views-field-nothing'})
        # find all h2 tags within the div tag
        h2_tags = soup.find_all(class_= 'title elibrary--title')
        # loop through each h2 tag and extract the link within it
        for h2 in h2_tags:
            link = h2.find('a').get('href')
            DocWeb = baseURL+(link)
            Doc_WebPage(DocWeb)

def Doc_WebPage(DocWeb):
    soup = scrape_website(url = DocWeb)   # Parse the HTML using BeautifulSoup
    # find the div tag with class name 'document--set file--attachment field field--name-field-document field--type-file field--label-hidden clearfix field__item'
    div_tag = soup.find('div', {'class': 'document--set file--attachment field field--name-field-document field--type-file field--label-hidden clearfix field__item'})
    # extract the link from the div tag using the 'href' attribute
    link = div_tag.find('a').get('href')
    # Download The PDF
    download_pdfs(link)


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
        print(f"Downloaded PDF: {pdf_name}")
    else:
        print(f"PDF already exists: {pdf_name}")


#Execution starts here
if __name__ == '__main__':
    logger.info('Starting script- RailRoad_gov.py')
    t1 = time.time()
    try:
        #Calling Func to Fetch Data from the 
        create_website_folder(baseURL)

        pdf_pagingnation()

        logger.info('Script Completed')
        logging.info('Total time took for complete run is {}'.format(time.time() - t1))

    except Exception as e:
        logger.error("Master Page urls couldn't be fetched, PDF conditions does not meet")
        traceback.print_exc()
