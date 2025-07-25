### 📝 LLM 應用規格文件

這份文件詳細說明「Document AI Chat」專案中大型語言模型（LLM）的應用方式、技術細節與核心流程。

---

### 🤖 核心模型與服務

-   **服務提供者 (Service Provider)**: OpenAI
-   **主要模型 (Model)**: `gpt-3.5-turbo`
-   **💡 知識點：為什麼選擇 `gpt-3.5-turbo`？**
    -   `gpt-3.5-turbo` 在成本、速度與效能之間取得了絕佳的平衡。它非常適合處理問答和摘要等對話式任務，且 API 回應速度快，能提供流暢的使用者體驗。對於需要更高準確性的場景，未來可考慮升級至 `gpt-4` 或更新的模型。

---

### 🔍 主要應用場景

本專案主要將 LLM 應用於以下兩個核心功能：

1.  **文件問答 (Question Answering)**: 基於檢索增強生成 (RAG) 架構。
2.  **文件摘要 (Summarization)**: 直接生成全文摘要。

---

### ⚙️ 1. 文件問答 (RAG) 流程

RAG 是一種結合外部知識庫（在此專案中是使用者上傳的 PDF 文件）來增強 LLM 回答能力的技術。它能有效減少模型「幻覺」（Hallucination）的發生，並讓回答更具備時效性與準確性。

**完整流程如下：**

1.  **檢索 (Retrieval) 🔎**:
    -   **目標**: 從文件中找出與使用者問題最相關的段落。
    -   **工具**: `scikit-learn` 的 `TfidfVectorizer`。
    -   **流程**:
        1.  系統讀取已解析的 `.json` 文件快取。
        2.  使用 TF-IDF 演算法計算使用者問題與文件中所有段落的「餘弦相似度」（Cosine Similarity）。
        3.  選取相似度分數最高的 **3** 個段落作為「上下文」（Context）。
    -   **💡 知識點：什麼是 TF-IDF？**
        -   TF-IDF（詞頻-逆文件頻率）是一種統計方法，用來評估一個詞語對於一個文件集或一個語料庫中的一份文件的重要程度。它能有效地過濾掉常見的停用詞（如「的」、「是」），並凸顯出關鍵詞，從而實現更精準的相似度計算。
    -   **💡 知識點：為什麼使用 TF-IDF 而非 Embedding？**
        -   **權衡考量**: 在本專案的初期階段，選擇 TF-IDF 主要是基於**簡單性**與**效能**的考量。
        -   **TF-IDF 優點**:
            -   **輕量快速**: 它不需依賴外部模型或大量的計算資源，在本機上就能快速完成索引和搜尋，非常適合原型開發與中小型文件。
            -   **無需 API 成本**: 整個檢索過程都在本地端使用 `scikit-learn` 完成，不會產生額外的 API 呼叫費用。
        -   **Embedding 的取捨**:
            -   雖然 **Embedding**（例如 OpenAI 的 `text-embedding-ada-002`）能夠理解語意相似度（例如「勞工」和「員工」在語意上相近），在檢索準確性上通常更勝一籌，但它會帶來額外的複雜性和成本：
                1.  **計算與儲存成本**: 文件中的所有段落都必須先透過 API 轉換為向量（Vector）並儲存，這會產生費用。
                2.  **查詢延遲**: 每次使用者提問時，問題本身也需要被轉換為向量，這會增加一次 API 呼叫的延遲。
            -   因此，對於這個專案，TF-IDF 是一個符合成本效益且高效的起點。未來若需處理更複雜的語意查詢，可再考慮升級至基於 Embedding 的檢索方法。

2.  **增強 (Augmentation) ✍️**:
    -   **目標**: 建立一個結構清晰、指令明確的提示（Prompt），引導 LLM 產生高品質的回答。
    -   **流程**: 將上一步檢索到的上下文（Context）與使用者的原始問題（Question）組合成一個提示。
    -   **提示模板 (Prompt Template)**:
        ```text
        請根據以下提供的上下文來回答問題。如果答案不在上下文中，請回答「根據提供的文件內容，我無法回答這個問題」。

        上下文：
        """
        {context}
        """

        問題：「{question}」
        ```
    -   **💡 知識點：提示工程 (Prompt Engineering)**
        -   一個好的提示對於 LLM 的輸出品質至關重要。這個模板包含了幾個關鍵元素：
            -   **角色扮演 (Role-playing)**: "請根據..."，設定 AI 的行為模式。
            -   **上下文注入 (Context Injection)**: 將檢索到的段落放入 `{context}`。
            -   **指令清晰 (Clear Instruction)**: "回答問題"。
            -   **防護欄 (Guardrail)**: "如果答案不在上下文中..."，這是一個重要的安全機制，防止模型在資訊不足時憑空捏造答案。

3.  **生成 (Generation) 🧠**:
    -   **目標**: 呼叫 LLM API，生成最終回答。
    -   **API 呼叫**: `llm_utils.py` 中的 `send_to_gemini` 函數（**注意：此函數應更名為 `send_to_openai`**）負責將組合好的提示發送給 OpenAI API。
    -   **模型參數 (Parameters)**:
        -   `model`: "gpt-3.5-turbo"
        -   `temperature`: 0.7 (在創造性與確定性之間取得平衡)
        -   `max_tokens`: 1024 (限制回答的最大長度)
    -   **回傳**: API 的回覆會被解析，並將純文字答案呈現給前端使用者。

---

### 📄 2. 文件摘要 (Summarization) 流程

此功能旨在快速提供文件的核心內容概覽。

1.  **內容準備**:
    -   系統會將 PDF 的所有頁面文字合併成一個長字串。

2.  **提示設計**:
    -   **提示模板**:
        ```text
        請將以下文件內容摘要成一份約 150 字的精簡摘要，專注於文章的核心觀點、主要發現和重要結論。

        文件內容：
        """
        {document_text}
        """
        ```

3.  **API 呼叫與生成**:
    -   與問答流程類似，組合好的提示被發送至 OpenAI API。
    -   模型會根據全文內容生成一份符合字數要求的摘要。

---

### 🔐 API 金鑰與安全

-   **金鑰管理**: API 金鑰嚴格透過**環境變數 (`OPENAI_API_KEY`)** 載入，避免硬式編碼在程式碼中。
-   **💡 知識點：為什麼不能硬式編碼 (Hardcode) API 金鑰？**
    -   將金鑰直接寫入程式碼並提交到版本控制系統（如 Git）是極大的安全風險。一旦程式碼被公開，任何人都可以竊取您的金鑰，導致您的帳戶被濫用並產生高額費用。使用環境變數是將敏感資訊與程式碼分離的最佳實踐。 