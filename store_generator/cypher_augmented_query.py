purshase_score_retrieval_query = """
        WITH node AS product, score AS searchScore

        OPTIONAL MATCH(product)<-[:VARIANT_OF]-(:Article)<-[:PURCHASED]-(:Customer)
        -[:PURCHASED]->(a:Article)<-[:PURCHASED]-(:Customer {{customerId: '{customer_id}'}})
        WITH count(a) AS purchaseScore, product, searchScore
        RETURN product.text + '\nurl: ' + 'https://representative-domain/product/' + product.productCode + '\nscore: ' + (1.0+purchaseScore)*searchScore AS text,
            (1.0+purchaseScore)*searchScore AS score,
            {{source: 'https://representative-domain/product/' + product.productCode,
                purchaseScore: purchaseScore,
                searchScore: searchScore}} AS metadata
        ORDER BY purchaseScore DESC, searchScore DESC LIMIT 5
    """

knn_product_query = """
    MATCH(:Customer {{customerId: '{customer_id}'}})-[:PURCHASED]->(:Article)
    -[r:CUSTOMERS_ALSO_LIKE]->(:Article)-[:VARIANT_OF]->(product)
    RETURN product.text + '\nurl: ' + 'https://representative-domain/product/' + product.productCode  AS text,
        sum(r.score) AS recommenderScore
    ORDER BY recommenderScore DESC LIMIT {k}
    """