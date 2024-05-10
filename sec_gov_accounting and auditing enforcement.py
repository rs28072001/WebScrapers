# Creator: D&I, ALQIMI
# This script downloads financial reporting related enforcement actions 
# concerning civil lawsuits brought by the Commission in federal court 
# and notices and orders concerning the institution and/or settlement of 
# administrative proceedings from USA SEC-Accounting and Auditing 
# Enforcement Releases as pdfs, txts and web pages (if pdf/txt aren't availble) 
# into txt file format and saves in Yearwise folders to be used as part of Violation Tracker.
# Dependency: pip install beautifulsoup4,requests,elasticsearch~=7.6.0

# importing libraries
import requests,os,logging,traceback,time,datetime
from urllib.parse import urlparse
from urllib.parse import urljoin
from urllib.parse import unquote
from bs4 import BeautifulSoup
PDFs_directory = r'C:\Users\HOME\Desktop\Script By Ashish\Directory Add\New folder'

# source url
masterUrl = 'https://www.sec.gov/divisions/enforce/friactions.htm'
baseURL = 'https://www.sec.gov'

# SEC's other sub divisions links  
avoidlinks = [  '/litigation/litreleases.htm',
                '/litigation/admin.htm',
                '/litigation/opinions.htm',
                '/litigation/suspensions.htm',
                '/litigation/admin.htm',
                '/litigation/fairfundlist.htm',
                '/litigation/litreleases.htm',
                '/litigation/opinions.htm',
                '/litigation/suspensions.htm']

# Emptying root.handlers before calling basicConfig() method
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

# C:/Users/AshishMishra/Desktop/sec 3 scripts/sec_enforce.log Logging implement settings 
log_path = ""
logging.basicConfig(filename=log_path, filemode='w', format='%(asctime)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# function to download pdf
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
        with open(pdf_path, 'wb') as f:              # Open a file in binary write mode to save the PDF file
            f.write(pdf_response.content)            # Write the PDF content to the file
        logger.info(f"Downloaded PDF: {pdf_name}")
    else:
        logger.info(f"PDF already exists: {pdf_name}")

# function to download txt
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
        logger.info(f"Downloaded Txt file: {txt_name}")
    else:
        logger.info(f"Txt file already exists: {txt_name}")

# function to create folder year-wise
def create_website_folder(url, sub_folder):
    global directory_path
    domain_name = urlparse(url).netloc   # Get the domain name from the URL using urlparse
    folder_name = domain_name.replace(".", "_")+' Enforce'   # Replace any periods in the domain name with underscores
    directory_path = os.path.join(PDFs_directory, folder_name, sub_folder)   # Create a new path with the original directory and the new directory
    if not os.path.exists(directory_path):   # Check if the directory already exists
        os.makedirs(directory_path)   # Create the directory if it doesn't exist
        logger.info(f"Created directory: {directory_path}")
    else:
        logger.info(f"Directory already exists: {directory_path}")

# function to process web pages in txt
def Write_TxT_Files(url):
    global Mtxtfilename
    soup =  enforce_website_scrape(url)
    new_url = url.replace('https://', 'http://', 1)
    if year <= 2008:
        font_tags = soup.find_all("font")
    elif year == 2009:
        font_tags = soup.find_all("tr")[-2]  
    elif year == 2010:
        font_tags = soup.find_all(class_ = 'Content')[-1]
    elif year < 2018:
        font_tags = soup.find_all("tr")[-2]
    else:
        font_tags = soup.find(class_ = 'grid_10 push_2')

    Mtxtfilename = os.path.splitext(os.path.basename(url))[0]# Get the filename from the URL
    folder_name = directory_path
    txtfilepath = os.path.join(folder_name, Mtxtfilename+'.txt')           # Create the full path to save the TXT file in the website folder
    with open(txtfilepath, "w", encoding="utf-8") as f:         # Find all font tags and write their content to a text file
        for tag in font_tags:
            f.write(tag.text.strip().split(new_url)[0] + "\n")
    logger.info(f"Webpage into txt file saved: {Mtxtfilename}")

# Extract the desired data from the soup object using BeautifulSoup methods and return it in a appropriate format
def enforce_website_scrape(url):
    while True:
        try:
            response = requests.get(url)        # Make a GET request to the website URL
            if response.status_code == 200:     # Check the response status code
                soup = BeautifulSoup(response.text, 'html.parser')   # Parse the HTML using BeautifulSoup
                return soup
            else:
                logger.info(f"Failed to scrape website: {response.status_code}")
                logger.info(f"Response content: {response.content}")
                logger.info(f"Response headers: {response.headers}")
                return None
        except Exception as e:
            logger.info('\n\nNetwork Error Occur, Reconnceting...\n\n')

# main function 
def mainpage():
    current_year = datetime.datetime.now().year
    create_website_folder(masterUrl, str(current_year))
    soup = enforce_website_scrape(masterUrl)   # Parse the HTML using BeautifulSoup
    tbody_elements = soup.find_all("table")
    links = (tbody_elements)[-1].find_all("a")
    # Loop through the links and extract PDF links
    for link in links:
        href = link.get("href")
        if href and href.endswith(".htm") and href.startswith('/litigation/enforce/') and href != '/litigation/enforce/enforcearchive/enforcearc2022.htm'  and href !=  '/litigation/enforce/enforcearchive/enforcearc2021.htm'  and href !=  '/litigation/enforce/enforcearchive/enforcearc2020.htm':
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
            
# function for checking years and divisions
def enforce_Check_Every_Year():
    global year
    current_year = datetime.datetime.now().year - 1
    for year in range(1999, current_year + 1):
        create_website_folder(baseURL, str(year))
        logger.info(f'\n\nWorking On {year} on\n\n')
        if year >= 2010:
            yearURL = f'/divisions/enforce/friactions/friactions{year}.htm'
        else:
            yearURL = f'/divisions/enforce/friactions/friactions{year}.shtml'
        soup = enforce_website_scrape(url = baseURL + yearURL)   # Parse the HTML using BeautifulSoup
        links = (soup).find_all("a")
        for link in links:
            href = link.get("href")
            if href and href.endswith(".htm") and href.startswith('/litigation/') and href not in avoidlinks :#and href != '/litigation/admin/adminarchive/adminarc2022.htm'  and href !=  '/litigation/admin/adminarchive/adminarc2021.htm'  and href !=  '/litigation/admin/adminarchive/adminarc2020.htm':
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

#Execution starts here
if __name__ == '__main__':
    logger.info('Starting script- SEC_Enforce_gov.py')
    t1 = time.time()
    try:
        #Calling Function to Fetch Data from the Websites
        enforce_Check_Every_Year()
        mainpage()
        logger.info('Script Completed')
        logging.info('Total time took for complete run is {}'.format(time.time() - t1))
    except Exception as e:
        logger.error("Master Page urls couldn't be fetched, PDF conditions does not meet")
        traceback.print_exc()
