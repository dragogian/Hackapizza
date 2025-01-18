import os
from getpass import getpass

from dotenv import load_dotenv
from langchain_ibm import ChatWatsonx
from langchain_openai import ChatOpenAI

load_dotenv()
watsonx_api_key = getpass()
os.environ["WATSONX_APIKEY"] = watsonx_api_key

# os.environ["WATSONX_URL"] = "your service instance url"
# os.environ["WATSONX_TOKEN"] = "your token for accessing the CPD cluster"
# os.environ["WATSONX_PASSWORD"] = "your password for accessing the CPD cluster"
# os.environ["WATSONX_USERNAME"] = "your username for accessing the CPD cluster"
# os.environ["WATSONX_INSTANCE_ID"] = "your instance_id for accessing the CPD cluster"

llm = ChatOpenAI("gpt-4o", temperature=0)

# parameters = {
#     "temperature": 0,
#     "max_tokens": 20000,
# }
#
# chat = ChatWatsonx(
#     model_id="ibm/granite-34b-code-instruct",
#     url="https://us-south.ml.cloud.ibm.com",
#     project_id="PASTE YOUR PROJECT_ID HERE",
#     params=parameters,
# )

# CLOUD PAK VERSION
# chat = ChatWatsonx(
#     model_id="ibm/granite-34b-code-instruct",
#     url="PASTE YOUR URL HERE",
#     username="PASTE YOUR USERNAME HERE",
#     password="PASTE YOUR PASSWORD HERE",
#     instance_id="openshift",
#     version="4.8",
#     project_id="PASTE YOUR PROJECT_ID HERE",
#     params=parameters,
# )

# DEPLOYMENT_ID VERSION
# chat = ChatWatsonx(
#     deployment_id="PASTE YOUR DEPLOYMENT_ID HERE",
#     url="https://us-south.ml.cloud.ibm.com",
#     project_id="PASTE YOUR PROJECT_ID HERE",
#     params=parameters,
# )