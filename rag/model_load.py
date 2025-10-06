import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
import torch
from langchain.llms import Ollama
from transformers import BitsAndBytesConfig
from transformers import AutoTokenizer, AutoModelForCausalLM
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.agents import AgentType, initialize_agent, load_tools
from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace, HuggingFacePipeline
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline


def load_embedding_model(model_name):
    embedding_model = HuggingFaceEmbeddings(model_name=model_name)

    return embedding_model

def load_ollama(model_name):
    model = Ollama(model=model_name)

    return model

def load_hf(model_name, quantization=True): # 4bit 양자화 모델 로드

    tokenizer = AutoTokenizer.from_pretrained(model_name)

    if quantization:
        quant_config = BitsAndBytesConfig(
        load_in_4bit=True,                    
        bnb_4bit_quant_type='nf4',            
        bnb_4bit_use_double_quant=True,       
        bnb_4bit_compute_dtype=torch.bfloat16 
        )

        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            quantization_config=quant_config,
            dtype=torch.bfloat16,
            device_map='auto'
        )

    else:
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            dtype=torch.bfloat16,
            device_map='auto'
        )

    qa_pipeline = pipeline(
        "text-generation",
        model=model,
        tokenizer=tokenizer,
        device_map="auto",
        return_full_text=False
    )

    llm = HuggingFacePipeline(pipeline=qa_pipeline)
    
    return llm

def use_endpoint(model_name, token):
    endpoint = HuggingFaceEndpoint(
        repo_id=model_name,
        task='text-generation',
        max_new_tokens=1024,
        huggingfacehub_api_token=token,
    )

    model = ChatHuggingFace(llm=endpoint, verbose=True)

    return model