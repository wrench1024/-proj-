"""
lcj 2025/5/11
文件解析接口
接收文件路径作为输入，对指定路径的文件进行markdown格式处理。
具体处理逻辑如下：
1. 接收用户传入的文件路径，检查该文件是否存在。
2. 对文件使用 textinapi 对其进行处理，并将处理结果输出到指定的输出目录。
3. 处理完成后，在输出目录中查找生成的 Markdown 文件，若找到则返回其路径；若未找到则返回处理失败信息。
4. 若文件不是 PDF或word 格式，则直接返回文件的原始路径。
整个过程中会使用日志记录关键信息，包括命令执行等情况，方便后续的调试和监控。
5.此接口可以说是寄生于mineru的接口，一般是先使用mineru解析之后，在使用此接口，将mineru解析出来的md文件给覆盖掉
"""
import requests
import json
from fastapi import APIRouter, HTTPException, Body
import os
import subprocess
from typing import List, Dict
import sys
import logging
import asyncio
from collections import deque

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.core.config import get_logger

router = APIRouter()

output_dir = 'file'
os.makedirs(output_dir, exist_ok=True)

logger = get_logger(__name__)
import requests
import json

def get_file_content(filePath):
    with open(filePath, 'rb') as fp:
        return fp.read()

class TextinOcr(object):
    def __init__(self, app_id, app_secret):
        self._app_id = app_id
        self._app_secret = app_secret
        self.host = 'https://api.textin.com'

    def recognize_pdf2md(self, image_path, options, is_url=False):
        """
        pdf to markdown
        :param options: request params
        :param image_path: string
        :param is_url: bool
        :return: response
        """
        url = self.host + '/ai/service/v1/pdf_to_markdown'
        headers = {
            'x-ti-app-id': self._app_id,
            'x-ti-secret-code': self._app_secret
        }
        if is_url:
            image = image_path
            headers['Content-Type'] = 'text/plain'
        else:
            image = get_file_content(image_path)
            headers['Content-Type'] = 'application/octet-stream'

        return requests.post(url, data=image, headers=headers, params=options)

from PyPDF2 import PdfReader
from docx import Document

def get_pdf_page_count(pdf_path: str) -> int:
    """
    获取指定 PDF 文件的总页数
    :param pdf_path: PDF 文件路径
    :return: 总页数
    """
    try:
        reader = PdfReader(pdf_path)
        return len(reader.pages)
    except Exception as e:
        logger.error(f"无法读取 PDF 文件 {pdf_path} 的页数: {e}")
        raise
    
def process_single_page(file_path: str, page_number: int, output_dir: str) -> Dict[str, str]:
    """
    解析 PDF 的指定页码并生成 Markdown 文件
    :param file_path: PDF 文件路径
    :param page_number: 当前页码（从 0 开始）
    :param output_dir: 输出目录
    :return: 处理结果信息
    """
    
    # textin = TextinOcr('8d26211a38b67565b5ef9f7eb0639fa9', 'c3a743585ff9410087591da9bd487e8c')
    textin = TextinOcr('f7913264b0f08ad6a0f492156998a5e8', '72c28b6469b76d6056eb64e70d4376fb')

    file_name = os.path.basename(file_path)
    base_name = os.path.splitext(file_name)[0]

    try:
        resp = textin.recognize_pdf2md(file_path, {
            'page_start': page_number + 1,
            'page_count': 1,  # 设置解析页数为1000页
            'table_flavor': 'html',
            'parse_mode': 'scan',  # 设置解析模式为scan模式
            'page_details': 1,  # 不包含页面细节  
            'markdown_details': 1,
            'apply_document_tree': 1,
            'catalog_details':1,
            'dpi': 144,  # 分辨率设置为144 dpi
            'get_excel':1, # 是否返回excel结果
            'paratext_mode':"annotation", #  markdown中非正文文本内容展示模式
            'get_image': "objects"
        })
        print("request time: ", resp.elapsed.total_seconds())

        if resp.status_code != 200:
            logger.error(f"[{resp.status_code}] 第 {page_number + 1} 页解析失败")
            return {"status": "failed", "message": f"第 {page_number + 1} 页解析失败"}

        result = json.loads(resp.text)

        # 构建输出路径
        output_md_path = os.path.join(output_dir, f"{base_name}/txt/", f"{base_name}_page_{page_number + 1}.md")

        with open(output_md_path, 'w', encoding='utf-8', errors='replace') as fw:
            fw.write(result['result']['markdown'])
            logger.info(f"第 {page_number + 1} 页 Markdown 已保存至 {output_md_path}")

        return {"status": "success", "output_file": output_md_path}

    except Exception as e:
        logger.error(f"处理第 {page_number + 1} 页时出错: {e}")
        return {"status": "failed", "message": f"处理第 {page_number + 1} 页时出错: {e}"}

def process_page(file_path: str, output_dir: str) -> Dict[str, str]:
    """
    解析 docx 的指定页码并生成 Markdown 文件
    :param file_path: PDF 文件路径
    :param page_number: 当前页码（从 0 开始）
    :param output_dir: 输出目录
    :return: 处理结果信息
    """
    
    # textin = TextinOcr('8d26211a38b67565b5ef9f7eb0639fa9', 'c3a743585ff9410087591da9bd487e8c')
    textin = TextinOcr('f7913264b0f08ad6a0f492156998a5e8', '72c28b6469b76d6056eb64e70d4376fb')

    file_name = os.path.basename(file_path)
    base_name = os.path.splitext(file_name)[0]

    try:
        resp = textin.recognize_pdf2md(file_path, {
            'page_start': 0,
            'page_count': 1000,  # 设置解析页数为1000页
            'table_flavor': 'html',
            'parse_mode': 'scan',  # 设置解析模式为scan模式
            'page_details': 1,  # 不包含页面细节
            'markdown_details': 1,
            'apply_document_tree': 1,
            'catalog_details':1,
            'dpi': 144,  # 分辨率设置为144 dpi
            'get_excel':1, # 是否返回excel结果
            'paratext_mode':"annotation", #  markdown中非正文文本内容展示模式
            'get_image':'objects'
        })
        print("request time: ", resp.elapsed.total_seconds())

        if resp.status_code != 200:
            logger.error(f"[{resp.status_code}] 解析失败")
            return {"status": "failed", "message": f"解析失败"}

        result = json.loads(resp.text)

        # 构建输出路径
        output_md_path = os.path.join(output_dir, f"{base_name}/txt/", f"{base_name}.md")

        with open(output_md_path, 'w', encoding='utf-8', errors='replace') as fw:
            fw.write(result['result']['markdown'])
            logger.info(f"docx的 Markdown 已保存至 {output_md_path}")

        return {"status": "success", "output_file": output_md_path}

    except Exception as e:
        logger.error(f"处理docx的时出错: {e}")
        return {"status": "failed", "message": f"处理docx的时出错: {e}"}
    
def process_pdf_file(file_path: str) -> Dict[str, str]:
    if not os.path.exists(file_path):
        logger.error(f"[400] 文件路径 {file_path} 不存在")
        return {"status": "failed", "message": "文件路径不存在"}
    
    file_name = os.path.basename(file_path)
    
    if file_name.endswith('.pdf') or file_name.endswith('.docx'):
        try:
            if file_name.endswith('.pdf'):
                total_pages = get_pdf_page_count(file_path)
                logger.info(f"开始处理 PDF 文件，共 {total_pages} 页")

                all_md_files = []
            
                for page_num in range(total_pages):
                    result = process_single_page(file_path, page_num, output_dir)
                    if result["status"] == "success": all_md_files.append(result["output_file"])
                    else: logger.warning(f"跳过第 {page_num + 1} 页的整合，继续处理下一页...")

                if not all_md_files:
                    logger.error("未生成任何 Markdown 文件")
                    return {"status": "failed", "message": "未生成任何 Markdown 文件"}
                
                # 保存Markdown内容（核心修改）
                base_name = os.path.splitext(file_name)[0]
                output_md_path = os.path.join(output_dir, f"{base_name}/txt/", f"{base_name}.md")

                with open(output_md_path, 'w', encoding='utf-8') as merged_file:
                    for md_file in all_md_files:
                        with open(md_file, 'r', encoding='utf-8') as f:
                            merged_file.write(f.read())

                logger.info(f"所有页面已合并至 {output_md_path}")

            elif file_name.endswith('.docx'):
                result = process_page(file_path, output_dir)
                if result["status"] == "success": output_md_path = result["output_file"]
                else: logger.warning("docx解析失败")


            # 构建可能包含 Markdown 文件的目录路径
            base_name = os.path.splitext(file_name)[0]
            potential_dir = os.path.join(output_dir, base_name)

            # 检查该目录是否存在
            if os.path.exists(potential_dir) and os.path.isdir(potential_dir):
                # 遍历该目录下的所有文件
                for root, dirs, files in os.walk(potential_dir):
                    for file in files:
                        if file.endswith('.md'):
                            # 找到 Markdown 文件，返回其完整路径
                            md_file_path = os.path.join(root, file)
                            try:
                                # 读取 Markdown 文件内容
                                with open(md_file_path, 'r', encoding='utf-8') as f:
                                    md_content = f.read()
                                return {"status": "success", "output_file": md_file_path, "md_content": md_content}
                            except Exception as e:
                                logger.error(f"读取 Markdown 文件 {md_file_path} 内容时出错: {e}")
                                return {"status": "failed", "message": f"读取 Markdown 文件内容时出错: {e}"}

            # 如果没有找到 Markdown 文件
            logger.warning("未找到生成的 Markdown 文件")
            return {"status": "failed", "message": "未找到生成的 Markdown 文件"}

        except subprocess.CalledProcessError as e:
            logger.error(f"处理文件 {file_path} 时，textin 命令出错: {e}")
            return {"status": "failed", "message": "textin 命令执行出错"}
    else:
        return {"status": "success", "outputFile": file_path}


import pandas as pd

if __name__ == "__main__":
    # file_path = '/home/ysdx2025/review_system/file/贵州省行政区划'
    # process_pdf_file(file_path)

    table_file_path = '/home/ysdx2025/review_system/knowledge_base/知识库附件信息(1).xlsx'  # 替换为你的表格文件路径
    
    # 读取Excel文件
    df = pd.read_excel(table_file_path)

    # 假设表格列从0开始索引，第1列为文件夹名，第3列为文件名
    for index, row in df.iterrows():
        folder_name = row[1]  # 第二列为文件夹名
        file_name = row[3]    # 第四列为文件名
        
        file_path = '/home/ysdx2025/shuikeyuan/knowledge_base'
        # 构建完整的PDF文件路径
        file_path = os.path.join(file_path, folder_name, file_name)  # 假设文件是PDF格式
        
        print(file_path)
        # # 检测有哪些地址不存在
        # base_name = os.path.splitext(file_name)[0]
        # file_end_path = os.path.join('./file', base_name, 'txt', f'{base_name}.md')
        
        # if not os.path.exists(file_end_path):
        #     logger.error(f"文件最终存的地儿{file_end_path},不存在")
        #     continue
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            logger.error(f"文件 {file_path} 不存在")
            continue
        
        # 处理PDF文件
        result = process_pdf_file(file_path)
        
        if result["status"] == "success":
            logger.info(f"文件 {file_path} 处理成功: {result['output_file']}")
        else:
            logger.error(f"文件 {file_path} 处理失败: {result['message']}")


# if __name__ == "__main__":
#     # 请登录后前往 “工作台-账号设置-开发者信息” 查看 app-id/app-secret
#     textin = TextinOcr('f7913264b0f08ad6a0f492156998a5e8', '72c28b6469b76d6056eb64e70d4376fb')

#     # 示例 1：传输文件
#     image = '/home/lcj/shuikeyuan-daily/routers/11111.pdf'
#     resp = textin.recognize_pdf2md(image, {
#         'page_start': 0,
#         'page_count': 1000,  # 设置解析页数为1000页
#         'table_flavor': 'md',
#         'parse_mode': 'scan',  # 设置解析模式为scan模式
#         'page_details': 0,  # 不包含页面细节
#         'markdown_details': 1,
#         'apply_document_tree': 1,
#         'dpi': 144  # 分辨率设置为144 dpi
#     })
#     print("request time: ", resp.elapsed.total_seconds())

#     result = json.loads(resp.text)
#     with open('result_1.md', 'w', encoding='utf-8') as fw:
#         json.dump(result, fw, indent=4, ensure_ascii=False)
