import gradio as gr
from store_generator.prompt_chain import chain_gen_v2, chain_gen
from langchain_community.llms import Ollama
from langchain_community.embeddings.ollama import OllamaEmbeddings
from store_generator import neo_client_setup as ncs
from store_generator import cypher_augmented_query as caq
import utils.utils as utils
import time

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
        self.log_path = './result/'

    def get_chain(self, customer_id, search_client_query, reco_query):
        if customer_id in self.chain_cach:
            return self.chain_cach[customer_id]
        gen = chain_gen_v2(search_client_query, reco_query, self.llm_instance)
        self.chain_cach[customer_id] = gen
        return gen

    def message_generator(self, *x):
        start = time.perf_counter()

        customer_id = x[0]

        purshase_query = caq.purshase_score_retrieval_query.format(customer_id=customer_id)
        reco_query = caq.knn_product_query.format(customer_id=customer_id, k=5)

        self.search_client_query.retrieval_query = purshase_query
        reco_query_func = self._kg_recommendations_app(self.reco_client_query, reco_query)

        chain = self.get_chain(customer_id, self.search_client_query, reco_query_func)
        params = {'searchPrompt':x[3], 'customerName':x[2], 'timeOfYear': x[1]}

        output = chain['output'].invoke(params)
        prompt = chain['prompt'].invoke(params)
        end = time.perf_counter()
        exec_time = str(end - start)


        utils.write_to_file((self.log_path + 'prompt_' + x[4]), prompt)
        utils.write_to_file((self.log_path + 'out_' + x[4]), output)


        return [
                    output,
                    prompt,
                    exec_time
                ]

    def get_interface(self, func_to_use=True):
        customer_id = gr.Textbox(label="Customer ID")
        time_of_year = gr.Textbox(label="Time Of Year")
        search_prompt_txt = gr.Textbox(label="Customer Interests(s)")
        customer_name = gr.Textbox(label="Customer Name")
        run_name = gr.Textbox(label="Log filename"
                              )
        message_result = gr.Markdown(label="Message")
        generated_prompt = gr.Markdown(label="Generated prompt")
        exec_time = gr.Markdown(label="Execution Time")

        fn = self.message_generator
        if func_to_use is False:
            fn=self.old_message_generator

        interface = gr.Interface(fn=fn,
                            inputs=[customer_id,
                                    time_of_year,
                                    customer_name,
                                    search_prompt_txt,
                                    run_name],
                            outputs=[message_result, generated_prompt, exec_time],
                            title="🪄 personalised email Generator 🥳")
        return interface


    def old_get_chain(self, customer_id):
        if customer_id in self.chain_cach:
            return self.chain_cach[customer_id]
        gen = chain_gen(customer_id, self.llm_instance, self.creds, self.embedding_model)
        self.chain_cach[customer_id] = gen
        return gen

    def old_message_generator(self, *x):
        customer_id = x[0]
        date = x[1]
        customer_name = x[2]
        search_prompt =  x[3]

        start_time = time.perf_counter()
        gen = self.old_get_chain(customer_id)
        output = gen.invoke['output']({'searchPrompt':x[3], 'customerName':x[2], 'timeOfYear': x[1]})
        prompt = gen.invoke['prompt']({'searchPrompt':x[3], 'customerName':x[2], 'timeOfYear': x[1]})
        end_time = time.perf_counter()
        exec_time = end_time - start_time

        utils.write_to_file((self.log_path + 'old_out_' + x[4]), output)
        utils.write_to_file((self.log_path + 'old_prompt_' + x[4]), prompt)

        return [output, prompt, exec_time]

    def _kg_recommendations_app(self, kg, query):
        def query_function(x):
            return kg.query(query)
        return query_function
