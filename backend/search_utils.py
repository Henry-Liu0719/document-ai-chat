import json
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def search_relevant_paragraphs(pdf_json_path, question, top_k=3):
    """
    根據問題，從 PDF 解析內容（json）中找出最相關的段落
    回傳 [(頁碼, 內容, 分數)]
    """
    if not os.path.exists(pdf_json_path):
        raise FileNotFoundError('找不到解析內容')
    with open(pdf_json_path, 'r', encoding='utf-8') as f:
        pages = json.load(f)
    page_numbers = list(pages.keys())
    texts = [pages[p] for p in page_numbers]
    # 加入問題進行 TF-IDF
    corpus = texts + [question]
    vectorizer = TfidfVectorizer().fit(corpus)
    tfidf_matrix = vectorizer.transform(corpus)
    question_vec = tfidf_matrix[-1]
    doc_vecs = tfidf_matrix[:-1]
    sims = cosine_similarity(question_vec, doc_vecs)[0]
    ranked = sorted(zip(page_numbers, texts, sims), key=lambda x: x[2], reverse=True)
    return ranked[:top_k] 