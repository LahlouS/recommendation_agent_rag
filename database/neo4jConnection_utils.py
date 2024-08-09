from dotenv import load_dotenv, find_dotenv
import os

from graphdatascience import GraphDataScience


def get_credential():
    env_path = find_dotenv()
    assert env_path != ''
    load_dotenv(env_path, override=True)

    # Neo4j
    NEO4J_URI = os.getenv('NEO4J_URI')
    NEO4J_USERNAME = os.getenv('NEO4J_USERNAME')
    NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD')
    AURA_DS = eval(os.getenv('AURA_DS'))
    LLM = os.getenv('LLM')
    OPENAI_KEY = None
    
    if 'gpt' in LLM:
        OPENAI_KEY = os.getenv('OPEN_API_KEY')
        assert OPENAI_KEY is not None, f"OpenAi key is missing but trying to reach [{LLM}]"
        os.environ['OPENAI_API_KEY'] = OPENAI_KEY
        print('LOG: setting OPENAI_KEY to os environment level')
    
    credential_dict = {
        'NEO4J_URI': NEO4J_URI,
        'NEO4J_USERNAME': NEO4J_USERNAME,
        'NEO4J_PASSWORD': NEO4J_PASSWORD,
        'AURA_DS': AURA_DS,
        'LLM': LLM,
        'OPENAI_KEY': OPENAI_KEY
    }
    
    return credential_dict

    


# CONNECTING TO THE SANDBOX INSTANCE
def db_connection(credentials):
    '''
    this function take the credential needed to establish connection to the DB/sandbox instance
    this function return the client object
    '''
    NEO4J_URI = credentials["NEO4J_URI"]
    NEO4J_USERNAME = credentials["NEO4J_USERNAME"]
    NEO4J_PASSWORD = credentials["NEO4J_PASSWORD"]
    AURA_DS = credentials["AURA_DS"]

    gds = GraphDataScience(
        NEO4J_URI,
        auth=(NEO4J_USERNAME, NEO4J_PASSWORD),
        aura_ds=AURA_DS)

    gds.set_database("neo4j")

    test = gds.debug.sysInfo()

    print('LOG connection to DB:')
    print(test)
    print('--------------> connection to db is OK')
    
    return gds

