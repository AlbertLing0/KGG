import openai
import os
import json
import streamlit as st

# API Configuration for vLLM local service
# 這裡必須填 "EMPTY"，因為 vLLM 不需要真實的 OpenAI Key
API_KEY = "EMPTY"
# SSH 隧道地址
BASE_URL = "http://localhost:8081/v1"
# 模型名稱 (必須與 vLLM 服務中的模型名稱一致)
DEFAULT_MODEL = "/mnt/chenbaiming/gpt-oss-120b"

# Initialize client
client = openai.OpenAI(
    api_key=API_KEY,
    base_url=BASE_URL
)

def call_llm(system_msg, user_msg, model_name=DEFAULT_MODEL):
    """Call the LLM API and get the response along with token usage."""
    st.info(system_msg, icon="🔥")
    st.info(user_msg, icon="🔥")
    st.info(f"当前模型: {model_name}", icon="ℹ️")
    
    try:
        # Make the API call
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg}
            ]
        )

        # Extract the response text
        response_text = response.choices[0].message.content

        # Get token usage
        token_usage = response.usage.total_tokens
        st.info(f"Total tokens consumed: {token_usage}", icon="ℹ️")

        return response_text  # Return both the response text and token usage

    except Exception as e:
        error_msg = f"API call error: {str(e)}"
        st.error(error_msg)
        return error_msg  # 返回字符串而不是元组
