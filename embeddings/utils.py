import pandas as pd



def get_full_text(df):
    '''
        This function must take the product dataframe from the dataset/product.csv
        it return a new df consisting of productCode associated with its full description
        i.e all the text available for the product (see _create_doc())
    '''

    df = df[['productCode', 'prodName', 'productTypeName', 'productGroupName', 'garmentGroupName', 'detailDesc']]
    df = df[df.detailDesc.notnull()] # TODO add a fancier way to avoid dropping the complete row (see first the proportion of null)

    df['text'] = df.apply(_create_doc, axis=1)
    df = df.drop(columns=['prodName', 'productTypeName', 'productGroupName', 'garmentGroupName', 'detailDesc']) # to keep only productCode and text
    return df

def _create_doc(row):
    return f'''
##Product
Name: {row.prodName}
Type: {row.productTypeName}
Group: {row.productGroupName}
Garment Type: {row.garmentGroupName}
Description: {row.detailDesc}
'''