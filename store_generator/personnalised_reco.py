from langchain.vectorstores.neo4j_vector import Neo4jVector
from langchain.graphs import Neo4jGraph

from database.neo4jConnection_utils import get_credential

def kg_personalized_search_gen(customer_id, credentials, embedding_model):
    return Neo4jVector.from_existing_index(
        embedding=embedding_model,
        url=credentials['NEO4J_URI'],
        username=credentials['NEO4J_USERNAME'],
        password=credentials['NEO4J_PASSWORD'],
        index_name='product_text_embeddings',
        retrieval_query=f"""
        WITH node AS product, score AS searchScore

        OPTIONAL MATCH(product)<-[:VARIANT_OF]-(:Article)<-[:PURCHASED]-(:Customer)
        -[:PURCHASED]->(a:Article)<-[:PURCHASED]-(:Customer {{customerId: '{customer_id}'}})
        WITH count(a) AS purchaseScore, product, searchScore
        RETURN product.text + '\nurl: ' + 'https://representative-domain/product/' + product.productCode  AS text,
            (1.0+purchaseScore)*searchScore AS score,
            {{source: 'https://representative-domain/product/' + product.productCode,
                purchaseScore: purchaseScore,
                searchScore: searchScore}} AS metadata
        ORDER BY purchaseScore DESC, searchScore DESC LIMIT 5
    """
    )

def kg_recommendations_app_dict(_dict):
    return _kg_recommendations_app(_dict['customer_id'], _dict['credentials'], _dict['k'])

# Use the same personalized recommendations as above but with a smaller limit
def _kg_recommendations_app(customer_id, credentials, k=30):
    kg = Neo4jGraph(url=credentials['NEO4J_URI'], 
                    username=credentials['NEO4J_USERNAME'], 
                    password=credentials['NEO4J_PASSWORD'])

    res = kg.query("""
    MATCH(:Customer {customerId:$customerId})-[:PURCHASED]->(:Article)
    -[r:CUSTOMERS_ALSO_LIKE]->(:Article)-[:VARIANT_OF]->(product)
    RETURN product.text + '\nurl: ' + 'https://representative-domain/product/' + product.productCode  AS text,
        sum(r.score) AS recommenderScore
    ORDER BY recommenderScore DESC LIMIT $k
    """, params={'customerId': customer_id, 'k':k})

    return "\n\n".join([d['text'] + '\nscore:' + str(d['recommenderScore']) for d in res])