from langchain.vectorstores.neo4j_vector import Neo4jVector
from langchain.graphs import Neo4jGraph

def prompt_search_client(credentials, embedding_model):
    return Neo4jVector.from_existing_index(
        embedding=embedding_model,
        url=credentials['NEO4J_URI'],
        username=credentials['NEO4J_USERNAME'],
        password=credentials['NEO4J_PASSWORD'],
        index_name='product_text_embeddings',
    )

def reco_search_client(_dict):
    return _kg_recommendations_app(_dict['credentials'], _dict['k'])

# Use the same personalized recommendations as above but with a smaller limit
def _kg_recommendations_app(credentials, k=5):
    return Neo4jGraph(url=credentials['NEO4J_URI'], 
                    username=credentials['NEO4J_USERNAME'], 
                    password=credentials['NEO4J_PASSWORD'])
    # return "\n\n".join([d['text'] + '\nscore:' + str(d['recommenderScore']) for d in res])