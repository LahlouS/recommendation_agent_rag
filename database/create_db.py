import pandas as pd
from neo4j_tools import gds_db_load, gds_utils

from database.neo4jConnection_utils import db_connection, get_credential

department_df = pd.DataFrame()
product_df = pd.DataFrame()
article_df = pd.DataFrame()
customer_df = pd.DataFrame()
transaction_df = pd.DataFrame()

def load_csv(base_path):
    department_df = pd.read_csv(base_path + '/department.csv')
    product_df = pd.read_csv(base_path + '/product.csv')
    article_df = pd.read_csv(base_path + '/article.csv')
    customer_df = pd.read_csv(base_path + '/customer.csv')
    transaction_df = pd.read_csv(base_path + '/transaction.csv')
    

def read_csv(path):
    return pd.read_csv(path)

def create_constraints(gds_client):
    gds_client.run_cypher('CREATE CONSTRAINT unique_department_no IF NOT EXISTS FOR (n:Department) REQUIRE n.departmentNo IS UNIQUE')
    gds_client.run_cypher('CREATE CONSTRAINT unique_product_code IF NOT EXISTS FOR (n:Product) REQUIRE n.productCode IS UNIQUE')
    gds_client.run_cypher('CREATE CONSTRAINT unique_article_id IF NOT EXISTS FOR (n:Article) REQUIRE n.articleId IS UNIQUE')
    gds_client.run_cypher('CREATE CONSTRAINT unique_customer_id IF NOT EXISTS FOR (n:Customer) REQUIRE n.customerId IS UNIQUE')
    print('LOG: constraints are created')

def create_db(gds_client):
    # load nodes
    gds_db_load.load_nodes(gds_client, department_df, 'departmentNo', 'Department')
    gds_db_load.load_nodes(gds_client, article_df.drop(columns=['productCode', 'departmentNo']), 'articleId', 'Article')
    gds_db_load.load_nodes(gds_client, product_df, 'productCode', 'Product')
    gds_db_load.load_nodes(gds_client, customer_df, 'customerId', 'Customer')
    print('LOG: nodes are loaded')

    # load relationships
    gds_db_load.load_rels(gds_client,   article_df[['articleId', 'departmentNo']], 
                                        source_target_labels=('Article', 'Department'),
                                        source_node_key='articleId', target_node_key='departmentNo',
                                        rel_type='FROM_DEPARTMENT')
    
    gds_db_load.load_rels(gds_client,   article_df[['articleId', 'productCode']], 
                                        source_target_labels=('Article', 'Product'),
                                        source_node_key='articleId',target_node_key='productCode',
                                        rel_type='VARIANT_OF')
    
    # SEE HOW THE TRANSACTION BECOME PURE RELATIONSHIPS IN GRAPH DB
    gds_db_load.load_rels(gds_client,   transaction_df, 
                                        source_target_labels=('Customer', 'Article'),
                                        source_node_key='customerId', target_node_key='articleId', rel_key='txId', # rel_key specifies the unique identifiant
                                        rel_type='PURCHASED')
    print('LOG: relations are loaded')
    
    gds_client.run_cypher('''
        MATCH (:Customer)-[r:PURCHASED]->()
        SET r.tDat = date(r.tDat)
        ''')
    
    gds_client.run_cypher("""
        MATCH(p:Product)
        SET p.text = '##Product\n' +
            'Name: ' + p.prodName + '\n' +
            'Type: ' + p.productTypeName + '\n' +
            'Group: ' + p.productGroupName + '\n' +
            'Garment Type: ' + p.garmentGroupName + '\n' +
            'Description: ' + p.detailDesc
        RETURN count(p) AS propertySetCount
        """)
    print('LOG: product.text property is set')

def create_node_embedding(gds_client):

    #clear past GDS analysis in the case of re-running
    gds_utils.clear_all_gds_graphs(gds_client)
    gds_utils.delete_relationships('CUSTOMERS_ALSO_LIKE', gds_client, src_node_label='Article')


    # graph projection - project co-purchase graph into analytics workspace
    gds_client.run_cypher('''
    MATCH (a1:Article)<-[:PURCHASED]-(:Customer)-[:PURCHASED]->(a2:Article)
    WITH gds.graph.project("proj", a1, a2,
        {sourceNodeLabels: labels(a1),
        targetNodeLabels: labels(a2),
        relationshipType: "COPURCHASE"}) AS g
    RETURN g.graphName
    ''')
    g = gds_client.graph.get("proj")

    # create FastRP node embeddings
    gds_client.fastRP.mutate(g, mutateProperty='embedding', embeddingDimension=128, randomSeed=7474, concurrency=4, iterationWeights=[0.0, 1.0, 1.0])

    # draw KNN
    knn_stats = gds_client.knn.write(g, nodeProperties=['embedding'], nodeLabels=['Article'],
                    writeRelationshipType='CUSTOMERS_ALSO_LIKE', writeProperty='score',
                    sampleRate=1.0, initialSampler='randomWalk', concurrency=1, similarityCutoff=0.75, randomSeed=7474)

    # write embeddings back to database to introspect later
    gds_client.graph.writeNodeProperties(g, ['embedding'], ['Article'])

    # clear graph projection once done
    g.drop()
    return knn_stats