
#https://pinglab-utils.github.io/docs/graph/query_neo4j/
#https://icd.who.int/browse/2024-01/mms/en#402520533 
#https://neo4j.com/docs/api/python-driver/current/ (hvordan sette opp neo4j database)
#https://icdcdn.who.int/icd11referenceguide/en/html/index.html
#https://id.who.int/swagger/index.html


import requests
import os
import re
import certifi
import urllib3
import csv
import json
from typing import Optional
import time
from dotenv import load_dotenv
from neo4j import GraphDatabase

urllib3.disable_warnings()

EntitiesCreated = []
counter = 0
max_count = 200000

# access ICD API
baseLinear = 'https://id.who.int/icd/release/11/2019-04/mms/lookup?foundationUri='
baseFoundation = 'http://id.who.int/icd/entity/'

http_session = requests.Session()
csv_data = []
csv_log=[]
icd_headers = None

# Load environment variables
load_dotenv()

class FoundationEntity:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', None)
        self.title =kwargs.get('title', None)  
        self.definition = kwargs.get('definition', None)
        self.long_definition = kwargs.get('long_definition', None)
        self.fully_specified_name = kwargs.get('fully_specified_name', None)
        self.diagnostic_criteria = kwargs.get('diagnostic_criteria', None)
        self.child = kwargs.get('child', None)
        self.parent = kwargs.get('parent', None)
        self.ancestor = kwargs.get('ancestor', None)
        self.descendant = kwargs.get('descendant', None)
        self.synonym = kwargs.get('synonym', None)
        self.narrowerTerm = kwargs.get('narrowerTerm', None)
        self.inclusion = kwargs.get('inclusion', None)
        self.exclusion = kwargs.get('exclusion', None)
        self.browserUrl = kwargs.get('browseUrl', None)

class LinearizationEntity:
    def __init__(self, **kwargs):
        # Initialize each attribute from kwargs with default to None if not provided
        self.id = kwargs.get('id', None)
        self.title = kwargs.get('title', None)
        self.definition = kwargs.get('definition', None)
        self.long_definition = kwargs.get('long_definition', None)
        self.fully_specified_name = kwargs.get('fully_specified_name', None)
        self.diagnostic_criteria = kwargs.get('diagnostic_criteria', None)
        self.source = kwargs.get('source', None)
        self.code = kwargs.get('code', None)
        self.coding_note = kwargs.get('coding_note', None)
        self.block_id = kwargs.get('block_id', None)
        self.code_range = kwargs.get('code_range', None)
        self.class_kind = kwargs.get('class_kind', None)
        self.child = kwargs.get('child', None)
        self.parent = kwargs.get('parent', None)
        self.ancestor = kwargs.get('ancestor', None)
        self.descendant = kwargs.get('descendant', None)
        self.foundation_child_elsewhere = kwargs.get('foundation_child_elsewhere', None)
        self.index_term = kwargs.get('index_term', None)
        self.inclusion = kwargs.get('inclusion', None)
        self.exclusion = kwargs.get('exclusion', None)
        self.related_entities_in_maternal_chapter = kwargs.get('related_entities_in_maternal_chapter', None)
        self.related_entities_in_perinatal_chapter = kwargs.get('related_entities_in_perinatal_chapter', None)
        self.postcoordination_scale = kwargs.get('postcoordination_scale', None)
        self.browser_url = kwargs.get('browser_url', None)

    @classmethod
    def init_from_foundation_entity(cls, foundation_entity: FoundationEntity):
        return cls(
            id=foundation_entity.id,
            title=foundation_entity.title,
            definition=foundation_entity.definition,
            long_definition=foundation_entity.long_definition,
            exclusion=foundation_entity.exclusion,
            inclusion=foundation_entity.inclusion
        )
        
    
    def __str__(self):
        # Convert the dictionary of all properties to a JSON string
        # Using `default=str` to handle non-serializable objects gracefully
        return json.dumps(self.__dict__, ensure_ascii=False, indent=4, default=str)

class FoundationEntity:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', None)
        self.title = kwargs.get('title', None)
        self.definition = kwargs.get('definition', None)
        self.long_definition = kwargs.get('long_definition', None)
        self.fully_specified_name = kwargs.get('fully_specified_name', None)
        self.diagnostic_criteria = kwargs.get('diagnostic_criteria', None)
        self.child = kwargs.get('child', None)
        self.parent = kwargs.get('parent', None)
        self.ancestor = kwargs.get('ancestor', None)
        self.descendant = kwargs.get('descendant', None)
        self.synonym = kwargs.get('synonym', None)
        self.narrower_term = kwargs.get('narrowerTerm', None)
        self.inclusion = kwargs.get('inclusion', None)
        self.exclusion = kwargs.get('exclusion', None)
        self.browser_url = kwargs.get('browserUrl', None)
        self.linearization_entity : Optional [LinearizationEntity] = kwargs.get('linearizationEntity', None)

    def __str__(self):
        # Convert the dictionary of all properties to a JSON string
        # Using `default=str` to handle non-serializable objects gracefully
        return json.dumps(self.__dict__, ensure_ascii=False, indent=4, default=str)

def request_headers():
    token_endpoint = 'https://icdaccessmanagement.who.int/connect/token'

    client_id = os.getenv('ICD_CLIENT_ID')
    client_secret = os.getenv('ICD_CLIENT_SECRET')
    scope = 'icdapi_access'
    grant_type = 'client_credentials'

    # set data to post
    payload = {'client_id': client_id, 
            'client_secret': client_secret, 
            'scope': scope, 
            'grant_type': grant_type}

    # make request
    r = requests.post(token_endpoint, data=payload, verify=True).json()
    print(r)
    token = r['access_token']

    # HTTP header fields to set
    headers = {'Authorization':  'Bearer '+token, 
            'Accept': 'application/json', 
            'Accept-Language': 'en',
        'API-Version': 'v2'}
    return headers

class Timer:
    def __init__(self, duration=3000):
        self.duration = duration
        self.start_time = None

    def start(self):
        """Start or restart the timer."""
        self.start_time = time.time()
        print("Timer started.")

    def check(self):
        """Check if the timer has reached its duration since the last start."""
        if not self.start_time:
            return False  # Timer has never been started
        elapsed_time = time.time() - self.start_time
        if elapsed_time >= self.duration:
            return True
        return False
    def elapsed_time(self):
        return time.time() - self.start_time


    def reset(self):
        print("Reset the timer by setting the start time to the current time.")
        self.start()

# Function to escape single quotes
def escape_single_quotes(value):
    return value.replace("'", " ")

def extract_numerical_part(url):
    # Use a regular expression to find all sequences of digits in the stemId
    matches = re.findall(r'\d+', url)
    if matches:
        # Return the longest match, assuming it represents the main identifier
        return max(matches, key=len)
    return None

def check_substring_in_url(substring, url):
    return substring in url

def make_request(url, timeout=60):
    global headers_timer
    global icd_headers
    # check for timer, 
    if headers_timer.check():
        # renew headers after 600 sec
        icd_headers = request_headers()
        headers_timer.reset()
    try:
        for _ in range(3):  # Retry up to 3 times
            response = http_session.get(url=url, headers=icd_headers, timeout=timeout, verify=False)
            if response.status_code == 200:
                return response
            if response.status_code == 404:
                print(f'Request return not found {url}, response:<{response}><{response.status_code}><{headers_timer.elapsed_time()}>')
                # not found, 
                return None
            if response.status_code == 401:
                elapsed_time_formatted = f"{headers_timer.elapsed_time():.2f}"
                error_message = f"Request failed with error: 401 at {elapsed_time_formatted} seconds"
                print(error_message)
                csv_log.append([error_message])
                
                # Try to renew headers safely
                try:
                    time.sleep(3)
                    icd_headers = request_headers()
                except Exception as e:
                    print(f"Failed to renew headers: {e}")
                    # Handle failure to renew headers, possibly re-raise or log
            else:
                elapsed_time_formatted = f"{headers_timer.elapsed_time():.2f}"
                error_message = f"Request failed, retying, response:<{response}><{response.status_code}>{elapsed_time_formatted} seconds"
                print(error_message)
       
    except Exception as e:
        print(f'Request failed with error: {e}')
        csv_log.append([f'Request failed with error: {e}'])
    return None  # Return None if all retries fail or an exception is raised


def fetch_children(uri, depth=0, parent_entity: FoundationEntity = None, max_depth=10):
    global counter, max_count
    if depth > max_depth:
        print("Maximum recursion depth reached.")
        csv_log.append(["Maximum recurssion depth reached."])
        return
    counter = counter + 1

    if counter == max_count:
        print("max_count reached.")
        csv_log.append(["max_count reached."])
        return

    entity = FoundationEntity()

    response = make_request(url=uri, timeout=50)
    if response:
        data = response.json()

        if(response.status_code==200):

            entity.id = data.get('@id')
            num_id = extract_numerical_part(entity.id)
            entity.title = escape_single_quotes(data['title']['@value'])

            entity.child = data.get('child', [])
            entity.parent = data.get('parent', [])
            exclusion = data.get('exclusion',[])
            labels = [excl['label']['@value'] for excl in exclusion]
            # Create a single string with labels separated by commas
            entity.exclusion = escape_single_quotes(', '.join(labels))

            entity.definition = escape_single_quotes(data.get('definition', {}).get('@value', ''))
            # # inherit from parent
            # if(parent_entity):
            #     if(parent_entity.definition):
            #         definition = parent_entity.definition +"/"+ definition

            entity.long_definition = escape_single_quotes(data.get('longDefinition', {}).get('@value', ''))
            #  # inherit from parent
            # if(parent_entity):
            #     if(parent_entity.long_definition):
            #         long_definition = parent_entity.long_definition +"/"+ long_definition

            synonyms = data.get('synonym',[])
            labels = [synonym['label']['@value'] for synonym in synonyms]
            # Create a single string with labels separated by commas
            entity.synonym = escape_single_quotes(', '.join(labels))


            # check linearization
            code = None
            
            linear_response = make_request(url=baseLinear+uri, timeout=60)
            if linear_response: 
                if(linear_response.status_code==200):
                    linear_data = linear_response.json()                    
                    # get the code
                    
                    linearization_entity = LinearizationEntity.init_from_foundation_entity(entity)
                    linearization_entity.code = linear_data.get('code', None)
                    code = linearization_entity.code 
                    entity.linearization_entity = linearization_entity

                    # get source (exists only if MMS code, or grouping MMS code)
                    source = linear_data.get('source')
                    if(source):
                        entity.linearization_entity.source = source
                        stem_id = extract_numerical_part(source)
                        
                        # source indicates a stemId
                        # several FoundationEntities are grouped under the same stemId
                        # we only want to create a single entity for the stemId:
                        if((stem_id==num_id) and (stem_id not in EntitiesCreated)):
                
                            # create entity
                            print(f'Create: {entity.linearization_entity.code} stemId: {stem_id} source: {entity.linearization_entity.source}')
                            csv_log.append([f'Create: {entity.linearization_entity.code} stemId: {stem_id} source: {entity.linearization_entity.source}'])
                            indexTerms = linear_data.get('indexTerm', [])
                            terms = [term['label']['@value'] for term in indexTerms]
                            indexTerms = ', '.join(terms)
                            entity.linearization_entity.index_term = escape_single_quotes(indexTerms)
                            entity.linearization_entity.browser_url = linear_data.get('browserUrl')
                            entity.linearization_entity.child = data.get('child', []) #overide, get it from Linearization
                            entity.linearization_entity.parent = data.get('parent', []) #overide, get it from Linearization
        
                            transaction = (
                                f"MERGE(a:LinearizationEntity{{ID: '{entity.linearization_entity.id}'}}) "
                                f"ON CREATE SET a.title = '{entity.linearization_entity.title}',"
                                f"a.indexTerms = '{entity.linearization_entity.index_term}',"
                                f"a.definition = '{entity.linearization_entity.definition}',"
                                f"a.long_definition = '{entity.linearization_entity.long_definition}',"
                                f"a.browserUrl = '{entity.linearization_entity.browser_url}',"
                                f"a.code = '{entity.linearization_entity.code}',"
                                f"a.exclusion = '{entity.linearization_entity.exclusion}',"
                                f"a.synonyms = '{entity.synonym}',"
                                f"a.parents = {entity.linearization_entity.parent},"
                                f"a.children = {entity.linearization_entity.child}"
                     
                            )

                            with driver.session() as session:
                                session.run(transaction)

                            EntitiesCreated.append(num_id)
            b = "-" * (depth + 1)
            print(f'{counter}'+b+ f'>id:{num_id}-<{kap_nr}><{code}>-<{depth}>{entity.title}')
            csv_log.append([f'{counter}'+b+ f'>id:{num_id}-{kap_nr}-{code}-{depth}-{entity.title}'])
            csv_data.append([f'{entity}'])

        if not isinstance(entity.child, list):
            print(">>Expected 'children' to be a list but got:", type(entity.child))
            return

        for child in entity.child:
            if (not check_substring_in_url('other', child)) and (not check_substring_in_url('unspecified', child) and(counter<max_count)):
                fetch_children(uri=child, parent_entity = entity, depth = depth + 1) 
    else:
        print(f'make_request returned None for {uri}')
        csv_log.append([f'make_request returned None for {uri}'])
        

driver = GraphDatabase.driver(uri=os.getenv('NEO_URI'), auth=(os.getenv('NEO_USER'), os.getenv('NEO_NEO_PASSWORD')))


# Clean the graph database, if using with pre-existing data
with driver.session() as session:
        session.run("MATCH (a) DETACH DELETE a")




KapList = ["http://id.who.int/icd/entity/1435254666",
        "http://id.who.int/icd/entity/1630407678",
        "http://id.who.int/icd/entity/1766440644",
        "http://id.who.int/icd/entity/1954798891",
        "http://id.who.int/icd/entity/21500692",
        "http://id.who.int/icd/entity/334423054",
        "http://id.who.int/icd/entity/274880002",
        "http://id.who.int/icd/entity/1296093776",
        "http://id.who.int/icd/entity/868865918",
        "http://id.who.int/icd/entity/1218729044",
        "http://id.who.int/icd/entity/426429380",
        "http://id.who.int/icd/entity/197934298",
        "http://id.who.int/icd/entity/1256772020",
        "http://id.who.int/icd/entity/1639304259",
        "http://id.who.int/icd/entity/1473673350",
        "http://id.who.int/icd/entity/30659757",
        "http://id.who.int/icd/entity/577470983",
        "http://id.who.int/icd/entity/714000734",
        "http://id.who.int/icd/entity/1306203631",
        "http://id.who.int/icd/entity/223744320",
        "http://id.who.int/icd/entity/1843895818",
        "http://id.who.int/icd/entity/435227771",
        "http://id.who.int/icd/entity/850137482",
        "http://id.who.int/icd/entity/1249056269",
        "http://id.who.int/icd/entity/1596590595",
        "http://id.who.int/icd/entity/718687701",
        # "http://id.who.int/icd/entity/231358748",
        # "http://id.who.int/icd/entity/979408586"
]
                                                                                                                                                                                                                                                                                                                                                  
# make request           
# r = requests.get(uri, headers=headers, verify=False)
# # print the result
# print (r.text)
kap_nr = 0	
# intitiate timer for headers 
headers_timer = Timer()
headers_timer.start()
icd_headers = request_headers()	
try:
    for kap in KapList:
        kap_nr += 1
        print (f'New Kap{kap_nr}-{kap}')
        fetch_children(uri=kap, depth = 0, max_depth=10)
except Exception as e:
    print(f'fetch_children failed with error: {e}')
    csv_log.append([f'Request failed with error: {e}'])

print('Writing csv_data')
with open("MMS_ICD11_transaction_log.csv", mode='w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    writer.writerows(csv_data)
    csv_data=[]

print('Writing csv_log')
with open("MMS_ICD11_log.csv", mode='w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    writer.writerows(csv_log)

#Create edge with relationship "parents"
with driver.session() as session:
    session.run("MATCH (a:LinearizationEntity),(b:LinearizationEntity) "
            "WHERE a.ID in b.parents "
            "MERGE (a)<-[r:Parents]-(b)")
    
with driver.session() as session:
    session.run("MATCH (a:LinearizationEntity),(b:LinearizationEntity) "
            "WHERE a.ID in b.children "
            "MERGE (a)<-[r:Children]-(b)")
    
driver.close()
