import pandas as pd
from neo4j_tools import gds_db_load

from database.neo4jConnection_utils import db_connection, get_credential

department_df = pd.read_csv('./dataset/department.csv')
product_df = pd.read_csv('./dataset/product.csv')
article_df = pd.read_csv('./dataset/article.csv')
customer_df = pd.read_csv('./dataset/customer.csv')
transaction_df = pd.read_csv('./dataset/transaction.csv')

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
    