import os
import time
import re
import torch
from dotenv import load_dotenv
from huggingface_hub import login
from langchain.vectorstores import FAISS
from rag.model_load import load_embedding_model
from sentence_transformers import CrossEncoder
from rag.agent import generate_agent
from pydantic import BaseModel
from fastapi import FastAPI

load_dotenv()
app = FastAPI()

main_db_path = os.path.join(os.path.dirname(os.getcwd()), 'AutoFix/vector_db/car_vector_store')
sub_db_path = os.path.join(os.path.dirname(os.getcwd()), 'AutoFix/vector_db/blog_kin_vector_store')

HF_TOKEN = os.getenv('HF_TOKEN')
login(token=HF_TOKEN)

store = {}

device = "cuda" if torch.cuda.is_available() else "cpu"
print(device)

embedding_model_name="dragonkue/snowflake-arctic-embed-l-v2.0-ko"
model_name = 'qwen3:8b'

embedding_model = load_embedding_model(embedding_model_name)
main_vector_store = FAISS.load_local(main_db_path, embedding_model, allow_dangerous_deserialization=True) # 벡터 DB 로드
sub_vector_store = FAISS.load_local(sub_db_path, embedding_model, allow_dangerous_deserialization=True) # 벡터 DB 로드
reranker_name = "Dongjin-kr/ko-reranker"
reranker = CrossEncoder(reranker_name, device='cuda')

filter = {"car_type": "K7(YG)", "engine_type": "L3.0LPI"}

filtered_docs = [
    doc for doc in main_vector_store.docstore._dict.values()
    if all(doc.metadata.get(key) == value for key, value in filter.items())
]

if filtered_docs:
    custom_store = FAISS.from_documents(filtered_docs, main_vector_store.embedding_function)
else:
    custom_store = None

# chain = generate_chain(model_type="ollama", model_name=model_name, history=store, token=HF_TOKEN)
agent = generate_agent(model_type="ollama", model_name=model_name, main_vector_store=custom_store, sub_vector_store=sub_vector_store, reranker=reranker, history=store, token=HF_TOKEN)

class QueryRequest(BaseModel):
    query: str
    session_id: str = "default"

class QueryResponse(BaseModel):
    output: str

# --------------------------
# LLM 호출 endpoint
# --------------------------
@app.post("/query", response_model=QueryResponse)
async def query_llm(request: QueryRequest):
    response = agent.invoke({'query': request.query}, config={'configurable': {'session_id': request.session_id}})
    cleaned_output = re.sub(r"<think>.*?</think>", "", response['output'], flags=re.DOTALL).strip()
    return {"output": cleaned_output}