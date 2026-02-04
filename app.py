import streamlit as st
from google import genai
from google.genai import types

# 頁面標題與設定
st.set_page_config(page_title="生合生技 - 產品諮詢專家", layout="wide")

# 從系統背景讀取 API Key (同事看不到)
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
except:
    st.error("系統尚未完成 API 設定，請聯絡 PM。")
    st.stop()

# 嚴格的生技專家指令
SYSTEM_INSTRUCTION = """
# 系統角色
你是一位公司內部的生技產品專家（PM 支援角色）。
你的回答僅限於「解讀既有產品資料與研究結果」，禁止進行產品規劃、配方設計。

主要核心產品：TWK10 益生菌原料。

# 核心原則
1. 閉環資料原則：所有回答必須嚴格僅依據上傳文件、文獻。
2. 零推測原則：若資料未提及，不可進行邏輯推論。
3. 誠實拒絕：資料不足時回覆：「此問題目前資料不足，請聯絡 PM 進一步確認。」

# 功能性回答判斷
● 情境 A (查無資料)：輸出【判定：查無研究數據】並結束。
● 情境 B (僅有動物實驗)：輸出【實驗層級：動物實驗觀察】，並加註「未經人體臨床驗證」警語。
● 情境 C (具備人體臨床)：輸出【實驗層級：人體臨床試驗】，以此為唯一核心。

# 行銷紅線
禁止對動物實驗使用「改善、提升、有效、有助於、功效顯示」等詞彙。
"""

st.title("🧬 TWK10 產品技術諮詢專家")
st.caption("生合生物科技內部專用系統 - 僅供技術查詢")

# 初始化紀錄
if "messages" not in st.session_state:
    st.session_state.messages = []

# 顯示對話歷史
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 處理使用者問題
if prompt := st.chat_input("請輸入關於 TWK10 的問題..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    try:
        client = genai.Client(api_key=API_KEY)
        
        # 呼叫 Gemini 2.0 Flash 模型
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=0.1, # 保持極高精準度
                tools=[types.Tool(google_search=types.GoogleSearch())]
            )
        )

        with st.chat_message("assistant"):
            st.markdown(response.text)
        
        st.session_state.messages.append({"role": "assistant", "content": response.text})

    except Exception as e:
        st.error(f"發生連線錯誤，請稍後再試。")
