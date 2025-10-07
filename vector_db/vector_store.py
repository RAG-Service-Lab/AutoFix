import torch, datetime
import os, json, re, unicodedata, glob
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_community.vectorstores.faiss import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

# 텍스트 정리 
def clean_string(s: str) -> str:
    if not s:
        return ""
    # 유니코드 정규화 (호환 문자 통합)
    s = unicodedata.normalize("NFKC", str(s))
    # 알파벳, 한글, 숫자, 공백만 남기기
    s = re.sub(r"[^0-9a-zA-Z가-힣\s]+", " ", s)
    s = re.sub(r"\s+", " ", s)   # 여러 공백 → 하나의 공백
    return s.strip()             # 앞뒤 공백 제거


#----- 기존설정 -----
# GPU 상태 프린트
print("PyTorch GPU 사용 가능:", torch.cuda.is_available())
print("GPU 개수:", torch.cuda.device_count())

file_path = './parsed_data.json'
blog_file_path = 'document/cleaned_blog_data.json'
kin_file_path = 'document/cleaned_kin_data.json'
db_path = "./kin_vector_store"

# 분할
splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=50
)

# 임베딩 모델 정의 
embedding_model = HuggingFaceEmbeddings(model_name="dragonkue/snowflake-arctic-embed-l-v2.0-ko", model_kwargs={'device':'cuda'}, encode_kwargs={'normalize_embeddings':True})
documents = [] 

with open(kin_file_path, 'r', encoding='utf-8-sig') as f:
    data = json.load(f) # 리스트 안에 딕셔너리들
total_len = len(data)

for idx, content in enumerate(data):              
    print(f'현재 {idx} 번째 처리중~~~~~', datetime.datetime.now())

    if content :
        if content['type'] == '블로그' :
            splits = splitter.split_text(content['content'])
            for split in splits:
                document = Document(   # 문서 정의
                    page_content=split,
                    metadata={
                        "title": content['title'],
                        "type":  content['type'],
                        "link":  content['link'],
                        "car_type":  content['car_type'],
                        "engine_type": content['engine_type'],
                    }
                )
                documents.append(document)

        # 지식인
        elif content['type'] == '지식인' : 
            contents = f"{content['title']} 해당 질문에 대한 답변은 다음과 같습니다. {content['content']}"
            splits = splitter.split_text(contents)

            for split in splits:
                document = Document(   # 문서 정의
                    page_content=split,
                    metadata={
                        "title": content['title'],
                        "type":  content['type'],
                        "link":  content['link'],
                        "car_type":  content['car_type'],
                        "engine_type": content['engine_type'],
                    }
                )
                documents.append(document)

        elif content['type'] in ['hyundai','kia']:

            content['content'] = clean_string(content['content'])
            content['title'] = clean_string(content['title'])

            contents = content['title'] + ' ' + content['content']
            
            if contents:
                document = Document(   # 문서 정의
                    page_content=contents,
                    metadata={
                        "title": content['title'],
                        "type":  content['type'],
                        "link":  content['link'],   # 메뉴얼에 출처가 없어서 공백 반환.. None으로 해야하나?? 
                        "car_type":  content['car_type'],
                        "engine_type": content['engine_type'],
                    }
                )
                documents.append(document)    

        if idx % 1000 == 0 and idx != 0:
            print('saving vector store, current idx: ', idx)
            if os.path.exists(db_path):
                print("기존 DB 로드 중:", db_path)
                vector_store = FAISS.load_local(db_path, embedding_model, allow_dangerous_deserialization=True)
                new_store = FAISS.from_documents(documents, embedding_model)
                vector_store.merge_from(new_store)
                vector_store.save_local(db_path)
                documents = [] 
            else:
                print("새 DB 생성:", db_path)
                vector_store = FAISS.from_documents(documents, embedding_model)
                vector_store.save_local(db_path)
                documents = []

vector_store = FAISS.load_local(db_path, embedding_model, allow_dangerous_deserialization=True)
new_store = FAISS.from_documents(documents, embedding_model)
vector_store.merge_from(new_store)
vector_store.save_local(db_path)

print('vector store generation finished')