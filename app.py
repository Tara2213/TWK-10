import streamlit as st
from google import genai
from google.genai import types
import os

# --- 頁面設定 ---
st.set_page_config(page_title="生合生物科技 - 益生菌技術諮詢系統", layout="wide")

# --- 系統指令 (你優化過的嚴謹 Prompt) ---
SYSTEM_INSTRUCTION = """
# 系統角色
你是一位公司內部的生技產品專家（PM 支援角色），主要職責是精準回覆業務端提出的產品技術與研究詢問。
你的回答僅限於「解讀既有產品資料與研究結果」，禁止進行產品規劃、配方設計或任何開發建議。

主要核心產品：TWK10 益生菌原料。

# 核心原則（最高優先權）
1. 閉環資料原則：所有回答必須嚴格僅依據使用者上傳的文件、文獻或系統既有試驗結果。嚴禁調用預訓練模型中的通用常識或網路資訊。
2. 零推測原則：若資料中未提及特定數據，不可進行任何邏輯推論。
3. 誠實拒絕：當資料不足時，必須僅回覆：「此問題目前資料不足，請聯絡 PM 進一步確認。」並立即停止回答。

# 功能性回答前之【強制判斷流程】
● 情境 A (查無資料)：輸出【判定：查無研究數據】並結束。
● 情境 B (僅有動物實驗)：輸出【實驗層級：動物實驗觀察】，僅說明機制並加上強制警語。
● 情境 C (具備人體臨床)：輸出【實驗層級：人體臨床試驗】，以此為核心依據。

# 行銷轉譯語言紅線
- 禁止對動物實驗結果使用：改善、提升、有效、有助於、功效顯示。
- 動物實驗僅能使用：觀察到、機制顯示、數據呈現、相關性研究。

# 語氣與語言
- 專業、務實、嚴謹、冷靜。一律使用繁體中文。
"""

# --- 側邊欄：設定 ---
with st.sidebar:
    st.title("⚙️ 系統設定")
    api_key = st.text_input("輸入 Gemini API Key", type="password")
    st.info("💡 提醒：請確保您的 API Key 已開啟 Google Search 或相關工具權限以檢索文獻。")
    if st.button("清除對話紀錄"):
        st.session_state.messages = []
        st.rerun()

st.title("🧬 TWK10 產品技術諮詢專家")
st.caption("本系統僅供內部業務同仁查詢產品技術文獻，回覆內容嚴禁直接對外作為廣告文宣使用。")

# --- 初始化對話紀錄 ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 顯示歷史對話 ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 處理使用者輸入 ---
if prompt := st.chat_input("請輸入關於 TWK10 的問題..."):
    if not api_key:
        st.error("請先在左側輸入 API Key 才能開始諮詢。")
    else:
        # 顯示使用者問題
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # 呼叫 Gemini API
        try:
            client = genai.Client(api_key=api_key)
            
            # 設定生成配置
            config = types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=0.2, # 保持嚴謹度
                tools=[types.Tool(google_search=types.GoogleSearch())], # 允許搜尋現有資料庫
            )

            with st.chat_message("assistant"):
                response_placeholder = st.empty()
                full_response = ""
                
                # 串流輸出
                for chunk in client.models.generate_content_stream(
                    model="gemini-2.0-flash", # 建議使用 flash 速度較快且免費額度多
                    contents=prompt,
                    config=config,
                ):
                    full_response += chunk.text
                    response_placeholder.markdown(full_response + "▌")
                
                response_placeholder.markdown(full_response)
            
            st.session_state.messages.append({"role": "assistant", "content": full_response})

        except Exception as e:
            st.error(f"連線出錯了：{str(e)}")
