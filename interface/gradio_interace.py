import gradio as gr
from store_generator.prompt_chain import chain_gen_v2
from langchain_community.llms import Ollama
from langchain_community.embeddings.ollama import OllamaEmbeddings
from store_generator import neo_client_setup as ncs
from store_generator import cypher_augmented_query as caq


class ModelInterface():
    def __init__(self, db_credentials, model_temperature=0.2, k=5):
        self.chain_cach = dict()
        self.creds = db_credentials
        self.llm_name = db_credentials['LLM']
        
        self.llm_instance = Ollama(model=self.llm_name, temperature=model_temperature)
        self.embedding_model = OllamaEmbeddings(model=self.llm_name, base_url='http://localhost:11434')
        self.search_client_query = ncs.prompt_search_client(self.creds, self.embedding_model)
        self.reco_client_query = ncs.reco_search_client({
            'credentials': self.creds,
            'k': k
        })

    def get_chain(self, customer_id, search_client_query, reco_query):
        if customer_id in self.chain_cach:
            return self.chain_cach[customer_id]
        gen = chain_gen_v2(search_client_query, reco_query, self.llm_instance)
        self.chain_cach[customer_id] = gen
        return gen

    def message_generator(self, *x):
        customer_id = x[0]

        purshase_query = caq.purshase_score_retrieval_query.format(customer_id=customer_id)
        reco_query = caq.knn_product_query.format(customer_id=customer_id, k=5)

        self.search_client_query.retrieval_query = purshase_query
        reco_query_func = self._kg_recommendations_app(self.reco_client_query, reco_query)

        chain = self.get_chain(customer_id, self.search_client_query, reco_query_func)
        return chain['output'].invoke({'searchPrompt':x[3], 'customerName':x[2], 'timeOfYear': x[1]})

    def get_interface(self):
        customer_id = gr.Textbox(label="Customer ID")
        time_of_year = gr.Textbox(label="Time Of Year")
        search_prompt_txt = gr.Textbox(label="Customer Interests(s)")
        customer_name = gr.Textbox(label="Customer Name")
        message_result = gr.Markdown(label="Message")

        interface = gr.Interface(fn=self.message_generator,
                            inputs=[customer_id, 
                                    time_of_year, 
                                    customer_name, 
                                    search_prompt_txt],
                            outputs=message_result,
                            title="🪄 personalised email Generator 🥳")
        return interface
    
    def _kg_recommendations_app(self, kg, query):
        def query_function(x):
            print('LOGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG --> ', type(x))
            return kg.query(query)
        return query_function
