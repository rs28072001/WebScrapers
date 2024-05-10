import requests,os,logging,traceback,time,datetime
from urllib.parse import urlparse
from urllib.parse import urljoin
from urllib.parse import unquote
from bs4 import BeautifulSoup

masterUrl = 'https://www.sec.gov/litigation/litreleases.htm'
baseURL = 'https://www.sec.gov'
donload_file_direct = '' # Set you PDFs Downloading Direcotory

# Emptying root.handlers before calling basicConfig() method
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

log_path = ""   #Set Your Path for Log File  
log_name = 'Sec_litigationLOG.logs' # Log file name 
logfile = log_path+log_name

# Logging implement settings
logging.basicConfig(filename=logfile, filemode='w', format='%(asctime)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Extract the desired data from the soup object using BeautifulSoup methods
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
            print('\n\nNetwork Error Occur, Reconnceting...\n\n')

def create_website_folder(url, sub_folder):
    global directory_path
    domain_name = urlparse(url).netloc   # Get the domain name from the URL using urlparse
    folder_name = domain_name.replace(".", "_")+' litigation'   # Replace any periods in the domain name with underscores
    directory_path = os.path.join(donload_file_direct, folder_name, sub_folder)   # Create a new path with the original directory and the new directory
    if not os.path.exists(directory_path):   # Check if the directory already exists
        os.makedirs(directory_path)   # Create the directory if it doesn't exist
        print(f"Created directory: {directory_path}")
    else:
        print(f"Directory already exists: {directory_path}")

def mainpage():
    create_website_folder(masterUrl, '2023')
    soup = scrape_website(masterUrl)   # Parse the HTML using BeautifulSoup
    tbody_elements = soup.find_all("table")
    links = (tbody_elements)[-1].find_all("a")
    # Loop through the links and extract PDF links
    for link in links:
        href = link.get("href")
        if href and href.endswith(".htm") and href.startswith('/litigation/litreleases'):
            link = (href)
            urlTxT_Files = baseURL+link
            Write_TxT_Files(urlTxT_Files)
        if href and href.endswith(".txt"):
            link = (href)
            download_txts(link)
        if href and href.endswith(".pdf") and href.startswith(baseURL):
            pdf_links = href.split(baseURL)[1]
            download_pdfs(pdf_links)
        if href and href.endswith(".pdf") and not href.startswith(baseURL):
            pdf_links = href
            download_pdfs(pdf_links)
            
def YeariNation():
    global year
    current_year = datetime.datetime.now().year
    for year in range(1995, current_year):
        create_website_folder(baseURL, str(year))
        print(f'Working On {year} on',baseURL)
        if year > 2019:
            yearURL = f'/litigation/litreleases/litrelarchive/litarchive{year}.htm'
        else:
            yearURL = f'/litigation/litreleases/litrelarchive/litarchive{year}.shtml'

        soup = scrape_website(url = baseURL + yearURL)   # Parse the HTML using BeautifulSoup
        print(year)
        if year < 2016:
            structural = -2
        else:
            structural = -1

        tbody_elements = soup.find_all("table")
        links = (tbody_elements)[structural].find_all("a")
        for link in links:
            href = link.get("href")
            if href and href.endswith(".htm") and href.startswith('/litigation/litreleases'):
                link = (href)
                urlTxT_Files = baseURL+link
                Write_TxT_Files(urlTxT_Files)
            if href and href.endswith(".txt"):
                link = (href)
                download_txts(link)
            if href and href.endswith(".pdf") and href.startswith(baseURL):
                pdf_links = href.split(baseURL)[1]
                download_pdfs(pdf_links)
            if href and href.endswith(".pdf") and not href.startswith(baseURL):
                pdf_links = href
                download_pdfs(pdf_links)

# this function handles crude file path issue on server.
def web_path_error():
    pdf_name='comp23555.pdf'
    pdf_url='https://www.sec.gov/litigation/complaints/2016/comp23555.pdf'
    folder_name = directory_path
    pdf_path = os.path.join(folder_name, pdf_name)   # Create the full path to save the PDF file in the website folder
    if not os.path.exists(pdf_path):                 # Check if the PDF file already exists in the website folder
        pdf_response = requests.get(pdf_url)         # Make a GET request to the PDF file URL
        with open(pdf_path, 'wb') as f:              # Open a file in binary write mode to save the PDF file
            f.write(pdf_response.content)            # Write the PDF content to the file
        logger.info(f"Downloaded PDF: {pdf_name}")
    else:
        logger.info(f"PDF already exists: {pdf_name}")
            

def download_txts(link):
    txt_url = urljoin(baseURL, link)             # Get the absolute URL of the PDF File
    filename = os.path.basename(txt_url)         # Get the filename portion of the URL
    txt_name = unquote(unquote(filename))        # Decode percent-encoded characters in the filename
    folder_name = directory_path
    pdf_path = os.path.join(folder_name, txt_name)# Create the full path to save the PDF file in the website folder
    if not os.path.exists(pdf_path):              # Check if the PDF file already exists in the website folder
        pdf_response = requests.get(txt_url)      # Make a GET request to the PDF file URL
        with open(pdf_path, 'wb') as f:           # Open a file in binary write mode to save the PDF file
            f.write(pdf_response.content)         # Write the PDF content to the file
        print(f"Downloaded Txt file: {txt_name}")
    else:
        print(f"Txt file already exists: {txt_name}")



def download_pdfs(link):
    pdf_url = urljoin(baseURL, link)                 # Get the absolute URL of the PDF File
    filename = os.path.basename(pdf_url)             # Get the filename portion of the URL
    try:
        pdf_name = Mtxtfilename+' '+unquote(unquote(filename))# Decode percent-encoded characters in the filename
    except NameError:
        pdf_name = unquote(unquote(filename))# Decode percent-encoded characters in the filename
    folder_name = directory_path
    pdf_path = os.path.join(folder_name, pdf_name)   # Create the full path to save the PDF file in the website folder
    if not os.path.exists(pdf_path):                 # Check if the PDF file already exists in the website folder
        pdf_response = requests.get(pdf_url)         # Make a GET request to the PDF file URL
        try:
            with open(pdf_path, 'wb') as f:              # Open a file in binary write mode to save the PDF file
                f.write(pdf_response.content)            # Write the PDF content to the file
        except:
            web_path_error()          # Write the PDF content to the file
        print(f"Downloaded PDF: {pdf_name}")
    else:
        print(f"PDF already exists: {pdf_name}")


def Write_TxT_Files(url):
    global Mtxtfilename
    soup =  scrape_website(url)

    if year < 2008:
        font_tags = soup.find_all("font")
    elif year == 2010:
        font_tags = soup.find_all(class_ = 'Content')[-1]  
    elif year < 2018:
        font_tags = soup.find_all("td")[-3]    
    else:
        font_tags = soup.find(class_ = 'grid_10 push_2')

    Mtxtfilename = os.path.splitext(os.path.basename(url))[0]# Get the filename from the URL
    folder_name = directory_path
    txtfilepath = os.path.join(folder_name, Mtxtfilename+'.txt')           # Create the full path to save the TXT file in the website folder
    with open(txtfilepath, "w", encoding="utf-8") as f:         # Find all font tags and write their content to a text file
        for tag in font_tags:
            f.write(tag.text.strip().split('http')[0] + "\n")
    print(f"Webpage into txt file saved: {Mtxtfilename}")


#Execution starts here
if __name__ == '__main__':
    logger.info('Starting script- SEC_litigation_gov.py')
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
