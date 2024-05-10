import logging,requests,datetime,time,hmac,hashlib,binascii,uuid
import traceback
from bs4 import BeautifulSoup
from elasticsearch import Elasticsearch
from sys import platform



#Input section for User
Notice_Type   = input("Enter Type of Your Notice 'Yellow' or 'Red' :- ")     # Here you can switch the site  
index_name_es = f"{Notice_Type}ata12"
log_path      = f"{index_name_es}.log"
envirotment   = 'local'
key_sig_256   = "f7bc83f430538424b13298e6aa6fb143ef4d59a14946175997479dbc2d1a394e"

#Hardcoded Values 
base_request_url    =   "https://ws-public.interpol.int"
Doc_source_url      =  f"https://www.interpol.int/en/How-we-work/Notices/{Notice_Type.capitalize()}-Notices/View-{Notice_Type.capitalize()}-Notices"
Doc_source          =   "INTERPOL"
Doc_source_type     =  f"{Notice_Type.capitalize()} Notice"
Entity_type         =   "individual"
Relationship_type   =   "enforcement"
nationalities       =   [] # Empty array for collecting all the country CODE
gender_list         =   ['F','M']

# Emptying root.handlers before calling basicConfig() method
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)
logging.basicConfig(filename=log_path, filemode='w', format='%(asctime)s - %(levelname)s - %(message)s',
                    level=logging.ERROR)
logger = logging.getLogger(__name__)

def get_es_connection(env):
    if env == 'dev':
        password = ''
        if platform == 'linux' or platform == "linux2":
            host_name = 'elasticsearch:9200'
        elif platform == 'win32':
            host_name = 'dev.es.aosen.ai:9200'
        # Instantiate ES Client
        client = Elasticsearch(['https://' + host_name],
                            http_auth=('logstash_internal', password),verify_certs=False,use_ssl=True, timeout=30, max_retries=10, retry_on_timeout=True)
    elif env == 'prod':
        password = ''
        if platform == 'linux' or platform == "linux2":
            host_name = 'elasticsearch:9200'
        elif platform == 'win32':
            host_name = 'aosen.ai:443/logstash'
        # Instantiate ES Client
        client = Elasticsearch(['https://' + host_name],
                            http_auth=('logstash_internal', password),verify_certs=False,use_ssl=True, timeout=30, max_retries=10, retry_on_timeout=True)
    else:
        client = Elasticsearch(['http://127.0.0.1:9200'])#In case of LOCAL HOST Server


    return client
#Get ES Index Details

#Function to get the Country Code from the HTML
def get_nat_array():
    # Send an HTTP GET request to the website
    response = requests.get(Doc_source_url)
    # Parse the HTML content of the page using BeautifulSoup
    soup = BeautifulSoup(response.content, 'html.parser')
    # Find the select tag with the ID "nationality"
    select_tag = soup.find('select', id='nationality')
    # Find all the option tags within the select tag
    options = select_tag.find_all('option')
    # Extract and print the values of the options tag of HTML
    for option in options:
        try:
            nationalities.append(option['value'])
        except KeyError as e:
            pass


# function to create signature
def create_sha256_signature(message):
    byte_key = binascii.unhexlify(key_sig_256)
    message = message.encode()
    return hmac.new(byte_key, message, hashlib.sha256).hexdigest().upper()

def get_webdata(BaseRequest):
    try:
        # Send a GET request to the person_request URL and get the response
        response = requests.get(BaseRequest)
        # Raise an exception if the response status code indicates an error
        status_code = response.status_code
        if status_code == 200:
            # Parse the response JSON data
            data = response.json()
            return data
        else:
            for _ in range(2):
                # Adding Time Sleep for the Giving the Time Gap to the URL Hit
                time.sleep(2)
                # Try Again Process Start :-
                if status_code == 200:
                    print(f'Retrying to get Connection  Try: {_+1} Url:{BaseRequest}')
                    # Parse the response JSON data
                    data = response.json()
                    return data
    except Exception as e:
        # Log an error if there's an exception during the request
        logger.error(e)
        for _ in range(3):
            try :
                logger.info(f'Retrying to get Connection After Error Try: {_+1} Url:{BaseRequest}')
                print(f'Retrying to get Connection After Error Try: {_+1} Url:{BaseRequest}')
                # Send a GET request to the person_request URL and get the response
                response = requests.get(BaseRequest)
                # Adding Time Sleep for the Giving the Time Gap to the URL Hit
                time.sleep(2)
                # Try Again Process Start :-
                if status_code == 200:
                    # Parse the response JSON data
                    print(f'Retrying to get Connection After Error Try: {_+1}')
                    data = response.json()
                    return data
            except:
                pass

#This function process each press release to give all required info and store it in ES.
def refining_dict(notices_doc):
        # Set a Dictionary to store the extracted data for the ES document
        # changing keys Field of dictionary
        notices_doc['entity_last_name']               = notices_doc.pop('name')
        notices_doc['entity_first_name']              = notices_doc.pop('forename')
        notices_doc['entity_sex']                     = notices_doc.pop('sex_id')
        notices_doc['entity_nationality']             = notices_doc.pop('nationalities')
        notices_doc['entity_place_of_birth']          = notices_doc.pop('place_of_birth')
        notices_doc['entity_place_of_birth_country']  = notices_doc.pop('country_of_birth_id')
        notices_doc['languages_spoken']               = notices_doc.pop('languages_spoken_ids')
        notices_doc['hair_colour']                    = notices_doc.pop('hairs_id')  
        notices_doc['eyes_colour']                    = notices_doc.pop('eyes_colors_id')  
        if Notice_Type.lower() == 'red':
            notices_doc['relationship_details']           = notices_doc.pop('charge')  
        # Updating the necessary fields in dictionary
        notices_doc['time_master']        =  datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3]+'Z'
        notices_doc["time_collected"]     =  datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3]+'Z'
        notices_doc["time_uploaded"]      =  datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3]+'Z'
        notices_doc["time_document"]      =  datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3]+'Z'             
        notices_doc["doc_source_url"]     =  (Doc_source_url)             
        notices_doc["doc_source"]         =  (Doc_source)        
        notices_doc["doc_source_type"]    =  (Doc_source_type)           
        notices_doc["entity_type"]        =  (Entity_type)              
        notices_doc["relationship_type"]  =  (Relationship_type)   

        # Print the full_info dictionary (for debugging purposes)
        # print(notices_doc)
        notices_doc_without_none = {key: value for key, value in notices_doc.items() if value is not None}
        update_phy_des_dict(notices_doc_without_none)

# Define a function to update the dictionary
def update_phy_des_dict(notices_doc_without_none):
        got_value = False
        # List of keys to check for in the dictionary
        keys_to_check = ["height", "weight", "hair_colour", "eyes_colour", "languages_spoken", "distinguishing_marks"]
        physical_descriptions = []  # List to store key-value pairs
        # Iterate through the list of keys to check
        for key in keys_to_check:
            # Check if the key is present in the dictionary
            if key in notices_doc_without_none:
                got_value = True
                if type(notices_doc_without_none[key]) == list:
                    # Add the value of the key before removing it Append key-value pair to the list
                    physical_descriptions.append(f"{key}: {notices_doc_without_none[key][-1]};")
                else:
                    physical_descriptions.append(f"{key}: {notices_doc_without_none[key]};")
                # If the key is present, remove it from the dictionary
                notices_doc_without_none.pop(key)
        if got_value:
            # Join the key-value pairs into a single string
            physical_des = " ".join(physical_descriptions)
            # Add a new key "entity_notes" with the value "Physical description"
            notices_doc_without_none["entity_notes"] = "Physical description: " + physical_des
            send_data_to_es(notices_doc_without_none)
        else:
            send_data_to_es(notices_doc_without_none)

def send_data_to_es(notices_doc_without_none):
    try:    
        # Generate a unique UUID for the document ID
        document_id = create_sha256_signature(notices_doc_without_none['entity_id'])

        # Generate a unique UUID for the document ID
        # document_id = str(uuid.uuid4())
        
        # Index the notices_doc dictionary as a document in Elasticsearch with the specified index_name_es and document_id
        resp = es.index(index=index_name_es.lower(), id=document_id, body=notices_doc_without_none)  # Sending Data into ES
        es_handler(resp,notices_doc_without_none,document_id)
    except Exception as e:
        logging.error("Exception occurred while ES uploading:", exc_info=True)

def es_handler(resp,notices_doc_without_none,document_id):
    print(resp)
    if resp['_version'] != 1:
        with open(f'{index_name_es} duplicates.txt','a') as file:
            file.writelines('\nURL: ')
            file.writelines(url_hit)
            file.writelines('\nDoc_ID: ')
            file.writelines(document_id)
            file.writelines('\n')
            file.writelines(str(notices_doc_without_none))
            file.writelines('\n\n')

    

# Function to get external details for a person based on the Interpol notices data
def get_external_details(person_info,notice):
    try:
        # Parse the response JSON data
        person_data = get_webdata(person_info)
        # Remove the "_links" key from the person_data.
        person_data.pop("_embedded")
        person_data.pop("_links")
        # Merging the two Dict to make them full information about a single person
        full_info = {**notice,**person_data}
        if Notice_Type.lower() == 'red':
            # Extract the "arrest_warrants" dictionary from the current full_info.
            arrest_warrants = full_info["arrest_warrants"][0]
            notices_doc = {**full_info,**arrest_warrants}
        else:
            notices_doc = full_info

        entity_date_of_birth = notices_doc["date_of_birth"]
        try:
            # Convert input date string to a datetime object
            date_object = datetime.datetime.strptime(entity_date_of_birth, "%Y/%m/%d")
        except ValueError:
            dateofbirth = f"{entity_date_of_birth}/01/01"
            date_object = datetime.datetime.strptime(dateofbirth, "%Y/%m/%d")
        # Format the datetime object in ISO 8601 format
        date_of_birth = date_object.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3]+'Z'
        notices_doc["entity_dob"] = date_of_birth
        # Remove the "arrest_warrants" key from the full_info.
        notices_doc.pop("_links")
        notices_doc.pop("date_of_birth")
        if Notice_Type.lower() == 'red':
            notices_doc.pop("issuing_country_id")
            notices_doc.pop("arrest_warrants")
        # Call another function to scrape and upload the obtained data into the ES (Elasticsearch)
        refining_dict(notices_doc)
    except Exception as e:
        # Log an error if there's an exception during the request
        logging.error("Exception occurred on userpage:", exc_info=True)

# Function to get Interpol notices data
def get_interpol_notices(request):
        global url_hit
        # print the URL for Debug process
        logger.info(f"Hitting URL: {request}")
        print(f"Hitting URL: {request}")
        url_hit = request
        # Send a GET request to the request URL and get the response
        data = get_webdata(request)
        # Extract the 'notices' array from the JSON response
        notices = data['_embedded']['notices']
        # Loop through each notice in the 'notices' list.
        for notice in notices:
            # Try to access details about the notice using its "_links" key.
            try:
                # Extract the "_links" dictionary from the current notice.
                detail_link = notice["_links"]
                try:
                    # Extract the URL to the thumbnail image from the "detail_link" dictionary.
                    entity_picture = detail_link.get('thumbnail')['href']
                except :
                    entity_picture = None
                # Extract the Personal Information of Each Person
                person_info = detail_link.get('self')['href']
                # Add the extracted thumbnail URL to the notice dictionary as "entity_picture".
                notice["entity_profile_image_url"] = entity_picture
                get_external_details(person_info,notice)
            # If there's an exception (error) during the above process, catch it and handle it.
            except Exception as e:
                # Print the error message in log file for debugging.
                logging.error("Exception occurred on Webpage:", exc_info=True)


# Function to calculate the number of pagination pages based on total notices and results per page
def pagination_num(request):
    try:
        # Send a GET request to the request URL and get the response & Parse the response JSON data
        data = get_webdata(request)
        # Extract the total number of notices and results per page from the JSON response
        total_notices = data['total']
        result_per_page = data['query']['resultPerPage']
        # Return the number of pages as an integer
        return int(total_notices)
    except Exception as e:
        # Log an error if there's an exception during the request
        logger.error(e)
        logger.info("Getting Page Details Retrying Again")
        # Send a GET request to the request URL and get the response & Parse the response JSON data
        data = get_webdata(request)
        # Extract the total number of notices and results per page from the JSON response
        total_notices = data['total']
        result_per_page = data['query']['resultPerPage']
        # Return the number of pages as an integer
        return int(total_notices)


#First get the all of Notices which has Unknown Gender 
def get_unknown_gen():
    request = f'{base_request_url}/notices/v1/{Notice_Type.lower()}?&sexId=U&resultPerPage=160&page=1'
    num_notices = pagination_num(request)
    logger.info(f'Total Number of Notices of Unkown Gender {num_notices}')
    if 160 > (num_notices):
        get_interpol_notices(request)

def extreme_scrape(request):
    logger.info('Extreme Scrape Function Started')
    for country in nationalities:
        filter_res = request.split('&resultPerPage')
        add_filter = f'&arrestWarrantCountryId={country}&resultPerPage=160&page=1'
        new_res = filter_res[0] + add_filter
        num_notices = pagination_num(new_res)
        if num_notices != 0:
            get_interpol_notices(new_res)

def get_data_wcountry(nation,num_notices):
    global url_hit
    for gender in gender_list:
        request = f'{base_request_url}/notices/v1/{Notice_Type.lower()}?nationality={nation}&sexId={gender}&resultPerPage=160&page=1'
        num_notices = pagination_num(request)
        url_hit = request
        logger.info(f'Total Notices:- {num_notices} Gender: {gender} in Country ={nation}')
        print(f'Total Notices:- {num_notices} Gender: {gender} in Country ={nation}')
        # Condition 1: Filters [Age Proceeding]{Gender: Female with Specific Country}
        if 160 < (num_notices):
            #Dividing Age Slab According to Child & Young & Adult & Old 
            age_limits = [(0,20),(21,50),(51,60),(60,100)]
            for age_group in age_limits:
                if age_group == (21,50):
                    for age in range(21,50):
                        request = f'{base_request_url}/notices/v1/{Notice_Type.lower()}?nationality={nation}&ageMin={age}&ageMax={age}&sexId={gender}&resultPerPage=160&page=1'
                        num_notices = pagination_num(request)
                        print(f"Age : {age} Total Number of Notices: {num_notices}")
                        if num_notices > 160:
                            logger.info(f"In Country {nation} Notices is in Age {age} is {num_notices}")
                            extreme_scrape(request)
                        else:
                            get_interpol_notices(request)
                else:       
                    request = f'{base_request_url}/notices/v1/{Notice_Type.lower()}?nationality={nation}&ageMin={age_group[0]}&ageMax={age_group[1]}&sexId={gender}&resultPerPage=160&page=1'
                    num_notices = pagination_num(request)
                    url_hit = request
                    print(f"Person Age {age_group[0]} to {age_group[1]} Total Notices:- {num_notices}")
                    get_interpol_notices(request)
        elif num_notices == 0:
            print(f'0 Notices in Country [{nation}] and Gender: {gender}')      
            logger.info(f'0 Notices in Country [{nation}] and Gender: {gender}')      
            
        else:
            get_interpol_notices(request)
            print(f'Data Uploaded Successfully of Country [{nation}] and Gender: {gender}')      
            logger.info(f'Data Uploaded Successfully of Country [{nation}] and Gender: {gender}')      


if __name__ == "__main__":
    try:
        #Get the Elasticsearch connection object (es) based on the environment ('dev' or 'prod')
        es = get_es_connection(env=envirotment)  # Pass 'dev' or 'prod' as the argument
        # Get the all of the Country Code in nationalities array
        get_nat_array()
        logger.info(f'We have Total {len(nationalities)} Country Data')
        print(f'We have Total {len(nationalities)} Country Data')
        get_unknown_gen()
        # Getting the Data by applying specific filters            
        for nation in nationalities: # Loop Throught the base of Country Code 
            request = f'{base_request_url}/notices/v1/{Notice_Type.lower()}?nationality={nation}&resultPerPage=160&page=1'
            num_notices = pagination_num(request)
            print(f'Total Notices:- {num_notices} in Country = {nation}')
            logger.info(f'Total Notices:- {num_notices} in Country = {nation}& We Coverd Almost {nationalities.index(nation)+1} Country Data')
            if 160 < (num_notices): # Condition 1: Filters {Gender with Specific Country}
                get_data_wcountry(nation,num_notices)
            else:
                get_interpol_notices(request)
                print('Data Uploaded Successfully of Country:',nation) 
        es.transport.close()# closing the es connection
    except Exception as e:
        logging.error("Exception occurred", exc_info=True)
