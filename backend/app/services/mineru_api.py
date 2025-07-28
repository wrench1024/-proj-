from fastapi import APIRouter, HTTPException, Body
import os
import subprocess
from typing import List, Dict
import sys
import logging
import asyncio
from collections import deque
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.config import get_logger

router = APIRouter()

logger = get_logger(__name__)

import json
import requests
from typing import Dict, Optional
from dataclasses import dataclass
import shutil

class OCRClient:
    def __init__(self, app_id: str, secret_code: str):
        self.app_id = app_id
        self.secret_code = secret_code

    def recognize(self, file_content: bytes, options: dict) -> str:
        # 构建请求参数
        params = {}
        for key, value in options.items():
            params[key] = str(value)

        # 设置请求头
        headers = {
            "x-ti-app-id": self.app_id,
            "x-ti-secret-code": self.secret_code,
            # 方式一：读取本地文件
            "Content-Type": "application/octet-stream"
            # 方式二：使用URL方式
            # "Content-Type": "text/plain"
        }

        # 发送请求
        response = requests.post(
            f"https://api.textin.com/ai/service/v1/pdf_to_markdown",
            params=params,
            headers=headers,
            data=file_content
        )

        # 检查响应状态
        response.raise_for_status()
        return response.text

def ocr_image_to_markdown(image_path: str, api_key: str, secret_key: str) -> Optional[str]:
    """
    将图片通过 OCR 转换为 Markdown 文件，并返回 Markdown 文件路径。

    :param image_path: 图片文件的路径
    :param api_key: OCRClient 的 API 密钥
    :param secret_key: OCRClient 的密钥
    :return: 生成的 Markdown 文件路径，如果转换失败则返回 None
    """
    try:
        # 创建客户端实例
        client = OCRClient(api_key, secret_key)

        # 读取图片文件
        with open(image_path, "rb") as f:
            file_content = f.read()

        # 设置转换选项
        options = dict(
            apply_document_tree=1,
            catalog_details=1,
            dpi=144,
            get_excel=1,
            get_image="objects",
            markdown_details=1,
            page_count=1,
            page_details=1,
            parse_mode="scan",
            table_flavor="html",
            paratext_mode="annotation",
        )

        response = client.recognize(file_content, options)

        # 生成 JSON 文件路径
        json_path = image_path.rsplit('.', 1)[0] + '.json'
        # 保存完整的 JSON 响应到 result.json 文件
        with open(json_path, "w", encoding="utf-8") as f:
            f.write(response)

        # 解析 JSON 响应以提取 markdown 内容
        json_response = json.loads(response)
        if "result" in json_response and "markdown" in json_response["result"]:
            markdown_content = json_response["result"]["markdown"]
            # 生成 Markdown 文件路径
            markdown_path = image_path.rsplit('.', 1)[0] + '.md'
            with open(markdown_path, "w", encoding="utf-8") as f:
                f.write(markdown_content)
            return markdown_path
        else:
            return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def replace_image_lines_with_md(original_md_path: str) -> None:
    """
    将原 Markdown 文件中图片行替换为对应的 Markdown 文件内容。

    :param original_md_path: 原 Markdown 文件的路径
    """
    # 读取原 Markdown 文件内容
    with open(original_md_path, 'r', encoding='utf-8') as original_file:
        original_lines = original_file.readlines()

    logger.info(original_md_path)
    # logger.info(original_lines)
    
    # 存储图片行的索引和对应的图片文件名
    image_line_indices = []
    image_file_names = []

    # 找到原文件中所有图片那一行的索引，并提取图片文件名
    for index, line in enumerate(original_lines):
        if line.strip().startswith('![](images/'):
            image_line_indices.append(index)
            # 提取图片文件名
            start_index = line.find('images/') + len('images/')
            end_index = line.find('.', start_index)
            if end_index == -1: continue
            image_file_name = line[start_index:end_index] + '.md'
            image_file_names.append(image_file_name)

    # 获取原 Markdown 文件所在的目录
    original_md_dir = os.path.dirname(original_md_path)
    logger.info(image_line_indices)
    logger.info(image_file_names)

    # 倒序遍历每个图片行的索引和对应的图片文件名，尝试进行替换
    for index, image_file_name in reversed(list(zip(image_line_indices, image_file_names))):
        # 在原 Markdown 文件同级目录下的 images 文件夹中构建文件路径
        md_file_path = os.path.join(original_md_dir, 'images', image_file_name)
        if os.path.exists(md_file_path):
            # 读取新解析出的 Markdown 文件内容
            try:
                with open(md_file_path, 'r', encoding='utf-8') as new_file:
                    new_content = new_file.readlines()
                # 替换图片那一行
                original_lines[index:index + 1] = new_content
            except Exception as e:
                logger.info(f"读取文件 {md_file_path} 时出错: {e}")
        else:
            logger.info(f"未找到对应的 Markdown 文件: {md_file_path}，不进行替换。")

    # 将修改后的内容写回原文件
    with open(original_md_path, 'w', encoding='utf-8') as original_file:
        original_file.writelines(original_lines)

    logger.info("替换操作完成。")

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
        # with open(f'result_page_{page_number + 1}.json', 'w', encoding='utf-8') as fw:
        #     json.dump(result, fw, indent=4, ensure_ascii=False)
        # 构建输出路径

        print(result)
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

        print(result)
        # 构建输出路径
        output_md_path = os.path.join(output_dir, f"{base_name}/txt/", f"{base_name}.md")
        
        with open(output_md_path, 'w', encoding='utf-8', errors='replace') as fw:
            fw.write(result['result']['markdown'])
            logger.info(f"dock的 Markdown 已保存至 {output_md_path}")

        return {"status": "success", "output_file": output_md_path}

    except Exception as e:
        logger.error(f"处理dock的时出错: {e}")
        return {"status": "failed", "message": f"处理dock的时出错: {e}"}


def process_pdf_file(file_path: str, output_dir: str, parse_mode: str) -> Dict[str, str]:
    if not os.path.exists(file_path):
        logger.error(f"[400] 文件路径 {file_path} 不存在")
        return {"status": 400, "error": "INVALID_PATH", "detail": f"路径 {file_path} 不存在"}

    file_name = os.path.basename(file_path)
    
   # 根据 parse_mode 决定配置文件路径
    if parse_mode == 'mineru': config_path = '/home/mengshengbo/RegDoc_System/backend/app/core/table_magic-pdf.json' # mineru模式使用表格处理
    else: config_path = '/home/mengshengbo/RegDoc_System/backend/app/core/notable_magic-pdf.json' # 所有非 mineru 模式使用默认配置 

    if not os.path.isabs(config_path):
        logger.error(f"配置文件路径必须是绝对路径: {config_path}")
        return {"status": 500, "error": "INVALID_CONFIG_PATH"}

    # 创建子进程环境变量副本
    env = os.environ.copy()
    env['MINERU_TOOLS_CONFIG_JSON'] = config_path  # 动态注入配置路径

    # 如果之前该文档已经被解析过了，直接清除之前的文件夹，防止出现images文件夹下内容冗余，和mineru_textin情况下,md文件识别有问题
    base1 = os.path.splitext(file_name)[0]
    delt = os.path.join(output_dir, base1)
    if os.path.exists(delt):
        try:
            logger.info(f"清理历史文件夹: {delt}")
            shutil.rmtree(delt)  # 删除整个文件夹
        except Exception as e:
            logger.error(f"删除文件夹 {delt} 失败: {str(e)}")

    if file_name.endswith('.pdf') or file_name.endswith('.docx') or file_name.endswith('.PDF') or file_name.endswith('.DOCX'):
        # 构建并执行 magic-pdf 命令
        command = f'CUDA_VISIBLE_DEVICES=1 magic-pdf -p "{file_path}" -o "{output_dir}" -m txt'
        
        try:
            logger.info('*****************')
            subprocess.run(command, shell=True, check=True, env=env)
            logger.info('*****************')
            logger.info(f"[200] 成功执行 magic-pdf 命令，处理文件: {file_path}")

            # 获取文件名（不包含扩展名）
            base_name = os.path.splitext(file_name)[0]

            # 构建可能包含 Markdown 文件的目录路径
            potential_dir = os.path.join(output_dir, base_name)

            # 检查该目录是否存在
            if os.path.exists(potential_dir) and os.path.isdir(potential_dir):
                # 遍历该目录下的所有文件

                if parse_mode == 'mineru_textin':
                    for root, dirs, files in os.walk(potential_dir):
                        for file in files:
                            if file.endswith('.md'):
                                # 找到 Markdown 文件，返回其完整路径
                                md_file_path = os.path.join(root, file)
                                try:
                                    # 找到 Markdown 文件同级目录
                                    md_dir = os.path.dirname(md_file_path)
                                    images_dir = os.path.join(md_dir, 'images')
                                    if os.path.exists(images_dir) and os.path.isdir(images_dir):
                                        for img_file in os.listdir(images_dir):
                                            img_path = os.path.join(images_dir, img_file)
                                            if os.path.isfile(img_path) and img_file.endswith('.jpg') :
                                                # api_key = "8d26211a38b67565b5ef9f7eb0639fa9"  # 请替换为实际的 API 密钥
                                                # secret_key = "c3a743585ff9410087591da9bd487e8c"  # 请替换为实际的密钥
                                                api_key = "f7913264b0f08ad6a0f492156998a5e8"
                                                secret_key = "72c28b6469b76d6056eb64e70d4376fb"
                                                ocr_image_to_markdown(img_path, api_key, secret_key)
                                                logger.info("")
                                    replace_image_lines_with_md(md_file_path)
                                    # 读取 Markdown 文件内容
                                    with open(md_file_path, 'r', encoding='utf-8') as f:
                                        md_content = f.read()
                                    return {"status": "success", "output_file": md_file_path, "md_content": md_content}
                                except Exception as e:
                                    logger.error(f"读取 Markdown 文件 {md_file_path} 内容时出错: {e}")
                                    return {"status": "failed", "message": f"读取 Markdown 文件内容时出错: {e}"}
                                
                elif parse_mode == 'mineru':
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
                
                elif parse_mode == 'textin':
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
                                            
                        except subprocess.CalledProcessError as e:
                            logger.error(f"处理文件 {file_path} 时，textin 命令出错: {e}")
                            return {"status": "failed", "message": "textin 命令执行出错"}
                    
        except subprocess.CalledProcessError as e:
            logger.error(f"处理文件 {file_path} 时，magic-pdf 命令出错: {e}")
            return {"status": "failed", "message": "magic-pdf 命令执行出错"}
    else:
        # 返回原始文件路径
        logger.info(f"[200] 跳过非处理文件: {file_name}")
        return {"status": 200, "output_file": file_path}

async def process_queue(queue: deque, output_dir: str, parse_mode: str):
    results = []
    while queue:
        file_path = queue.popleft()
        #file_path = os.path.join('/app/review_system',file_path)
        result = await asyncio.to_thread(process_pdf_file, file_path, output_dir, parse_mode)
        results.append(result)
    return results

@router.post("/parse-files/")
async def parse_files(file_paths: List[str] = Body(..., description="Paths to the files to be processed"),
                      output_dir: str = Body(..., description="Output directory"),
                      parse_mode: str = Body("mineru", description="解析模式: mineru, mineru_textin, textin")) -> List[Dict[str, str]]:
    
    if parse_mode not in ["mineru", "mineru_textin", "textin"]:
        raise HTTPException(status_code=400, detail="Invalid parse_mode")
    if not isinstance(file_paths, list):
        raise HTTPException(status_code=422, detail="file_paths must be a list of strings")
    queue = deque(file_paths)
    #output_dir = os.path.join('/app/review_system',output_dir)
    results = await process_queue(queue, output_dir, parse_mode)
    return results

if __name__ == "__main__":
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(router)
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7000)


    