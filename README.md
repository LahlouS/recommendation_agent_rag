# recommendation_agent_rag
A graph RAG recommendation agent on H&amp;M kaggle dataset
From a workshop presented by the wonderful team of Neo4j

data preprocessing: h&m dataset -> neo4j graph database:
[link to the graph pattern image]

recomendation algorythm: two query that produce product ranking:
- cosine similarity based on product description
- knn scores of node proximities based on graph projection of CO-PURCHASED items
[link to the pattern of the projected graph for co_purshased]

### Stack:
- database: neo4j
- data prep: pandas
- LLM: llama3.1:8b (But you can also put you GPT API key if you have one, see database/README to configure your env)
- pipe and embeddings: Langchain
- Gradio for interface



