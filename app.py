import streamlit as st
import google.generativeai as genai
import os

# --- 1. 系統指令 (嚴格遵循 PM 支援與行銷紅線) ---
SYSTEM_PROMPT = """
你是一位公司內部的生技產品專家（PM 支援角色），主要職責是精準回覆業務端提出的產品技術與研究詢問。
你的回答僅限於「解讀既有產品資料與研究結果」，禁止進行產品規劃、配方設計或任何開發建議。

主要核心產品：TWK10 益生菌原料。

# 核心原則
1. 閉環資料原則：所有回答必須嚴格僅依據使用者上傳的文件、文獻。嚴禁調用通用常識。
2. 零推測原則：若資料中未提及特定數據，不可進行任何邏輯推論。
3. 誠實拒絕：資料不足時，僅回覆：「此問題目前資料不足，請聯絡 PM 進一步確認。」

# 功能性回答前之【強制判斷流程】
● 情境 A (查無資料)：輸出【判定：查無研究數據】並結束。
● 情境 B (僅有動物實驗)：輸出【實驗層級：動物實驗觀察】。僅說明機制，強制加上警語：「此功能性尚未經人體臨床試驗驗證，不可作為人體功效宣稱。」
● 情境 C (具備人體臨床)：輸出【實驗層級：人體臨床試驗】。

# 行銷轉譯語言紅線
- 動物實驗禁止使用：改善、提升、有效、有助於、功效顯示。
- 動物實驗僅能使用：觀察到、機制顯示、數據呈現、相關性研究。

# 語氣與語言
- 語氣：專業、務實、嚴謹、冷靜。
- 語言：繁體中文。
"""

# --- 2. 介面與側邊欄 ---
st.set_page_config(page_title="TWK10 技術支援系統", layout="wide")
st.title("🧬 TWK10 技術與轉譯支援系統")
st.caption("目前運行模型：Gemini 1.5 Pro (Experimental)")

with st.sidebar:
    st.header("⚙️ API 設定")
    # 從 Secrets 讀取預設 Key，若無則留空
    default_key = st.secrets.get("GEMINI_API_KEY", "")
    api_key = st.text_input("輸入 Gemini API Key:", value=default_key, type="password")
    
    st.markdown("---")
    uploaded_files = st.file_uploader("上傳 TWK10 研究文獻 (PDF)", accept_multiple_files=True, type=['pdf'])

# --- 3. 初始化 Experimental 模型 ---
if api_key:
    try:
        genai.configure(api_key=api_key)
        # 精確對接 Google AI Studio 中的 Experimental 1.5 Pro 版本
        model = genai.GenerativeModel(
            model_name="gemini-1.5-pro-exp-0801", # 或使用 "models/gemini-1.5-pro-latest"
            system_instruction=SYSTEM_PROMPT
        )
    except Exception as e:
        st.error(f"模型啟動失敗：{e}")
        st.stop()
else:
    st.warning("請在左側輸入 API Key。")
    st.stop()

# --- 4. 檔案處理邏輯 ---
processed_docs = []
if uploaded_files:
    for f in uploaded_files:
        with open(f.name, "wb") as tmp:
            tmp.write(f.getbuffer())
        with st.spinner(f"正在分析文獻: {f.name}..."):
            genai_file = genai.upload_file(path=f.name)
            processed_docs.append(genai_file)
        os.remove(f.name)

# --- 5. 聊天與回應處理 ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

if prompt := st.chat_input("請描述業務詢問..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            # 整合文件與提問
            inputs = []
            if processed_docs:
                inputs.extend(processed_docs)
            inputs.append(prompt)
            
            # 設定 Temperature 以確保嚴謹
            response = model.generate_content(
                inputs,
                generation_config={"temperature": 0.2}
            )
            
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            
        except Exception as e:
            # 針對 429 錯誤的友善化處理
            if "429" in str(e):
                st.error("⚠️ 目前 API 使用額度已達上限（Free Tier 限制）。請等待約 60 秒後再發問，或考慮將模型切換為 Gemini 1.5 Flash 以獲得更高的呼叫次數。")
            else:
                st.error(f"執行出錯：{str(e)}")
