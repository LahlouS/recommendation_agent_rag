from neo4j_tools import gds_db_load
import pandas as pd

def embed_description(product_emb_df, embedding_model):
    count = 0
    embeddings = []
    for docs in gds_db_load.chunks(product_emb_df.text, n=500):
        count += len(docs)
        print(f'Embedded {count} of {product_emb_df.shape[0]}')
        embeddings.extend(embedding_model.embed_documents(docs))
    print("<<<< text embedding finalised >>>>")
    product_emb_df['textEmbedding'] = embeddings
    return product_emb_df

