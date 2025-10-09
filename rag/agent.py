import os
from langchain.agents import Tool
from langchain.prompts import PromptTemplate
from langchain.agents import AgentExecutor, create_react_agent
from langchain.agents import create_tool_calling_agent
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.prompts.chat import SystemMessagePromptTemplate, HumanMessagePromptTemplate
from model_load import load_ollama, load_hf, use_endpoint
from memory import get_by_session_id
from retrieval import retrieval

def fallback_chat(query, model):
    instruction = "사용자의 질문에 친절하고 자연스럽게 대화합니다."
    response = model.invoke(f"{instruction}\n\n사용자 질문: {query}")

    return response


def build_agent(model, vector_store, default_filter, history):

    # instruction = """
    # 당신은 자동차 전문가 챗봇입니다. 질문에 답하기 위해 아래의 지시사항을 따르세요.
    # 당신은 다음의 도구들을 사용할 수 있습니다
    # - 사용자 질문이 자동차 부품의 정의나 설명을 묻는 질문이면 web_search 도구 사용.
    # - 사용자 질문이 자동차 고장, 문제 해결, 원인 분석 질문이면 document_retrieval 도구 사용.
    # - 사용자 질문이 잡담이나 인사, 일상 대화면 tool을 사용하지 않고 직접 답변.
    # 답변은 반드시 한국어로 작성하며, 전문 용어는 쉽게 풀어쓰세요.
    # """

    # prompt = ChatPromptTemplate.from_messages([
    #     SystemMessagePromptTemplate.from_template(instruction),
    #     MessagesPlaceholder(variable_name='history'),
    #     HumanMessagePromptTemplate.from_template("사용자 질문: {query}\n\n"),
    #     MessagesPlaceholder(variable_name='agent_scratchpad')
    # ])

    prompt = PromptTemplate.from_template ('''Answer the following questions as best you can. You have access to the following tools:

    {tools}

    Previous conversation history:
    {history}

    Use the following format:

    Question: the input question you must answer
    Thought: you should always think about what to do
    Action: the action to take, should be one of [{tool_names}].
    Note: If this is a general chit-chat, greeting, or simple question, skip Action and respond directly.
    Action Input: the input to the action
    Observation: the result of the action
    ... (this Thought/Action/Action Input/Observation can repeat N times)
    Thought: I now know the final answer
    Final Answer: the final answer to the original input question in Korean

    Begin!

    Question: {query}
    Thought:{agent_scratchpad}'''
    )

    tools = []
    search = DuckDuckGoSearchRun()
    tools.append(
        Tool(
            name="web_search",
            func=search.run,
            description="자동차 부품에 대해 무엇인지 물어보면 웹에서 검색하여 답변",
            return_direct=False
        )
    )

    tools.append(
        Tool(
            name="document_retrieval",
            func=lambda q: retrieval(q, vector_store, default_filter),
            description="자동차 문제 관련 질문 시 검색된 컬 문서를 참고하여 답변",
            return_direct=False
        )
    )

    # agent = create_tool_calling_agent(model, tools, prompt)
    agent = create_react_agent(model, tools, prompt)

    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=False,
        max_iterations=30,
        max_execution_time=60,
        handle_parsing_errors=True,
    )

    agent_with_history = RunnableWithMessageHistory(
        agent_executor,
        get_session_history=lambda session_id: get_by_session_id(session_id, history),
        input_messages_key='query',
        history_messages_key='history',
    )
    
    return agent_with_history


def generate_agent(model_type, model_name, vector_store, default_filter, history, token=None):
    if model_type == "ollama":
        model = load_ollama(model_name=model_name)
    elif model_type == "hf":
        model = load_hf(model_name=model_name, quantization=True)
    elif model_type == "endpoint":
        model = use_endpoint(model_name=model_name, token=token)
    else:
        raise ValueError("Unsupported model type")
    agent = build_agent(model, vector_store, default_filter, history)

    return agent