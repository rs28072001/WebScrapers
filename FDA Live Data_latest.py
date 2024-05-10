# This script fetches all the press releases urls from DEPT of US Food & Drug Administration Criminal Division website
# and scrape them to store required data to ES to be used as part of violation tracker.
# Dependency: pip install beautifulsoup4,selenium==4.2.0,webdriver-manager,customtkinter,requests,elasticsearch~=7.6.0

# importing required modules
import os,sys,logging,time,traceback,hmac,hashlib,binascii,requests,pytz
from bs4 import BeautifulSoup
from datetime import datetime
from elasticsearch import Elasticsearch
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
# Global variables:
new_rows = []#List Variable for Storing Every New data

# Link of our target website
base_url = 'https://www.fda.gov/'
master_url = 'https://www.fda.gov/inspections-compliance-enforcement-and-criminal-investigations/criminal-investigations/press-releases'


# doc fields required in es
entity_keys = ['message_title', 'message_body', 'doc_source_type', 'document_id', 'doc_source', 'doc_source_url',
               'doc_source_pdf_url', 'time_collected', 'time_uploaded', 'time_master', 'time_document']
key_sig_256 = "f7bc83f430538424b13298e6aa6fb143ef4d59a14946175997479dbc2d1a394e"


# Emptying root.handlers before calling basicConfig() method
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

log_path = ""   #Set Your Path for Log File  
log_name = 'FDA.logs' # Log file name 
logfile = log_path+log_name

# Logging implement settings
logging.basicConfig(filename=logfile, filemode='a', format='%(asctime)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


# Get the value of the 'ENVIRONMENT' environment variable.

# If the environment variable is not set, use 'local' as the default.
if len(sys.argv) < 2:
    print('environment variable missing, please pass dev or prod along as sys arg')
    sys.exit(1)
else:
    environment_name_es = os.environ.get('ENVIRONMENT', 'Dev').lower()
    environment_name_es = sys.argv[1].lower()


# Connect to the Elasticsearch host based on the environment name.
if environment_name_es == 'local':# Connect to a local Elasticsearch instance running on the default port (9200).
    elasticsearch_url = 'http://127.0.0.1:9200'
    # es = Elasticsearch([{'host': 'localhost', 'port': 9200}])
elif environment_name_es == 'dev':# Connect to the dev Elasticsearch server.
    elasticsearch_url = ''
    user = ''
    password = ''
    # es = Elasticsearch([{'host': 'dev-elasticsearch-server', 'port': 9200}])
elif environment_name_es == 'prod':# Connect to the prod Elasticsearch server.
    elasticsearch_url = ''
    user = 'logstash_internal'
    password = ''
    # es = Elasticsearch([{'host': 'prod-elasticsearch-server', 'port': 9200}])
else:
    # Print an error message if the environment name is not 'local', 'dev', or 'prod'.
    print('Invalid environment: {}'.format(environment_name_es))
    sys.exit(1)


if environment_name_es == 'local':
    es = Elasticsearch(elasticsearch_url)#In case of LOCAL HOST Server
    print(es)
else:
    #You have to Provide User name & Password In Case of Other than Local Host
    es = Elasticsearch(elasticsearch_url, http_auth=(user, password))


index_name_es = "main_casemanager_master" # Index Regarding to Your ES Database
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
def utctimestamp(PressDate_date_str):
    utc_timezone = pytz.utc
    # Convert input date string to datetime object in local timezone
    local_datetime = datetime.strptime(PressDate_date_str, '%m/%d/%Y')
    # Convert local datetime object to UTC timezone
    utc_datetime = utc_timezone.localize(local_datetime)
    # Format UTC datetime object as desired string
    output_str = utc_datetime.strftime('%Y-%m-%dT%H:%M:%S')
    return output_str # Return Timestamp: "03/02/2023 00:00:00"




#This code opens each link from all press release articles and extracts the message body from it
def sendrequest(PressLinks):
    # Send a GET request to the website
    source = requests.get(PressLinks)
    # Raise an exception if the request fails
    source.raise_for_status()
    # Get the HTML content of the website
    html = source.text
    # Create a BeautifulSoup object from the HTML content
    soup = BeautifulSoup(html, "html.parser")
    # Find all the `p` tags in the HTML content
    p_tags = soup.find_all('p')
    # Initialize an empty string for storing the message body
    messagebody = ''
    # Loop through all the `p` tags
    for p_tag in p_tags:
        # Get the string content of the `p` tag
        bodycontent = (p_tag.string)#.text.strip().replace('\n', ' ')
        # Check if the `p` tag has a string content
        if bodycontent != None:
            # Add the string content to the message body
            messagebody = messagebody + bodycontent
    
    return messagebody# Return the concatenated `messagebody`


# Use the count API in Elasticsearch, To get the number of documents in an index
def getESdetails():
    global latest_article
    # Define the search query to retrieve the first saved document
    search_query = {
        "query": {
            "match_all": {}   # Define a query to match all documents
        },
        "sort": [
            {
                "_doc": {      # Sort the documents by _doc in ascending order
                    "order": "asc"
                }
            }
        ],
        "size": 1           # Limit the search results to the first document only
    }

    # Execute the search query
    search_result = es.search(index=index_name_es, body=search_query)

    # Get the first document from the search results
    first_document = search_result['hits']['hits'][0]['_source']
    latest_article = first_document['message_title']
    # Print the first document
    print("\n\n\nLatest Article In the ES:\n\n\n", latest_article)


#This function processes each each articles and Extract the date,title,link of the press_releases.
def process_webpages(master_url):
    try:
        logging.info('Collecting All Information from the Webpage')
        web = webdriver.Chrome(ChromeDriverManager().install())#Initiating Your Chorme 
        web.get(master_url)

        # dropdown = '//*[@id="DataTables_Table_0_length"]/label/select'
        # select = Select(web.find_element(By.XPATH, dropdown))
        # select.select_by_visible_text('All')
        #time.sleep(5)# Time Sleep for In case of Slow internet

        firstlink = '//*[@id="DataTables_Table_0"]/tbody/tr[1]/td[2]/a'
        element = WebDriverWait(web, 10).until(
        EC.presence_of_element_located((By.XPATH, firstlink)))
        html = web.page_source
        soup = BeautifulSoup(html, "html.parser")
        maincontent = soup.find(class_='view-content')
        entry = maincontent.find("span").string
        Totalpress = int(entry.split(' ')[-2])
        logging.info('The Website has :{}'.format(entry))
        tb = maincontent.find("tbody").find_all('tr')
        for t in tb: # Loop for Itrating Every Value 
            data = (t.find_all('td'))
            date = (data[0].string) # Date of Every Press Article
            presstitle = (data[1].string) # Title Of Every Press Article
            presslink = base_url + ((data[1]).find("a").get("href")) # URL of Every Single Press
            if presstitle == latest_article:
                break
            dataFi = [date, presstitle, presslink] # Creating List Pair of Date,Title,Press
            new_rows.append(dataFi)#Append only unique data to the List
        web.close()# Closing the Browser After Scraping Getting Done
    except:
        logger.error("Press releases urls couldn't be fetched from master page url : " + master_url)
        traceback.print_exc()


#This function process each press release to give all required info and store it in ES.
def scrape_press_release_webpage(PressDate_date_str,PressTitles,PressLinks):
    try:
        violation_doc = {}
        message_title = PressTitles # Press Title
        message_body = sendrequest(PressLinks) # This fucntion return the msg body 
        doc_source_type = 'Press Release'
        doc_source = 'US Food & Drug Administration Criminal Division'
        doc_source_url =  master_url 
        doc_source_pdf_url = PressLinks # Our Press Article Link
        time_collected = datetime.now()
        time_uploaded = datetime.now()
        time_master = utctimestamp(PressDate_date_str)  # Press Article Date
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
    logger.info('Starting script- FDAScript.py')
    t1 = time.time()
    try:
        #Calling Func to Fetch Index Count from ES
        getESdetails()

        #function passing it two arguments: master_url and tablist.
        process_webpages(master_url)

        #Calling Func to Fetch all Dates, Press Titles, Press Links
        for data in range(len(new_rows)):# For Loop for Ittrate Every Data Store in List New_Rows
            # Calling Func to process/scrape all Press Releases webpages
            scrape_press_release_webpage(PressDate_date_str= new_rows[data][0],PressTitles=new_rows[data][1],PressLinks=new_rows[data][2])      
        
        
        logger.info('Script Completed')
        logging.info('Total time took for complete run is {}'.format(time.time() - t1))

    except:
        logger.error("master page urls couldn't be fetched")
        traceback.print_exc()
