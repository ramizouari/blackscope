from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace

import config

DEFAULT_MODEL = config.config.default_model
DEFAULT_VL_MODEL = config.config.default_vl_model

def get_vl_model():
    """
    Creates and returns a pre-configured Vision-Language (VL) model based on a
    specified HuggingFace endpoint.

    The returned VL model is configured to operate with conversational capabilities
    using the default repository and an auto-determined
    provider.

    :return: An instance of `ChatHuggingFace` configured with a conversational
        VL model.
    """
    return ChatHuggingFace(
        llm=HuggingFaceEndpoint(
            repo_id=DEFAULT_VL_MODEL,
            provider="auto",  # set your provider here
            task="conversational"
        )
    )