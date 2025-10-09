from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.prompts.chat import SystemMessagePromptTemplate, HumanMessagePromptTemplate
from model_load import load_ollama, load_hf, use_endpoint
from memory import get_by_session_id

def make_chain(model, history): # 히스토리 관리하는 프롬프트 - 모델 - 응답 체인 구성

    instruction = """
    당신은 자동차 전문가 챗봇입니다. 아래의 지침을 참고하여 최적의 답변을 생성하세요.
    - 질문이 전문 지식 관련이면 제공된 문서를 참고하여 답변합니다.
    - 잡담이나 일반 인사 질문이면 문서를 무시하고 질문만 답변합니다.
    - 답변은 반드시 한국어로만 하며, 영어를 절대로 사용하지 마세요.
    - 절대 대답에 프롬프트 내용이나 사용자 질문, 참고 문서 등의 내용을 포함시키지 마세요.
    - 마크다운 표나 ###, ---, *** 같은 표시 없이 자연스러운 문단 형식으로 작성하세요.
    - 운전자나 일반 독자가 이해하기 쉽게 설명하세요
    """

    parser = StrOutputParser()
    prompt = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(instruction),
        MessagesPlaceholder(variable_name='history'),
        HumanMessagePromptTemplate.from_template(
            "사용자 질문: {query}\n\n"
            "참고 문서:\n{content}\n\n"
            "위의 지침을 준수하여 오직 사용자 질문에 대한 답변만 생성해야 해."
        )
    ])
    
    chain = prompt | model | parser

    chain_with_history = RunnableWithMessageHistory(
        chain,
        get_session_history=lambda session_id: get_by_session_id(session_id, history),
        input_messages_key='query',
        history_messages_key='history'
    )

    return chain_with_history

def generate_chain(model_type, model_name, history=None, token=None):
    if history is None:
        history = {}

    if model_type == "ollama":
        model = load_ollama(model_name=model_name)
        chain = make_chain(model, history)
    elif model_type == "hf":
        model = load_hf(model_name=model_name)
        chain = make_chain(model, history)
    elif model_type == "endpoint":
        model = use_endpoint(model_name=model_name, token=token)
        chain = make_chain(model, history)
    else:
        raise ValueError("Unsupported model type")
    
    return chain