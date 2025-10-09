import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
import torch
from langchain_ollama import ChatOllama
from transformers import BitsAndBytesConfig
from transformers import AutoTokenizer, AutoModelForCausalLM
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace, HuggingFacePipeline
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

def load_embedding_model(model_name):
    embedding_model = HuggingFaceEmbeddings(model_name=model_name)

    return embedding_model

def load_ollama(model_name):
    model = ChatOllama(model=model_name, temperature=0)

    return model

def load_hf(model_name, quantization=True): # 4bit 양자화 모델 로드
    print('hf model start to loaded')
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    print('tokenizer loaded')
    if quantization:
        quant_config = BitsAndBytesConfig(
        load_in_4bit=True,                    
        bnb_4bit_quant_type='nf4',            
        bnb_4bit_use_double_quant=True,       
        bnb_4bit_compute_dtype=torch.float16 
        )

        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            quantization_config=quant_config,
            dtype=torch.bfloat16,
            device_map='cuda'
        )

        print('quantized model loaded')
    else:
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            dtype=torch.bfloat16,
            device_map='cuda'
        )
        print('model loaded')

    qa_pipeline = pipeline(
        "text-generation",
        model=model,
        tokenizer=tokenizer,
        use_cache=True,
        return_full_text=False,
        device_map='cuda',
        max_new_tokens=512,
        do_sample=True,
        top_k=7,
        num_return_sequences=1,
        eos_token_id=tokenizer.eos_token_id,
        pad_token_id=tokenizer.eos_token_id,
    )
    print('pipeline constructed')

    llm = HuggingFacePipeline(pipeline=qa_pipeline)
    llm = ChatHuggingFace(llm=llm)
    print('llm loaded')
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