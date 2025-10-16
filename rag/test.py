import os
import time
import re
import torch
from dotenv import load_dotenv
from huggingface_hub import login
from langchain.vectorstores import FAISS
from model_load import load_embedding_model
from sentence_transformers import CrossEncoder
from chain import generate_chain
from retrieval import retrieval
from agent import generate_agent

load_dotenv()
main_db_path = os.path.join(os.path.dirname(os.getcwd()), 'vector_db/car_vector_store')
sub_db_path = os.path.join(os.path.dirname(os.getcwd()), 'vector_db/blog_kin_vector_store')

HF_TOKEN = os.getenv('HF_TOKEN')
login(token=HF_TOKEN)

store = {}

device = "cuda" if torch.cuda.is_available() else "cpu"
print(device)

embedding_model_name="dragonkue/snowflake-arctic-embed-l-v2.0-ko"
# model_name = 'qwen2.5:7b'
model_name = 'qwen3:8b'
# model_name = "Qwen/Qwen3-8B"
# model_name = "Qwen/Qwen2.5-7B"
# model_name = "unsloth/Qwen2.5-7B-bnb-4bit"
# model_name = "google/gemma-3-4b-it"

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

print("자동차 전문가 챗봇에 오신 것을 환영합니다! 종료하려면 'exit'를 입력하세요.\n")

while True:
    query = input("질문: ") # 사용자 질문 입력
    if query.lower() in ["exit", "quit"]:
        print("챗봇을 종료합니다.")
        break

    # context_text = retrieval(query, vector_store, filter)

    # response = chain.invoke({'query': query, 'content': context_text}, config={'configurable': {'session_id': 'user'}})
    response = agent.invoke({'query': query}, config={'configurable': {'session_id': 'jason'}})
    cleaned_output = re.sub(r"<think>.*?</think>", "", response['output'], flags=re.DOTALL).strip()
    print("\n답변:\n", cleaned_output)