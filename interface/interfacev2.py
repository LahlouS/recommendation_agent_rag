import gradio as gr
from store_generator.prompt_chain import prompt as chatPromptTemplate
from store_generator.prompt_chain import format_docs, format_final_prompt

from langchain_community.llms import Ollama
from langchain_community.embeddings.ollama import OllamaEmbeddings
from langchain.prompts import SystemMessagePromptTemplate, HumanMessagePromptTemplate, ChatPromptTemplate
from langchain.schema import StrOutputParser
from langchain.schema.runnable import RunnableLambda

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

		self.db_vector_search = ncs.set_vector_search(self.creds, self.embedding_model)
		self.db_graph_search = ncs.set_graph_search(self.creds)
        self.log_path = './result/'

	def get_interface(self):
        customer_id = gr.Textbox(label="Customer ID")
        time_of_year = gr.Textbox(label="Time Of Year")
        search_prompt_txt = gr.Textbox(label="Customer Interests(s)")
        customer_name = gr.Textbox(label="Customer Name")
        run_name = gr.Textbox(label="Log filename"
                              )
        message_result = gr.Markdown(label="Message")
        generated_prompt = gr.Markdown(label="Generated prompt")
        exec_time = gr.Markdown(label="Execution Time")

        interface = gr.Interface(fn=self.message_generator,
                            inputs=[customer_id,
                                    time_of_year,
                                    customer_name,
                                    search_prompt_txt,
                                    run_name],
                            outputs=[message_result, generated_prompt, exec_time],
                            title="🪄 personalised email Generator 🥳")
        return interface

	def message_generator(self, *x):
        customer_id = x[0]
        params = {'searchPrompt':x[3], 'customerName':x[2], 'timeOfYear': x[1]}
		run_name = x[4]

        start = time.perf_counter()
		chain = self.get_chain(customer_id)
        output = chain['output'].invoke(params)
        prompt = chain['prompt'].invoke(params)
        end = time.perf_counter()
        exec_time = str(end - start)

		# TODO remove when interface will be more serious than gradio
        utils.write_to_file((self.log_path + 'prompt_' + run_name), prompt)
        utils.write_to_file((self.log_path + 'out_' + run_name), output)


        return [
                    output,
                    '\n\nINPUT PROMPT' + prompt,
                    '\n\nEXECUTION TIME' + exec_time
                ]


    def get_chain(self, customer_id):
        if customer_id in self.chain_cach:
            return self.chain_cach[customer_id]
        gen = self.chain_gen(customer_id)
        self.chain_cach[customer_id] = gen
        return gen

	def chain_gen(self, customer_id, k=5):
		populated_prompt = {
					'searchProds': (lambda x:x['searchPrompt'])| self._kg_vector_similarity_search(customer_id).as_retriever(search_kwargs={"k": k}) | format_docs,
					'recProds': (lambda x:customer_id) | RunnableLambda(self._graph_customer_also_like_search),
					'customerName': lambda x:x['customerName'],
					'timeOfYear': lambda x:x['timeOfYear'],
					"searchPrompt":  lambda x:x['searchPrompt']
					} | chatPromptTemplate

		return ({
				'output': (populated_prompt | self.llm_instance | StrOutputParser()),
				'prompt': (populated_prompt | format_final_prompt | StrOutputParser())
				})

	def _kg_vector_similarity_search(self, customer_id):
		retrieval_query=f"""
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
		self.db_vector_search.retrieval_query = retrieval_query
		return self.db_vector_search


	def _graph_customer_also_like_search(self, customer_id, k=5):

		res = self.db_graph_search.query("""
		MATCH(:Customer {customerId:$customerId})-[:PURCHASED]->(:Article)
		-[r:CUSTOMERS_ALSO_LIKE]->(:Article)-[:VARIANT_OF]->(product)
		RETURN product.text + '\nurl: ' + 'https://representative-domain/product/' + product.productCode  AS text,
			sum(r.score) AS recommenderScore
		ORDER BY recommenderScore DESC LIMIT $k
		""", params={'customerId': customer_id, 'k':k})

		return "\n\n".join([d['text'] + '\nscore:' + str(d['recommenderScore']) for d in res])

