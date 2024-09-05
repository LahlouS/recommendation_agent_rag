
from neo4j_tools import gds_db_load

def push_embeddings(gds_client, productcode_embedding_dict):

    '''
        this function is used to push the embeddings of the product description
        the productcode_embedding_dict arg must have the following format:
        [{
         productCode: xxxxx
         textEmbedding: 4562853011...   
        }, ... ]
    '''

    records = productcode_embedding_dict
    total = len(records)
    print(f'staging {total:,} records')
    cumulative_count = 0
    for recs in gds_db_load.chunks(records, n=100):
        res = gds_client.run_cypher('''
        UNWIND $recs AS rec
        MATCH(n:Product {productCode: rec.productCode})
        WHERE NOT exists(n.textEmbedding)
        CALL db.create.setNodeVectorProperty(n, "textEmbedding", rec.textEmbedding)
        RETURN count(n) AS propertySetCount
        ''', params={'recs': recs})
        cumulative_count += res.iloc[0, 0]
        print(f'Set {cumulative_count:,} of {total:,} text embeddings')


def create_vector_index(gds_client, embedding_dimension=4096):
    
    '''
    be careful the embedding dimension must match the embedding dimension of the model you 
    used for generating the embeddings
    '''

    gds_client.run_cypher('''
    CREATE VECTOR INDEX product_text_embeddings IF NOT EXISTS FOR (n:Product) ON (n.textEmbedding)
    OPTIONS {indexConfig: {
    `vector.dimensions`: toInteger($dim),
    `vector.similarity_function`: 'cosine'
    }}''', params={'dim': embedding_dimension})

    gds_client.run_cypher('CALL db.awaitIndex("product_text_embeddings", 300)')