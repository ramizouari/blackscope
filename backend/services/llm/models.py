from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace

import config

DEFAULT_MODEL = config.config.default_model
DEFAULT_VL_MODEL = config.config.default_vl_model

def get_vl_model():
    return ChatHuggingFace(
        llm=HuggingFaceEndpoint(
            repo_id="Qwen/Qwen3-VL-30B-A3B-Instruct",
            provider="auto",  # set your provider here
            task="conversational"
        )
    )