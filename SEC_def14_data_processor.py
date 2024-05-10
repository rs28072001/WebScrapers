'''
Creator: D&I, ALQIMI
This script uses sec_edgar_downloader package to download SEC Form DEF 14A filings via 
SEC Edgar Database for a given CIK (Central Index Key)/Ticker Symbol and save filings 
in zip format on AWS S3 Bucket.

SEC Form DEF 14A: is a filing with the Securities and Exchange Commission (SEC) that 
must be filed by or on behalf of a registrant when a shareholder vote is required.  
The form should provide security holders with sufficient information to allow them 
to make an informed vote at an upcoming security holders' meeting or to authorize a 
proxy to vote on their behalf.
'''

# required imports
import boto3, csv, os, zipfile, shutil, logging
from time import sleep
from sec_edgar_downloader import Downloader

# ticker symbol csv file
filename = r'stocks.csv'

# logging settings
log_path = r'/usr/local/lib/python3.7/site-packages/secdef14/z_secdef14_data_processor.log'
logging.basicConfig(filename=log_path, filemode='w', format='%(asctime)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# AWS S3 Bucket settings
s3_client = boto3.client(service_name='s3', region_name='us-east-1',
                         aws_access_key_id='Your Key ID',
                         aws_secret_access_key='You r Secreat Access key')

# S3 bucket name
bucket_name = 'secdef14'

# get the hard coded path of sec edgar filing lib.
down_dir = os.getcwd()
# sub directory of hard coded path given by package.
download_folder = down_dir + '\\sec-edgar-filings'

with open(filename, 'r') as csvfile:
    # Skip the headers row
    csvreader = csv.reader(csvfile)
    # Find the index of the "ticker" column
    headers = next(csvreader)
    ticker_idx = headers.index("TICKER")
    for row in csvreader:# Loop through the items in the CSV
        # Append the value in the "ticker" column to the list
        ticker = row[ticker_idx]

    # The title and ticker values
    logger.info(f'Currently wokring on Ticker : {ticker}....')
    try:
        # Create a new instance of the Downloader class
        dl = Downloader()
        # Use the Downloader class to download the DEF 14A form for the current ticker
        f1 = dl.get("DEF 14A", ticker, after='2021-12-31', before='2023-01-01')
    except Exception as e:
        logger.error(f'Error Occur While Downloading {ticker} Files: {e}')
        for run in range(5):
            sleep(5)
            try:
                # to download ticker if failed in try block
                f1 = dl.get("DEF 14A", ticker, after='2021-12-31',
                            before='2023-01-01')
                break
            except Exception as e:
                logger.info(f"{run}. Failed, Try Again ")
                f1 = e
    # in case of network error
    if type(f1) != int:
        logger.error(f"{ticker} has Network Error")
    # in case tikcer hasn't got any filings
    elif f1 == 0:
        logger.info(f"{ticker} has 0 files")
    else:
        logger.info(
            f'All Downloading Done of : {ticker} and Total Downloaded Files : {f1}')
        try:  # Upload all files to S3 bucket
            zipdir = download_folder+f'\{ticker}'  # Create a ZIP archive
            zip_filename = os.path.join(zipdir + '.zip')
            with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zip:
                for root, dirs, files in os.walk(zipdir):
                    for file in files:
                        zip.write(os.path.join(root, file))
            logger.info(f'Converted Zip File Name:- {ticker}.zip...')
            uploading = s3_client.upload_file(
                zip_filename, bucket_name, f"DEF_14A/{ticker}")
            if (uploading) is None:  # Upload status logging
                logger.info(f'File Uploaded Successfully {ticker}.zip\n\n')
                shutil.rmtree(zipdir)
                os.remove(zip_filename)
            else:
                logger.error(
                    f'BOTO Error Occur in Ticker{ticker} : {uploading}')
        except FileNotFoundError:  # If the file is not found, continue to the next file
            pass
