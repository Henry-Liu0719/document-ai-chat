import os
from PyPDF2 import PdfReader

def parse_pdf(file_path):
    """
    解析 PDF，回傳 {頁碼: 文字} 字典
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError('找不到檔案')
    reader = PdfReader(file_path)
    pages = {}
    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ''
        pages[i+1] = text.strip()
    return pages 