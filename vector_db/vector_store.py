import torch, datetime
import os, json, re, unicodedata, glob
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_community.vectorstores.faiss import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

#----- 기존설정 -----
# GPU 상태 프린트
print("PyTorch GPU 사용 가능:", torch.cuda.is_available())
print("GPU 개수:", torch.cuda.device_count())
# print("현재 GPU 인덱스:", torch.cuda.current_device())
# print("GPU 이름:", torch.cuda.get_device_name(torch.cuda.current_device()))

# 블로그 파일 path 
#file_paths = ['./naver_blog_results_tmp.json', './naver_in_results_tmp.json', './parsed_data.json']
file_paths = ['./parsed_data.json']
base_db_path = './faiss_db'

# 분할
splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=50
)

# 임베딩 모델 정의 
embedding_model = HuggingFaceEmbeddings(model_name="dragonkue/snowflake-arctic-embed-l-v2.0-ko", model_kwargs={'device':'cpu'}, encode_kwargs={'normalize_embeddings':True})
# embedding_model = HuggingFaceEmbeddings(model_name="Alibaba-NLP/gte-Qwen2-1.5B-instruct", model_kwargs={'device':'cuda'}, encode_kwargs={'normalize_embeddings':True})

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


# 파일 불러오기 
for file_path in file_paths :
    with open(file_path, 'r', encoding='utf-8-sig') as f:
        data = json.load(f) # 리스트 안에 딕셔너리들
    total_len = len(data)
    mini_batch = total_len // 4
    print('!!!!!!!', type(data))
    print('!!!!!!!', data[:3])

    # for val in data :
    # 50개 단위로 루프 코드
    #for start_idx in range(0, len(data), 50):
        #batch = data[start_idx:start_idx+50]
        #documents = []

    for i in range(0, mini_batch*1): # 첫세트 돌릴때의 경우
        val = data[i]
        documents = []               
        # for keys, vals in item.items():
        #     for val in vals :
        print(f'현재 {i} 번째 처리중~~~~~', datetime.datetime.now())

        # for val in vals :
        if val :
                # 일괄 전처리 
                val['content'] = clean_string(val['content'])
                val['title'] = clean_string(val['title'])

                # 블로그
                if val['type'] == '블로그' :
                    splits = splitter.split_text(val['content'])     # 리스트 안에 쪼개진 문자열들 - 블로그만 쪼개기 

                    for split in splits:
                        document = Document(   # 문서 정의
                            page_content=split,
                            metadata={
                                "title": val['title'],
                                "type":  val['type'],
                                "url":  val['출처'],
                                "car_type":  val['차종'],
                                "engine_type": val['엔진'],
                            }
                        )
                        documents.append(document)
                        #print('🎈🎈🎈블로그:', document)

                # 지식인
                elif val['type'] == '지식인' :
                    if type(val['content']) == list :
                        answers = {clean_string(answer.get('text','')) for i, answer in enumerate(val['content'])}
                        contents = val['title'] + ' ' + answers
                    else : 
                        contents = val['title'] + ' ' + val['content']
                    
                    splits = splitter.split_text(contents)

                    for split in splits:
                        document = Document(   # 문서 정의
                            page_content=split,
                            metadata={
                                "title": val['title'],
                                "type":  val['type'],
                                "url":  val['출처'],
                                "car_type":  val['차종'],
                                "engine_type": val['엔진'],
                            }
                        )
                        documents.append(document)
                        #print('🎈🎈🎈지식인:', document)

                elif val['type'] in ['hyundai','kia']:

                    contents = val['title'] + ' ' + val['content']
                    
                    if contents:
                        document = Document(   # 문서 정의
                            page_content=contents,
                            metadata={
                                "title": val['title'],
                                "type":  val['type'],
                                "url":  val.get('출처', ''),   # 메뉴얼에 출처가 없어서 공백 반환.. None으로 해야하나?? 
                                "car_type":  val['차종'],
                                "engine_type": val['엔진'],
                            }
                        )
                        documents.append(document)    
                        #print('🎈🎈🎈메뉴얼:', document)


                file_name = os.path.splitext(os.path.basename(file_path))[0]
                db_path = os.path.join(base_db_path, file_name)
#
                #if documents :
                #    vector_store = FAISS.from_documents(documents, embedding_model)  # 벡터화 
                #    vector_store.save_local(db_path)
                #    print(f"현재 처리 중: {file_path} → DB 저장 경로: {db_path}")
                #else :
                #     print(f'문서없음: {file_path}')
#
                #print(f'{file_name} 파일의 {1}번째 ~ {mini_batch+1}번째 완료')


                # 벡터스토어 로드 후 업데이트
                if os.path.exists(db_path):
                    print("기존 DB 로드 중:", db_path)
                    vector_store = FAISS.load_local(db_path, embedding_model, allow_dangerous_deserialization=True)
                    new_store = FAISS.from_documents(documents, embedding_model)
                    vector_store.merge_from(new_store)  # 기존 벡터스토어에 새 데이터 합치기
                else:
                    print("새 DB 생성:", db_path)
                    vector_store = FAISS.from_documents(documents, embedding_model)

                # 저장
                vector_store.save_local(db_path)
                print(f"{file_name} 파일의 {1}번째 ~ {mini_batch*1}번째 벡터화 완료 → DB 저장 경로: {db_path}")