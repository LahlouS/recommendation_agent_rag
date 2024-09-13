from langchain.prompts import SystemMessagePromptTemplate, HumanMessagePromptTemplate, ChatPromptTemplate
from langchain.schema import StrOutputParser
from langchain.schema.runnable import RunnableLambda
from store_generator.personnalised_reco import kg_personalized_search_gen, kg_recommendations_app_dict
from operator import itemgetter

general_system_template = '''
You speak as you were a personal assistant named Sally, you are a funny and sexy a talker. 
you work for a fashion, home, and beauty company called HRM.
you write an email to a customer named: {customerName} so you will start you e-mail adressing to her.
to promote and summarize relevant products for her given the current season / time of year: {timeOfYear}.
Please only mention the products listed below. Do not come up with or add any new products to the list.
Each product comes with an https `url` field. Make sure to provide that https url with descriptive name text in markdown for each product.

---

# Relevant Products:
{searchProds}

# Customer May Also Be Interested In the following
 (pick items from here that pair with the above products well for the current season / time of year: {timeOfYear}.
 prioritize those higher in the list if possible):
{recProds}

remember to write the email as Sally the personal assistant 
---

'''
general_user_template = "hello, my name is {customerName} and I'm looking for: {searchPrompt}"
messages = [
    SystemMessagePromptTemplate.from_template(general_system_template),
    HumanMessagePromptTemplate.from_template(general_user_template),
]
prompt = ChatPromptTemplate.from_messages(messages)

def format_docs(docs):
    return "\n\n".join([d.page_content for d in docs])

def format_final_prompt(x):
   return f'''=== Prompt to send to LLM ===
   {x.to_string()}
   === End Prompt ===
   '''

# LLM chain
def chain_gen(customer_id, llm_instance, credentials, embedding_model, k=5):
    
    populated_prompt = {
                'searchProds': (lambda x:x['searchPrompt'])| kg_personalized_search_gen(customer_id, credentials, embedding_model).as_retriever(search_kwargs={"k": 5}) | format_docs,
                'recProds': (lambda x:{'customer_id': customer_id, 'credentials': credentials, 'k': k}) | RunnableLambda(kg_recommendations_app_dict),
                'customerName': lambda x:x['customerName'],
                'timeOfYear': lambda x:x['timeOfYear'],
                "searchPrompt":  lambda x:x['searchPrompt']
                } | prompt
    
    return ({
            'output': (populated_prompt | llm_instance | StrOutputParser()),
            'prompt': (populated_prompt | format_final_prompt | StrOutputParser())
            })