from elasticsearch import Elasticsearch
from sys import platform

def get_es_connection(env):
    if env == 'dev':
        password = ''
        if platform == 'linux' or platform == "linux2":
            host_name = 'elasticsearch:9200'
        elif platform == 'win32':
            host_name = ''
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





