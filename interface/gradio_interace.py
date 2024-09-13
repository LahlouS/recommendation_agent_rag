import gradio as gr
from store_generator.prompt_chain import chain_gen
from langchain_community.llms import Ollama
from langchain_community.embeddings.ollama import OllamaEmbeddings

class ModelInterface():
    def __init__(self, db_credentials, model_temperature=0.2):
        self.chain_cach = dict()
        self.creds = db_credentials
        self.llm_name = db_credentials['LLM']
        
        self.llm_instance = Ollama(model=self.llm_name, temperature=0.2)
        self.embedding_model = OllamaEmbeddings(model=self.llm_name, base_url='http://localhost:11434')

    def get_chain(self, customer_id, llm_instance, credentials, embedding_model, k=5):
        if customer_id in self.chain_cach:
            return self.chain_cach[customer_id]
        gen = chain_gen(customer_id, llm_instance, credentials, embedding_model, k)
        self.chain_cach[customer_id] = gen
        return gen

    def message_generator(self, *x):
        chain = self.get_chain(x[0], self.llm_instance, self.creds, self.embedding_model)
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

