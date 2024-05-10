import requests, os, logging, traceback, time, csv
from urllib.parse import urlparse
from urllib.parse import urljoin
from urllib.parse import unquote
from bs4 import BeautifulSoup

baseURL = 'https://www.bsee.gov'
pdfInweb = ['/summary-of-civil-penalties-paid/cy2016-cp-paid',
            '/cp-paid-fy2017',
            '/civil-penalties-program']
savedfile_dir =r''#Set your path where you want to save the files


# Emptying root.handlers before calling basicConfig() method
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

log_path = "log.log"#C:/Users/AshishMishra/Desktop/pdf sources_initial_scripts/bsee.log

# Logging implement settings
logging.basicConfig(filename=log_path, filemode='w', format='%(asctime)s - %(levelname)s - %(message)s',
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


# function to create folder per source name
def create_website_folder():
    global folder_name
    domain_name = urlparse(baseURL).netloc   # Get the domain name from the URL using urlparse
    folder = domain_name.replace(".", "_")   # Replace any periods in the domain name with underscores
    folder_name = os.path.join(savedfile_dir, folder)   # Create a new path with the original directory and the new directory
    if not os.path.exists(folder_name):   # Check if the folder already exists
        os.makedirs(folder_name)   # Create the folder if it doesn't exist
        logger.info(f"Created folder: {folder_name}")
    else:
        logger.info(f"Folder already exists: {folder_name}")

def ProcessMasterPage():
    create_website_folder()
    for ittr in pdfInweb:
        url = baseURL + ittr
        soup = scrape_website(url)   # Parse the HTML using BeautifulSoup
        links = soup.find_all("a") # Loop through the links and extract PDF links
        for link in links:
            href = link.get("href")
            if href and href.endswith(".pdf") and not href.endswith("matrix-522.pdf"):
                pdf_links = href
                download_pdfs(pdf_links)

def datasaved_csv(YearUrl,year):
        soup = scrape_website(YearUrl)
        # Find the table element on the webpage
        table = soup.find('table')
        # Open a new CSV file for writing
        csv_name = f'{year}civil_penalties.csv'
        csv_path = os.path.join(savedfile_dir,folder_name, csv_name)
        with open(csv_path, mode='w', newline='') as csv_file:
            writer = csv.writer(csv_file)
            # Find all the rows in the table
            rows = table.tbody.find_all('tr')
            # Loop through each row in the table
            for row in rows:
                # Find all the cells in the row
                cells = row.find_all('td')
                # Extract the data from each cell
                data = [cell.text.strip() for cell in cells]
                # Write the data to the CSV file
                writer.writerow(data)

def table_extraction():
    create_website_folder()
    for year in range(1997,2012):
        middlelink = '/what-we-do/safety-enforcement-division/civil-penalties/'
        if year == 1997:
            addlink = '4th-quarter-of-1997-civil-penalties'
            YearUrl = baseURL+middlelink+addlink
            datasaved_csv(YearUrl,year)
        elif year == 2009:
            pass
        else:
            YearUrl = baseURL+middlelink+f'{year}-civil-penalties'
            datasaved_csv(YearUrl,year)

def download_pdfs(link):
    pdf_url = urljoin(baseURL, link)   # Get the absolute URL of the PDF File
    filename = os.path.basename(pdf_url)# Get the filename portion of the URL
    pdf_name = unquote(unquote(filename))# Decode percent-encoded characters in the filename
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
    logger.info('Starting script- bsee_gov.py')
    t1 = time.time()
    try:
        #Calling Func to Fetch Data from the Websites
        ProcessMasterPage()
        table_extraction()
        logger.info('Script Completed')
        logging.info('Total time took for complete run is {}'.format(time.time() - t1))

    except Exception as e:
        logger.error("Master Page urls couldn't be fetched, PDF conditions does not meet")
        traceback.print_exc()
