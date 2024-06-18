
#https://pinglab-utils.github.io/docs/graph/query_neo4j/
#https://icd.who.int/browse/2024-01/mms/en#402520533 
#https://neo4j.com/docs/api/python-driver/current/ (hvordan sette opp neo4j database)
#https://icdcdn.who.int/icd11referenceguide/en/html/index.html

#for ICD-11:
#ClientId: 487eb68b-fb2b-4ac3-83a5-58a32c7b7e45_0eed45fa-c7a3-4c14-828c-c52c5bde59d6
#ClientSecret: xHrU0eIqGl3VssuOT6ewQpo5hhqqj7zfNqsPyYW0qbY=

# user
# temant: 6a2828dc-c732-46e9-9832-de22f72116ee
# Wait 60 seconds before connecting using these details, or login to https://console.neo4j.io to validate the Aura Instance is available
# NEO4J_URI=neo4j+s://49806a05.databases.neo4j.io
# NEO4J_USERNAME=neo4j
# NEO4J_PASSWORD=fr0detSnPFYJ5XVlSZy5uRMiZUPdJDpG5Ny5Iyvgsso
# NEO4J_PASSWORD=14141414
# AURA_INSTANCEID=49806a05
# AURA_INSTANCENAME=ICD11_MMS

import requests
import json
import re
from neo4j import GraphDatabase
import certifi
import urllib3
from typing import List
import csv
import uuid

# Disable SSL warnings
urllib3.disable_warnings()

# Set up the Neo4j driver
driver = GraphDatabase.driver(uri="bolt://localhost:7687", auth=("neo4j", "14141414"))
#driver = GraphDatabase.driver(uri="neo4j+s://49806a05.databases.neo4j.io", auth=("neo4j", "14141414"))

# Clean the graph database, if using with pre-existing data
with driver.session() as session:
    session.run("MATCH (a) DETACH DELETE a")

CODES = {"Prevensjon": [], "Navn": [], "ID": [] }

csv_data = []
csv_data.append(['Log', 'Description']  )

class Prevensjon:
    def __init__(self, **kwargs):
        self.navn = kwargs.get('navn')
        self.id = kwargs.get('id', None)
        self.definition = kwargs.get('definition', None)
        self.bivirkninger = kwargs.get('bivirkninger', None)
        self.hvordan_starte = kwargs.get('hvordan_starte', None)
        self.bruk = kwargs.get('bruk', None)
        self.hvordan_slutte = kwargs.get('hvordan_slutte', None)
        self.koster = kwargs.get('koster', None)
        self.nyttig_aa_vite = kwargs.get('nyttig_aa_vite', None)
    
    def __str__(self):
        return (f"Prevensjon(navn={self.navn}, id={self.id}, definition={self.definition}, bivirkninger={self.bivirkninger}, "
                f"hvordan_starte={self.hvordan_starte}, bruk={self.bruk}, hvordan_slutte={self.hvordan_slutte}, "
                f"koster={self.koster}, nyttig_aa_vite={self.nyttig_aa_vite})")
 
class Informasjon:
    def __init__(self, **kwargs):
        self.navn = kwargs.get('navn')
        self.type = kwargs.get('type')
        self.id = kwargs.get('id', None)
        self.definition = kwargs.get('definition', None)
        
    def __str__(self):
        return (f"Informasjon(type={self.type}, id={self.id}, definition={self.definition})")
    

def create_node_from_Prevensjon(m: Prevensjon):
    transaction = (
        "MERGE (a:Prevensjon {ID: $id}) "
        "ON CREATE SET a.navn = $navn, "
        "a.definition = $definition, "
        "a.bivirkninger = $bivirkninger, "
        "a.hvordan_starte = $hvordan_starte, "
        "a.bruk = $bruk, "
        "a.hvordan_slutte = $hvordan_slutte, "
        "a.koster = $koster, "
        "a.nyttig_aa_vite = $nyttig_aa_vite"
    )
    
    with driver.session() as session:
        session.run(
            transaction, 
            id=m.id, 
            navn=m.navn, 
            definition=m.definition, 
            bivirkninger=m.bivirkninger, 
            hvordan_starte=m.hvordan_starte, 
            bruk=m.bruk, 
            hvordan_slutte=m.hvordan_slutte, 
            koster=m.koster, 
            nyttig_aa_vite=m.nyttig_aa_vite
        )
            
def create_node_from_Informasjon(m: Informasjon):
    transaction = (
        "MERGE (a:Informasjon {ID: $id}) "
        "ON CREATE SET a.type = $type, "
        "a.navn = $navn, "
        "a.definition = $definition "
    )
    
    with driver.session() as session:
        session.run(
            transaction, 
            id=m.id, 
            type=m.type, 
            navn = m.navn,
            definition=m.definition, 
        )
 
 # Les inn MMS-koder fra JSON-fil
with open('Prevensjonsguiden.json', "r", encoding="utf-8-sig") as json_file:
    json_codes = json.load(json_file)
    Codes = json_codes.get("values", [])

    try:

        for code in Codes:
            prevensjon = Prevensjon(
                navn = code.get('Navn'), 
                id = str(uuid.uuid4()),
                definition = code.get('Beskrivelse')
            )
            
            bivirkninger = Informasjon(
                type = 'Bivirkninger',
                navn = f'BIVIRKNINGER OM {prevensjon.navn}',
                id = str(uuid.uuid4()),
                definition = code.get('Bivirkninger')
            )
            prevensjon.bivirkninger = bivirkninger.id
            
            hvordan_starte = Informasjon(
                type = 'Hvordan starte',
                navn = f'HVORDAN STARTE MED {prevensjon.navn}',
                id = str(uuid.uuid4()),
                definition = code.get('Hvordan starte')
            )
            prevensjon.hvordan_starte = hvordan_starte.id

            hvordan_slutte = Informasjon(
                type = 'Hvordan slutte',
                navn = f'HVORDAN SLUTTE MED {prevensjon.navn}',
                id = str(uuid.uuid4()),
                definition = code.get('Hvordan slutte')
            )
            prevensjon.hvordan_slutte = hvordan_slutte.id

            bruk = Informasjon(
                type = 'Bruk',
                navn = f'HVORDAN BRUKE {prevensjon.navn}',
                id = str(uuid.uuid4()),
                definition = code.get('Brukes')
            )
            prevensjon.bruk = bruk.id

            koster = Informasjon(
                type = 'Koster',
                navn = f'HVA KOSTER {prevensjon.navn}',
                id = str(uuid.uuid4()),
                definition = code.get('Koster')
            )
            prevensjon.koster = koster.id
            
            nyttig_aa_vite = Informasjon(
                type = 'Nyttig å vite',
                navn = f'NYTTIG Å VITE OM {prevensjon.navn}',
                id = str(uuid.uuid4()),
                definition = code.get('Nyttig å vite'),
                om = prevensjon.id
            )
            prevensjon.nyttig_aa_vite = nyttig_aa_vite.id

            create_node_from_Prevensjon(prevensjon)
            create_node_from_Informasjon(bivirkninger)
            create_node_from_Informasjon(hvordan_starte)
            create_node_from_Informasjon(hvordan_slutte)
            create_node_from_Informasjon(bruk)
            create_node_from_Informasjon(koster)
            create_node_from_Informasjon(nyttig_aa_vite)
            
        with driver.session() as session:
            print('Edge creation step 1')
            session.run("MATCH (i:Informasjon),(p:Prevensjon) WHERE i.ID in p.bivirkninger MERGE (i)<-[r:Har_bivirkninger]-(p)")
            session.run("MATCH (i:Informasjon),(p:Prevensjon) WHERE i.ID in p.hvordan_starte MERGE (i)<-[r:Hvordan_starte]-(p)")
            session.run("MATCH (i:Informasjon),(p:Prevensjon) WHERE i.ID in p.hvordan_slutte MERGE (i)<-[r:Hvordan_slutte]-(p)")
            session.run("MATCH (i:Informasjon),(p:Prevensjon) WHERE i.ID in p.bruk MERGE (i)<-[r:Brukes]-(p)")
            session.run("MATCH (i:Informasjon),(p:Prevensjon) WHERE i.ID in p.koster MERGE (i)<-[r:Koster]-(p)")
            session.run("MATCH (i:Informasjon),(p:Prevensjon) WHERE i.ID in p.nyttig_aa_vite MERGE (i)<-[r:Nyttig_å_vite]-(p)")
            print('Success!')




    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")