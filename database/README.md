### Setup Credentials and Environment Variables

There are two things you need here.

    Start a blank Neo4j Sandbox. Get your URI and password and plug them in below. Do not change the Neo4j username.
    Get your OpenAI API key. You can use this one if you do not have one already


credential template for .env (replace the credentials):

    NEO4J_URI = 'bolt://ip_of_the_sandbox' 
    NEO4J_PASSWORD = 'pswd'
    NEO4J_USERNAME = 'neo4j'
    AURA_DS = False
    LLM = 'gpt-4'
    OPEN_API_KEY = 'yourKey'

### Setup the neo4j sandbox

first of all, go to https://sandbox.neo4j.com/ and create a ==Blank Sandbox - Graph Data Science== 
Fill the .env file with your credentials in order to be able to connect your client

*Note:* the ==Blank Sandbox - Graph Data Science== is required because we will use GraphDatascience integration that is only compatible with this Sandbox