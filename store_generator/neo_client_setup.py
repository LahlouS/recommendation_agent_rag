from langchain.vectorstores.neo4j_vector import Neo4jVector
from langchain.graphs import Neo4jGraph

def set_vector_search(credentials, embedding_model):
    return Neo4jVector.from_existing_index(
        embedding=embedding_model,
        url=credentials['NEO4J_URI'],
        username=credentials['NEO4J_USERNAME'],
        password=credentials['NEO4J_PASSWORD'],
        index_name='product_text_embeddings',
    )

def set_graph_search(credentials):
    return Neo4jGraph(url=credentials['NEO4J_URI'],
                    username=credentials['NEO4J_USERNAME'],
                    password=credentials['NEO4J_PASSWORD'])
    # return "\n\n".join([d['text'] + '\nscore:' + str(d['recommenderScore']) for d in res])
