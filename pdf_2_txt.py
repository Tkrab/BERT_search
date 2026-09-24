import os
from PyPDF2 import PdfFileReader
from pdfplumber import PDF
import ssl

# 禁用 SSL 验证
ssl._create_default_https_context = ssl._create_unverified_context


def extract_text_from_pdf(pdf_path):
    with PDF.open(pdf_path) as pdf:
        text = ''
        for page in pdf.pages:
            text += page.extract_text()
    return text


def main():
    # 设置文件路径
    base_dir = os.path.dirname(os.path.abspath(__file__))
    paper_dir = os.path.join(base_dir, 'data', 'paper')
    output_dir = os.path.join(base_dir, 'data', 'paper_txt')

    # 获取所有PDF文件
    pdf_files = [f for f in os.listdir(paper_dir) if f.endswith('.pdf')]

    # 创建输出目录
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 处理每个PDF文件
    total_files = len(pdf_files)
    for idx, pdf_file in enumerate(pdf_files, 1):
        print(f'处理进度: {idx}/{total_files}')
        pdf_path = os.path.join(paper_dir, pdf_file)
        text = extract_text_from_pdf(pdf_path)

        # 保存文本文件
        output_path = os.path.join(output_dir, f'{pdf_file}.txt')
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(text)


if __name__ == '__main__':
    main()