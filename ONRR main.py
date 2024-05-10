# Importing required libraries and modules
import logging,time,traceback,tabula,datetime,hmac,hashlib,binascii,re,uuid
from get_es_connection import get_es_connection

index_name_es = 'onrr1234'
base_url      = 'https://www.onrr.gov/'
master_url    = 'https://www.onrr.gov/compliance-enforcement/enforcement?tabs=civil-penalties'
key_sig_256   = "f7bc83f430538424b13298e6aa6fb143ef4d59a14946175997479dbc2d1a394e"

# Logging implementation settings
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)
log_path = f'{index_name_es}.log'  # Log file path
logging.basicConfig(filename=log_path, filemode='w', format='%(asctime)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)  # Setting up logging

# Function to create a SHA-256 signature
def create_sha256_signature(message):
    # Convert the hexadecimal key to bytes
    byte_key = binascii.unhexlify(key_sig_256)
    # Encode the message (a string) as bytes
    message = message.encode()
    # Create a new HMAC (Hash-based Message Authentication Code) object with SHA-256
    hmac_obj = hmac.new(byte_key, message, hashlib.sha256)
    # Calculate the HMAC hash and convert it to uppercase hexadecimal representation
    signature = hmac_obj.hexdigest().upper()
    # Return the calculated signature
    return signature

def send_data_to_es(pdfdictdata):
        # Set various fields in the `pdfdictdata` dictionary
        pdfdictdata['doc_source_type']    = 'Press Release'
        pdfdictdata['doc_source']         = 'department of interior, office of natural resources revenue'
        pdfdictdata['doc_source_url']     = base_url
        pdfdictdata['doc_source_pdf_url'] = master_url
        # Format the datetime object in ISO 8601 format
        date_object                       = datetime.datetime.strptime(f"{year}/12/31", "%Y/%m/%d")
        pdfdictdata['time_master']        = date_object.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3]+'Z'
        pdfdictdata['time_collected']     = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3]+'Z'
        pdfdictdata['time_uploaded']      = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3]+'Z'
        pdfdictdata['time_document']      = date_object.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3]+'Z'  
        # Generate a unique UUID for the document ID
        document_id = str(uuid.uuid4())
        # document_id = create_sha256_signature(pdfdictdata['message_id']+pdfdictdata['entity_full_name'])
        resp = es.index(index=index_name_es, id=document_id, body=pdfdictdata)  # Sending Data into ES
        print(resp)


# Function to extract and process merged text data
def text_extract_pattern_merged(dict_row):
    global violation, regulation  # Declare global variables for violation and regulation
    # Define a list of patterns to search for in 'Violation Regulation(s)' column
    pattern_list = [r'30 CFR', r'Part', r'and 30 ', r'CFR ', r'Subpart']
    vigulation = dict_row['Violation Regulation(s)']  # Get the value of 'Violation Regulation(s)' column
    # Iterate through the patterns in pattern_list
    for pat in pattern_list:
        lation = (vigulation.split(pat))  # Split the 'Violation Regulation(s)' value using the current pattern
        # Check if the split result has more than one part (pattern found)
        if len(lation) != 1:
            violation += vigulation[:vigulation.index(pat)]  # Append the text before the pattern to 'violation'
            regulation += vigulation[vigulation.index(pat):] + ' '  # Append the text after the pattern to 'regulation' with a space
            break  # Exit the loop when a pattern is found
    # Check if the 'Business Name' column value is not of type float
    if type(dict_row['Business Name']) != float:
        # Create a dictionary named 'data_dict' with various keys and corresponding values
        data_dict = {'message_title': message_title,
                     'entity_full_name': dict_row['Business Name'],
                     'message_id': dict_row['Case Number'],
                     'message_summary': violation,
                     'message_tags': regulation,
                     'message_value': refine_message_value(dict_row['Payments'])}

        send_data_to_es(data_dict)  # Send the 'data_dict' dictionary to Elasticsearch
        violation, regulation = '', ''  # Reset the 'violation' and 'regulation' variables to empty strings

# Function to extract and process header data
def text_extract_pattern_header(dict_row):
    global violation, regulation  # Declare global variables for violation and regulation
    print(dict_row)
    # Check if the 'Violation' column value is not of type float
    if type(dict_row['Violation']) != float:
        violation += dict_row['Violation']  # Append the 'Violation' column value to the 'violation' variable
    # Check if the 'Regulation(s)' column value is not of type float
    if type(dict_row['Regulation(s)']) != float:
        regulation += dict_row['Regulation(s)'] + ' '  # Append the 'Regulation(s)' column value to the 'regulation' variable with a space
    # Check if the 'Business Name' column value is not of type float
    if type(dict_row['Business  Name']) != float:
        # Create a dictionary named 'data_dict' with various keys and corresponding values
        data_dict = {'message_title': message_title,
                     'entity_full_name': dict_row['Business Name'],
                     'message_id': dict_row['Case Number'],
                     'message_summary': violation,
                     'message_tags': regulation,
                     'message_value': refine_message_value(dict_row['Payments'])}
        send_data_to_es(data_dict)  # Send the 'data_dict' dictionary to Elasticsearch
        violation, regulation = '', ''  # Reset the 'violation' and 'regulation' variables to empty strings

def refine_message_value(message_value):
    # Use regular expression to extract digits and commas
    matches = re.findall(r'\d+', message_value)
    # Join the extracted digits and remove commas
    numeric_str = ''.join(matches).replace(',', '')
    # Convert the numeric string to a int
    numeric_double = int(numeric_str)
    return (numeric_double)

# Function to process PDF data for different years
def mainfunc():
    global message_title, year  # Declare global variables for message title and year
    current_year = datetime.datetime.now().year  # Get the current year
    # Loop through years from 2017 to the current year
    for year in range(2018, current_year):
        print('Working on Year:', year)  # Print the current year being processed
        # Determine the PDF URL based on the year
        if year >= 2018 and year <= 2021:
            pdf_url = base_url + f'/document/{year}.pdf'
        elif year == 2022:
            pdf_url = base_url + f'/document/{year}_Penalties.pdf'
        else:
            pdf_url = base_url + f'/document/{year}_Penalties.pdf'
        message_title = f"PENALTY COLLECTIONS FY {year}"  # Set the message title for the current year
        # Extract tabular data from the PDF (you can specify page numbers or 'all' for all pages)
        tables = tabula.read_pdf(pdf_url, pages='all')
        # Convert each table extracted from the PDF into a Pandas DataFrame
        dfs = [table for table in tables]
        # Now, you can work with the DataFrames as needed
        for idx, df in enumerate(dfs):
            dataframe_to_dict_list(df)

# Function to convert a DataFrame to a list of dictionaries
def dataframe_to_dict_list(dataframe):
    global violation, regulation      # Declare global variables
    violation, regulation = '', ''  # Initialize violation and regulation variables as empty strings
    for index, row in dataframe.iterrows():  # Iterate through rows in the DataFrame
        dict_row = row.to_dict()  # Convert the current row to a dictionary
        try:
            vigulation = dict_row['Violation Regulation(s)']  # Get the 'Violation Regulation(s)' value
            text_extract_pattern_merged(dict_row)  # Call a function to extract and process text
        except KeyError as error:  # Handle KeyError exceptions
            if str(error) == f"'Violation Regulation(s)'":  # Check if the error is related to a missing key
                text_extract_pattern_header(dict_row)  # Call a function to handle header data


if __name__ == '__main__':  # This condition checks if the script is being executed as the main program.
    logger.info('Starting script- FDAScript.py')  # Logs an informational message indicating the start of the script execution.
    t1 = time.time()  # Records the current time using the `time.time()` function.
    # try:
    es = get_es_connection(env='local')  # Calls a function `get_es_connection` to establish a connection to Elasticsearch with the 'local' environment.
    # The environment can be 'dev' or 'prod' depending on the use case.
    mainfunc()  # Calls the `mainfunc` function, which is responsible for processing PDF data and sending it to Elasticsearch.
    es.transport.close()  # Closes the connection to Elasticsearch after processing.
    # Logs an informational message indicating the completion of the script execution and the total time taken.
    logging.info('Script Completed Total time took for complete run is {}'.format(time.time() - t1))
    # except:
    #     # In case of an exception, logs an error message indicating that the master page URLs couldn't be fetched.
    #     logger.error("master page URLs couldn't be fetched",exc_info=True)
    #     # Prints a traceback of the exception for debugging purposes.
    #     traceback.print_exc()
