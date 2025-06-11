from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_deepseek import ChatDeepSeek
from langchain_openai.chat_models.base import BaseChatOpenAI
from langchain_together import Together
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq



import os
from dotenv import load_dotenv

load_dotenv()

prompt = '''You are an assistant for question-answering tasks. Use only the following pieces of retrieved context and history to
answer the question. If you don't know the answer, just say that you don't know.
.\nQuestion: {question} \nContext: {context} \nConversation History:\n{history} \nAnswer:
'''

generate_answer_prompt = PromptTemplate(
        input_variables=["context", "question", "history"], template=prompt)

#llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0)
#llm = ChatOpenAI(model_name="gpt-4", temperature=0)
"""
llm = ChatDeepSeek(
    model="deepseek-chat",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=4
)
"""
"""
llm = ChatDeepSeek(
    model="deepseek-reasoner",
    timeout=None,
    max_retries=4
)
"""

#llm = Together(together_api_key=os.getenv("TOGETHER_API_KEY"), model='meta-llama/Llama-3.3-70B-Instruct-Turbo', temperature=0.2, max_tokens=1024)
#llm = Together(together_api_key=os.getenv("TOGETHER_API_KEY"), model='deepseek-ai/DeepSeek-R1', temperature=0.2, max_tokens=1024)
#llm = Together(together_api_key=os.getenv("TOGETHER_API_KEY"), model='deepseek-ai/DeepSeek-V3', temperature=0.2, max_tokens=1024)
#llm = Together(together_api_key=os.getenv("TOGETHER_API_KEY"), model='Qwen/Qwen2-VL-72B-Instruct', temperature=0.2, max_tokens=1024)
#llm = Together(together_api_key=os.getenv("TOGETHER_API_KEY"), model='mistralai/Mistral-7B-Instruct-v0.2', temperature=0.2, max_tokens=1024)

llm = ChatOpenAI(
    #model = 'deepseek/deepseek-chat:free',
    #model = 'deepseek/deepseek-chat',
    model = 'deepseek/deepseek-r1:nitro',
    #model='deepseek/deepseek-r1-distill-qwen-32b',
    #model='deepseek/deepseek-r1-distill-llama-8b',
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
    #model_kwargs={"extra_body": {"include_reasoning": True}}
)

"""
llm = ChatGroq(
    #model_name="deepseek-r1-distill-llama-70b",
    model_name="deepseek-r1-distill-qwen-32b",
    temperature=0
)
"""

#llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp")
generation_chain = generate_answer_prompt | llm | StrOutputParser()

