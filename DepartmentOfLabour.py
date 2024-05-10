# This script fetches all the press releases urls from U.S. DEPARTMENT OF LABOR website
# and scrape them to store required data to ES to be used as part of violation tracker.
# Dependency: pip install beautifulsoup4,requests,elasticsearch~=7.6.0

# importing required modules
import os,sys,logging,time,traceback,hmac,hashlib,binascii,requests
from bs4 import BeautifulSoup
from datetime import datetime
from elasticsearch import Elasticsearch


# Link of our target website
masterUrl = 'https://www.dol.gov/newsroom/releases?agency=48&state=All&topic=All&year=all'
baseURL = 'https://www.dol.gov'

Live_Data = []#List Variable for Storing Every New data

# doc fields required in es
entity_keys = ['message_title', 'message_body', 'doc_source_type', 'document_id', 'doc_source', 'doc_source_url',
               'doc_source_pdf_url', 'time_collected', 'time_uploaded', 'time_master', 'time_document']
key_sig_256 = "f7bc83f430538424b13298e6aa6fb143ef4d59a14946175997479dbc2d1a394e"

# Emptying root.handlers before calling basicConfig() method
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

# Logging implement settings
log_path = r"Dol.log"
logging.basicConfig(filename=log_path, filemode='w', format='%(asctime)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# environment function description
def set_environment():
    global es,index_name_es
    # Get the value of the 'ENVIRONMENT' environment variable.
    # If the environment variable is not set, use 'local' as the default.
    environment_name_es = os.environ.get('ENVIRONMENT', 'LOCAL').lower()

    # Connect to the Elasticsearch host based on the environment name.
    if environment_name_es == 'local':# Connect to a local Elasticsearch instance running on the default port (9200).
        elasticsearch_url = 'http://127.0.0.1:9200'
    elif environment_name_es == 'dev':# Connect to the dev Elasticsearch server.
        elasticsearch_url = ''
        user = 'logstash_internal'
        password = ''
    elif environment_name_es == 'prod':# Connect to the prod Elasticsearch server.
        elasticsearch_url = ''
        user = ''
        password = ''
    else:
        # logging errors if any via logger error()
        logger.error('Invalid environment: {}'.format(environment_name_es))

    if environment_name_es == 'local':
        es = Elasticsearch(elasticsearch_url)#In case of LOCAL HOST Server
    else:
        es = Elasticsearch(elasticsearch_url, http_auth=(user, password))

    index_name_es = "dol" # Index Regarding to Your ES Database
    index_name_es = index_name_es.lower() # Because ES accepts Only Lower Case index name 

    # Creating an index with the name 'index_name_es' in Elasticsearch, In case Index isn't there  
    # if Index is there, it automatically skips this without any error
    createIndex = es.indices.create(index=index_name_es, ignore=400) # ignore=400 For Skipping the Error of Index Already Exist 

# function to create signature
def create_sha256_signature(key, message):
    byte_key = binascii.unhexlify(key)
    message = message.encode()
    return hmac.new(byte_key, message, hashlib.sha256).hexdigest().upper()

#function to Convert time into UTC TimeStamp
def convert_date(date_string):
    # Convert date string to datetime object
    date_obj = datetime.strptime(date_string, '%B %d, %Y')
    # Convert datetime object to desired string format
    return date_obj.strftime('%Y-%m-%dT00:00:00')

#This code opens each link from all press release articles and extracts the message body from it
def scrape_website(url):
    while True:
        try:
            response = requests.get(url)        # Make a GET request to the website URL
            if response.status_code == 200:     # Check the response status code
                soup = BeautifulSoup(response.text, 'html.parser')   # Parse the HTML using BeautifulSoup
                return soup
            else:
                logger.error(f"Failed to scrape website: {response.status_code}")
                logger.error(f"Response content: {response.content}")
                logger.error(f"Response headers: {response.headers}")
                return None
        except Exception as e:
            logger.info('Getting Network Error: Reconnecting...')

def GetMainPage(articlelink,articleDate,articleTitle):
    try:
        ReleaseLink=baseURL+articlelink
        soup = scrape_website(ReleaseLink)   # Parse the HTML using BeautifulSoup
        dol_press_page = soup.find('div', {'class': 'dol-press-page'})
        if dol_press_page:
            text = dol_press_page.text
            messageBody = (text.split('Share This')[0])
            SendingDataToES(articleDate,articleTitle,ReleaseLink,messageBody)
        else:
            print('Could not find the dol-press-page class on the page')
           
    except:
        logger.error("Could not find the MessageBody")
        traceback.print_exc()

#This function processes each articles and Extract the date,title,link of the press_releases.
def WebpagePro():
    try:
        current_year = datetime.now().year 
        for year in range(2009, current_year + 1):
            YearURL = f'/newsroom/releases?agency=48&state=All&topic=All&year={year}'
            logger.info(f'\n\nWorking On {year}\n\n')
            soup = scrape_website(url = baseURL + YearURL)   # Parse the HTML using BeautifulSoup
            # find all the elements with class "image-left-teaser"
            view_content = soup.find_all(class_="image-left-teaser")
            # iterate over the "image-left-teaser" elements and extract all the links
            for content in view_content:
                links = content.find('a')
                date_texts = content.find(class_="dol-date-text")
                h3_tags = content.find('h3')
                href = links.get("href")
                if href.startswith('    /newsroom/releases'):
                    articlelink = str(href).split()[0]
                    articleDate = date_texts.text.strip()
                    articleTitle = h3_tags.text.strip()
                    GetMainPage(articlelink,articleDate,articleTitle)
    except:
        logger.error("Press releases urls couldn't be fetched from master page url : " + masterUrl)
        traceback.print_exc()



#This function process each press release to give all required info and store it in ES.
def SendingDataToES(articleDate,articleTitle,ReleaseLink,messageBody):
    try:
        violation_doc = {}
        message_title = articleTitle # Press Title
        message_body = messageBody # This fucntion return the msg body 
        doc_source_type = 'Office of Federal Contract Complinance Programs'
        doc_source = 'U.S. DEPARTMENT OF LABOR'
        doc_source_url =  masterUrl 
        doc_source_pdf_url = ReleaseLink # Our Press Article Link
        time_collected = datetime.now()
        time_uploaded = datetime.now()
        time_master = convert_date(articleDate) # Press Article Date
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
        # storing dict as doc in elasticsearch
        resp = es.index(index=index_name_es, id=document_id, body=violation_doc)#Sending Data into ES
    except Exception as e:
        logger.error("Sending Data To ES: " + e)
        traceback.print_exc()

#execution starts here
if __name__ == '__main__':

    logger.info('Starting script- DOL.py')
    t1 = time.time()
    try:
        #Calling environment Function to Set The environment
        set_environment()
        # Calling Function to Scrape All Main Page Press 
        WebpagePro()
        
        es.transport.close()# closing the es connection
        logger.info('Script Completed')
        logging.info('Total time took for complete run is {}'.format(time.time() - t1))
        
    except:

        logger.error("master page urls couldn't be fetched")
        traceback.print_exc()
