import os
import openai

def get_openai_client():
    """檢查 API 金鑰並回傳 OpenAI client instance。"""
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("環境變數 OPENAI_API_KEY 未設定，無法呼叫 OpenAI API。")
    return openai.OpenAI(api_key=api_key)

def get_answer_from_llm(question, context):
    prompt = f"你是一個文件問答助理，請根據以下內容回答問題：\n\n內容：{context}\n\n問題：{question}\n\n請用繁體中文簡潔回答。"
    try:
        client = get_openai_client()
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "你是一個文件問答助理，請用繁體中文回答。"},
                {"role": "user", "content": prompt}
            ],
            max_tokens=512,
            temperature=0.2
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f'OpenAI API 失敗: {str(e)}'

def generate_summary(full_text):
    """
    使用 LLM 生成文件摘要
    """
    prompt = f"你是一個專業的文件摘要助理。請根據以下全文，生成一段約 100 字的繁體中文摘要。\n\n全文內容：\n{full_text}"
    try:
        client = get_openai_client()
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "你是一個文件摘要助理，請用繁體中文回答。"},
                {"role": "user", "content": prompt}
            ],
            max_tokens=512,
            temperature=0.3
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f'摘要生成失敗: {str(e)}'

def create_qa_prompt(question: str, context: str) -> str:
    """
    建立一個包含上下文和問題的提示。
    """
    prompt_template = """
請根據以下提供的上下文來回答問題。如果答案不在上下文中，請回答「根據提供的文件內容，我無法回答這個問題」。

上下文：
\"\"\"
{context}
\"\"\"

問題：「{question}」
"""
    return prompt_template.format(context=context, question=question)

def send_to_openai(model: str, temperature: float, max_tokens: int, prompt: str):
    """
    將請求發送至 OpenAI API。
    """
    client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    system_message = """
        你是一個專業的AI文件助理。你的任務是根據使用者提供的上下文來回答問題。
        請基於上下文進行回答，並盡可能整合上下文中的相關資訊來提供一個全面且準確的答案。
        你的回答應該完全基於提供的資料，不要使用任何外部知識或個人觀點。
        如果上下文完全沒有提到與問題相關的資訊，你才需要回答：「根據提供的文件內容，我無法回答這個問題。」
    """

    try:
        response = client.chat.completions.create(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        return None 