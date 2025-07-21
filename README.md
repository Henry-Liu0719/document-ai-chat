# Document AI Chat

這是一個基於大型語言模型（LLM）的智慧文件問答與摘要應用程式。使用者可以上傳 PDF 文件，系統會對文件內容進行分析、摘要，並允許使用者針對文件內容提出問題，由 AI 提供精準的回答。

## 核心功能

- **PDF 文件上傳與解析**：支援上傳 PDF 檔案，後端會自動解析並提取純文字內容。
- **文件內容摘要生成**：在上傳文件時，可選擇自動生成一份約 100 字的內容摘要。
- **基於文件內容的問答 (RAG)**：結合了文件內容檢索與大型語言模型，讓 AI 能根據文件中的具體資訊回答使用者的提問。

## 技術選型與架構 (Schema)

本專案採用前後端分離的架構。

### 後端 (Backend)

- **框架 (Framework)**: `Flask`
- **PDF 處理 (PDF Processing)**: `PyPDF2`
- **內容檢索 (Content Retrieval)**: `scikit-learn` (用於計算文字相似度，找出與問題最相關的段落)
- **CORS 處理**: `flask-cors`

### 前端 (Frontend)

- 一個基本的 `HTML` 頁面，透過 JavaScript 的 `fetch` API 與後端進行互動。

### 大型語言模型 (Large Language Model - LLM)

- **服務提供者 (Service Provider)**: **OpenAI**
- **模型 (Model)**: `gpt-3.5-turbo`
- **應用場景**:
    1.  **問答 (Question Answering)**: 採用 **檢索增強生成 (Retrieval-Augmented Generation, RAG)** 模式。
    2.  **摘要 (Summarization)**: 將全文發送給模型以生成摘要。

---

## 系統流程 (System Workflow)

### 1. 文件上傳與預處理

1.  **上傳**: 使用者從前端介面選擇一個 PDF 檔案並點擊上傳。
2.  **接收與儲存**: Flask 後端接收檔案，並將其儲存於 `/uploads` 資料夾。
3.  **解析與快取**:
    - 後端呼叫 `pdf_utils.py` 中的 `parse_pdf` 函數，逐頁提取 PDF 的文字內容。
    - 提取出的內容會被儲存為一個 `.json` 檔案（例如 `example.pdf.json`），作為快取，避免重複解析。
4.  **(可選) 生成摘要**:
    - 如果使用者勾選了「生成摘要」選項，後端會將所有頁面的文字合併。
    - 呼叫 `llm_utils.py` 中的 `generate_summary` 函數，將全文傳送給 `gpt-3.5-turbo` 模型以生成摘要。

### 2. 問答流程 (RAG)

當使用者針對已上傳的文件提出問題時，系統會啟動 RAG 流程：

1.  **問題接收**: Flask 後端透過 `/qa` 端點接收來自前端的 `filename` 和 `question`。
2.  **檢索 (Retrieval)**:
    - 系統讀取對應的 `.json` 快取檔案。
    - 呼叫 `search_utils.py` 中的 `search_relevant_paragraphs` 函數。此函數使用 `scikit-learn` 的 TF-IDF 演算法來計算問題與文件中所有段落之間的相似度分數。
    - 系統會找出分數最高的 K 個段落（目前設定為 3）作為上下文（Context）。
3.  **增強 (Augmentation)**:
    - 系統將檢索到的上下文段落與使用者的原始問題組合成一個結構化的提示（Prompt）。這個提示會明確指示 LLM 根據提供的上下文來回答問題。
4.  **生成 (Generation)**:
    - 組合好的提示被傳送給 `llm_utils.py` 中的 `send_to_gemini` 函數（**注意：此函數名稱有誤，實際呼叫的是 OpenAI 的 API**）。
    - `gpt-3.5-turbo` 模型根據提示生成回答，並由後端回傳給前端顯示。

---

## API 端點

- `POST /upload`
  - **功能**: 上傳 PDF 檔案並進行解析。
  - **Request Body**: `multipart/form-data`，包含 `file` 和可選的 `generate_summary` (`true`/`false`)。
  - **Response**: 成功訊息、檔名和文件摘要（如果已生成）。

- `POST /search`
  - **功能**: 僅執行內容檢索，回傳最相關的段落。
  - **Request Body**: JSON 格式，包含 `filename` 和 `question`。
  - **Response**: 包含頁碼、內容和相關性分數的段落列表。

- `POST /qa`
  - **功能**: 執行完整的 RAG 問答流程。
  - **Request Body**: JSON 格式，包含 `filename` 和 `question`。
  - **Response**: AI 生成的回答、用於生成回答的上下文，以及完整的提示。

## 如何設定與啟動

1.  **複製儲存庫**:
    ```bash
    git clone <repository-url>
    cd document-ai-chat
    ```

2.  **建立並啟用虛擬環境**:
    ```bash
    python -m venv venv
    # Windows
    .\venv\Scripts\activate
    # macOS/Linux
    source venv/bin/activate
    ```

3.  **安裝依賴套件**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **設定環境變數**:
    為了讓應用程式能夠存取 OpenAI API，您必須設定 API 金鑰。在您的終端機中設定環境變數：
    ```bash
    # Windows (PowerShell)
    $env:OPENAI_API_KEY="sk-..."

    # macOS/Linux
    export OPENAI_API_KEY="sk-..."
    ```
    **重要**: 請勿將您的 API 金鑰直接寫入程式碼中。

5.  **啟動後端伺服器**:
    ```bash
    python backend/app.py
    ```
    伺服器將會在 `http://localhost:5000` 啟動。

6.  **開啟前端頁面**:
    在您的瀏覽器中直接開啟 `frontend/index.html` 檔案即可開始使用。

## 未來改進方向

- **API 金鑰管理**: 移除程式碼中硬式編碼的備用 API 金鑰，強制從環境變數載入，以提高安全性。
- **修正函數命名**: 將 `llm_utils.py` 中的 `send_to_gemini` 函數更名為 `send_to_openai` 或更通用的名稱，以避免混淆。
- **支援更多文件格式**: 擴充檔案處理能力，支援如 `.docx`, `.txt` 等更多格式。
- **前端介面優化**: 使用現代前端框架（如 Vue 或 React）重構，提升使用者體驗與互動性。
- **非同步處理**: 對於大型文件，解析和摘要過程可能耗時較長。導入非同步任務佇列（如 Celery 或 Dramatiq）可以防止請求超時，提升系統的回應速度。 