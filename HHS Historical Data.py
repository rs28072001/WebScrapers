# This script fetches all the press releases urls from DEPT of U.S. Department of Health and Human Services Office of Inspector General website
# and scrape them to store required data to ES to be used as part of violation tracker.
# Dependency: pip install beautifulsoup4,requests,elasticsearch~=7.6.0
# First Install All the Modules

# importing required modules
import os,sys,logging,time,traceback,hmac,hashlib,binascii,requests,datetime
from bs4 import BeautifulSoup
from elasticsearch import Elasticsearch

# Global variables:
new_rows = []#List Variable for Storing Every New data

# Link of our target website
masterUrl = 'https://oig.hhs.gov/fraud/enforcement/?type=cmp-and-affirmative-exclusions'
baseURL = 'https://oig.hhs.gov'
archieve = '/archives/enforcement-actions'


# doc fields required in es
entity_keys = ['message_title', 'message_body', 'doc_source_type', 'document_id', 'doc_source', 'doc_source_url',
               'doc_source_pdf_url', 'time_collected', 'time_uploaded', 'time_master', 'time_document']
key_sig_256 = "f7bc83f430538424b13298e6aa6fb143ef4d59a14946175997479dbc2d1a394e"


# Emptying root.handlers before calling basicConfig() method
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

log_path = ""   #Set Your Path for Log File  
log_name = 'HHS.logs' # Log file name 
logfile = log_path+log_name

# Logging implement settings
logging.basicConfig(filename=logfile, filemode='w', format='%(asctime)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


# Get the value of the 'ENVIRONMENT' environment variable.
# If the environment variable is not set, use 'local' as the default.
environment_name_es = os.environ.get('ENVIRONMENT', 'LOCAL').lower()


print('Initiating Elastic Search in',environment_name_es)

# Connect to the Elasticsearch host based on the environment name.
if environment_name_es == 'local':# Connect to a local Elasticsearch instance running on the default port (9200).
    elasticsearch_url = 'http://127.0.0.1:9200'
    # es = Elasticsearch([{'host': 'localhost', 'port': 9200}])
elif environment_name_es == 'dev':# Connect to the dev Elasticsearch server.
    elasticsearch_url = ''
    user = 'logstash_internal'
    password = ''
    # es = Elasticsearch([{'host': 'dev-elasticsearch-server', 'port': 9200}])
elif environment_name_es == 'prod':# Connect to the prod Elasticsearch server.
    elasticsearch_url = ''
    user = 'logstash_internal'
    password = ''
    # es = Elasticsearch([{'host': 'prod-elasticsearch-server', 'port': 9200}])
else:
    # Print an error message if the environment name is not 'local', 'dev', or 'prod'.
    # print('Invalid environment: {}'.format(environment_name_es))
    sys.exit(1)


if environment_name_es == 'local':
    es = Elasticsearch(elasticsearch_url)#In case of LOCAL HOST Server
    print(es)
else:
    #You have to Provide User name & Password In Case of Other than Local Host
    es = Elasticsearch(elasticsearch_url, http_auth=(user, password))


index_name_es = "hhs_press_articles" # Index Regarding to Your ES Database
index_name_es = index_name_es.lower() # Because ES accepts Only Lower Case index name 
#Creating an index with the name 'index_name_es' in Elasticsearch, In case of You don't have Index for it 
#But don't worry about it if you already have same Index then it automatically skip this without any error
createIndex = es.indices.create(index=index_name_es, ignore=400) # ignore=400 For Skipping the Error of Index Already Exist 

# function to create signature
def create_sha256_signature(key, message):
    byte_key = binascii.unhexlify(key)
    message = message.encode()
    return hmac.new(byte_key, message, hashlib.sha256).hexdigest().upper()


#function to Convert time into UTC TimeStamp
def dateformat(date_str):
    if date_str == 'March 2010':
        date_str = 'March 25 2010'
    if date_str == 'April 2010':
        date_str = 'April 29 2010'
    if date_str == 'December 2010':
        date_str = 'December 1 2010'
    if date_str == '(February 10 2011':
        date_str = 'February 10 2011'
    date = datetime.datetime.strptime(date_str, '%B %d %Y') # Convert date string to datetime object
    # print('Date: ',date_str)
    return(date.strftime('%Y-%m-%dT00:00:00')) #Print the date in the desired format


#This code opens each link from all press release articles and extracts the message body from it
def scrape_website(url):
    while True:
        try:
            # print('Working On ',url)
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
            print('Getting Network Error: Reconnecting...')


def PageSurffing(post_page,PressTitles):
    soup = scrape_website(post_page)   # Parse the HTML using BeautifulSoup
    # Find the article tag with the specified class
    article_tag = soup.find('article', class_='grid-col desktop:grid-col-10 margin-bottom-2 desktop:margin-bottom-5')
    # Extract all the p tags within the article tag
    p_tags = article_tag.find_all('p')
    # Find the li tag within the article tag
    li_tag = article_tag.find('li')
    # Extract the text within the li tag
    li_text = li_tag.get_text()
    PDate = (li_text).split('Date:')[1].split(',')
    pressdate = dateformat(PDate[0]+PDate[1])
    print(pressdate,PressTitles)
    # Loop through the p tags and print their contents
    for p_tag in p_tags:
        messageBody = (p_tag.get_text())
        print(messageBody)
        break
    SendingDataToES(pressdate,PressTitles,post_page,messageBody)

def WebPagination():
    ittr =  totalPage + 1
    for pages in range(2,ittr):
        print(f'\n\nWokring on Page No.{pages}\n\n')
        soup = scrape_website(url = masterUrl+f'&page={pages}')   # Parse the HTML using BeautifulSoup
        ul_element = soup.find('ul', {'class': 'usa-card-group padding-y-0'})
        li_elements = ul_element.find_all('li')
        for li in li_elements:
            anchor_element = li.find('a')  # Find the anchor tag within the li element
            if anchor_element:  # Check if the anchor tag exists
                postlink = anchor_element['href']  # Extract the URL of the anchor tag
                content = anchor_element.text.strip()  # Extract the text content of the anchor tag
                PressTitles = (content)
                postpage = (baseURL) + (postlink)
                PageSurffing(postpage,PressTitles)
                print('\n')

def GetPageNum(soup):
    global totalPage
    # Find the li tag with class 'next-page' within the article tag
    li_tag = soup.find('li', class_='next-page')
    # Extract the previous sibling's text
    prev_text = li_tag.find_previous_sibling().get_text(strip=True)
    totalPage = int(prev_text)

#This function processes each each articles and Extract the date,title,link of the press_releases.
def GetMainPage():
    try:
        soup = scrape_website(masterUrl)   # Parse the HTML using BeautifulSoup
        GetPageNum(soup)
        ul_element = soup.find('ul', {'class': 'usa-card-group padding-y-0'})
        li_elements = ul_element.find_all('li')
        for li in li_elements:
            anchor_element = li.find('a')  # Find the anchor tag within the li element
            if anchor_element:  # Check if the anchor tag exists
                postlink = anchor_element['href']  # Extract the URL of the anchor tag
                content = anchor_element.text.strip()  # Extract the text content of the anchor tag
                PressTitles = (content)
                postpage = (baseURL) + (postlink)
                print(postpage)
                PageSurffing(postpage,PressTitles)

                print('\n\n')
    except:
        logger.error("Press releases urls couldn't be fetched from master page url : " + masterUrl)
        traceback.print_exc()

#This function process each press release to give all required info and store it in ES.
def SendingDataToES(pressdate,PressTitles,post_page,messageBody):
    try:
        violation_doc = {}
        message_title = PressTitles # Press Title
        message_body = messageBody # This fucntion return the msg body 
        doc_source_type = 'Enforcement Actions / CMP and Affirmative Exclusions'
        doc_source = 'U.S. Department of Health and Human Services Office of Inspector General'
        doc_source_url =  masterUrl 
        doc_source_pdf_url = post_page # Our Press Article Link
        time_collected = datetime.datetime.now()
        time_uploaded = datetime.datetime.now()
        time_master = pressdate  # Press Article Date
        time_document = time_master
        message = ''
        for variable in entity_keys: #
            if variable == 'document_id':
                continue
            elif variable == 'time_uploaded':
                continue
            elif variable == 'time_collected':
                continue
            else:
                message = message + eval(variable)

        document_id = create_sha256_signature(key_sig_256, message)

        # converting variables to a dict object for storing as doc in elasticsearch
        for variable in entity_keys:
            violation_doc[variable] = eval(variable)
        #print(violation_doc)
        # storing dict as doc in elasticsearch
        resp = es.index(index=index_name_es, id=document_id, body=violation_doc)#Sending Data into ES
    except:
        logger.error("Press Articles release couldn't be scraped and stored for case: " + PressTitles)
        traceback.print_exc()


#execution starts here
if __name__ == '__main__':

    logger.info('Starting script- hhsScript.py')
    t1 = time.time()

    try:

        # Calling Func for Scrape All Main Page Press 
        GetMainPage()

        # Calling Func for Scrape Data All throught Pagination Press 
        WebPagination()

        logger.info('Script Completed')
        logging.info('Total time took for complete run is {}'.format(time.time() - t1))

    except:

        logger.error("master page urls couldn't be fetched")
        traceback.print_exc()
