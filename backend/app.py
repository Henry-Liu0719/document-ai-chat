from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import os
import json
from dotenv import load_dotenv
from pdf_utils import parse_pdf
from flask_cors import CORS
from search_utils import search_relevant_paragraphs
from llm_utils import create_qa_prompt, generate_summary, send_to_openai

load_dotenv()  # 在應用程式啟動時載入 .env 檔案

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}
MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB
EXAMPLE_FOLDER = 'doc_examples'

app = Flask(__name__)
CORS(app)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': '未選擇檔案'}), 400
    file = request.files['file']
    
    # 從表單獲取 'generate_summary' 標誌
    should_generate_summary = request.form.get('generate_summary') == 'true'

    if file.filename == '':
        return jsonify({'error': '未選擇檔案'}), 400
    if not allowed_file(file.filename):
        return jsonify({'error': '只允許 PDF 檔案'}), 400
    filename = secure_filename(file.filename)
    save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(save_path)
    # 解析 PDF 並存成 json
    try:
        pages = parse_pdf(save_path)
        json_path = save_path + '.json'
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(pages, f, ensure_ascii=False, indent=2)
        
        summary = ''
        if should_generate_summary:
            # 將所有頁面的文字合併成一個字串
            full_text = "\n".join(pages.values())
            summary = generate_summary(full_text)

    except Exception as e:
        return jsonify({'error': f'PDF 解析或摘要失敗: {str(e)}'}), 500
    
    return jsonify({
        'message': '上傳並解析成功', 
        'filename': filename,
        'summary': summary
    }), 200

@app.route('/use_example', methods=['POST'])
def use_example_file():
    data = request.json
    filename = data.get('filename')
    should_generate_summary = data.get('generate_summary', False)

    if not filename:
        return jsonify({'error': '未提供檔案名稱'}), 400

    example_file_path = os.path.join(EXAMPLE_FOLDER, filename)
    if not os.path.exists(example_file_path):
        return jsonify({'error': '範例檔案不存在'}), 404

    # 將範例檔案複製到上傳目錄
    save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    try:
        import shutil
        shutil.copy(example_file_path, save_path)
    except Exception as e:
        return jsonify({'error': f'無法複製範例檔案: {str(e)}'}), 500
    
    # 解析 PDF 並存成 json
    try:
        pages = parse_pdf(save_path)
        json_path = save_path + '.json'
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(pages, f, ensure_ascii=False, indent=2)
        
        summary = ''
        if should_generate_summary:
            full_text = "\n".join(pages.values())
            summary = generate_summary(full_text)

    except Exception as e:
        return jsonify({'error': f'PDF 解析或摘要失敗: {str(e)}'}), 500
    
    return jsonify({
        'message': '範例檔案處理成功', 
        'filename': filename,
        'summary': summary
    }), 200


@app.route('/search', methods=['POST'])
def search():
    data = request.json
    filename = data.get('filename')
    question = data.get('question')
    if not filename or not question:
        return jsonify({'error': '缺少 filename 或 question'}), 400
    json_path = os.path.join(app.config['UPLOAD_FOLDER'], filename + '.json')
    try:
        results = search_relevant_paragraphs(json_path, question, top_k=3)
        # 格式化回傳
        formatted = [
            {'page': p, 'content': t, 'score': float(s)} for p, t, s in results
        ]
        return jsonify({'results': formatted}), 200
    except Exception as e:
        return jsonify({'error': f'搜尋失敗: {str(e)}'}), 500

@app.route('/qa', methods=['POST'])
def qa():
    data = request.json
    filename = data.get('filename')
    question = data.get('question')
    send_request = data.get('send_request', True)

    if not filename or not question:
        return jsonify({'error': '缺少 filename 或 question'}), 400
    json_path = os.path.join(app.config['UPLOAD_FOLDER'], filename + '.json')
    try:
        results = search_relevant_paragraphs(json_path, question, top_k=3)
        context = '\n'.join([f'【第{p}頁】{t}' for p, t, s in results])
        
        prompt = create_qa_prompt(question, context)
        
        answer = ''
        if send_request:
            answer = send_to_openai(
                model="gpt-3.5-turbo",
                temperature=0,
                max_tokens=1024,
                prompt=prompt
            )
        else:
            answer = "（未發送請求）"

        return jsonify({'answer': answer, 'context': context, 'prompt': prompt}), 200
    except Exception as e:
        return jsonify({'error': f'問答失敗: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 