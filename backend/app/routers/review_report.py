"""
待审查报告解析接口
指标审查接口
"""
import re
import asyncio
import subprocess
from fastapi import APIRouter, Request,Body,Response,UploadFile,File,HTTPException
from pypdf import PdfReader, PdfWriter
from app.core.config import get_logger
import json
import tempfile
import os
import shutil
import pdfplumber
from concurrent.futures import ThreadPoolExecutor
from docx2pdf import convert
from concurrent.futures  import as_completed 
from datetime import datetime
import requests
import sys
from fuzzywuzzy import fuzz
# from ollama import chat
# from ollama import AsyncClient
import requests
from langchain.document_loaders import DirectoryLoader,UnstructuredMarkdownLoader
from langchain.document_loaders  import TextLoader
# from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from langchain.docstore.document import Document
from routers.knowledge_inter import retrieval
from routers.chunknew0521 import process_markdown_file
# from routers.llm_extract_key_elements import llm_extract_key_elements
# from openai import OpenAI
import aiohttp
from openai import AsyncOpenAI
# from collections import defaultdict
import torch
import jieba
from fastapi import APIRouter, Body
import asyncio
from langchain.embeddings import SentenceTransformerEmbeddings
import numpy as np
from langchain.docstore.in_memory import InMemoryDocstore
import faiss
import tiktoken

client = AsyncOpenAI(
    api_key="sk-762b0529add947b081778614c7fe1cda",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)

headers = {'Content-Type': 'application/json'}

# 设置 OpenAI 的 API key 和 API base 来使用 vLLM 的 API server.
openai_api_key = "EMPTY"  # 如果不需要 API key，可以留空或设置为 "EMPTY"
openai_api_base = "http://localhost:8000/v1"

#api_key="sk-762b0529add947b081778614c7fe1cda", 
#base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 指定本地模型路径
embedding_model_path = "backend/app/models/bge-m3"
embeddings = SentenceTransformerEmbeddings(model_name=embedding_model_path)  # 全局嵌入模型实例

#url = 'http://localhost:7001/generate_text/'
model_path = '/home/ysdx2025/shuikeyuan/model/qwen/Qwen/Qwen2___5-14B-Instruct'
#url = "http://localhost:8000/v1/chat/completions"
router = APIRouter()

logger = get_logger(__name__)

# 创建一个线程池，最大并发数为 5
executor = ThreadPoolExecutor(max_workers=3)

# 定义将 DOCX 文件转换为 PDF 文件的函数
# def convert_docx_to_pdf(docx_bytes: bytes, output_path: str):
#     # 使用 BytesIO 将字节流保存为临时文件
#     with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as temp_docx_file:
#         temp_docx_file.write(docx_bytes)
#         temp_docx_path = temp_docx_file.name
    
#     # 转换为 PDF 并读取 PDF 内容到字节流
#     convert(temp_docx_path, output_path)
    
#     # 删除临时文件
#     os.remove(temp_docx_path)

# # 定义将 PDF 文件切块并保存的函数
# def split_pdf(pdf_path: str, output_folder: str):
#     # 打开 PDF 文件
#     with pdfplumber.open(pdf_path) as pdf:
#         # 遍历每一页面并将每个页面保存为单独的 PDF 文件
#         for i, page in enumerate(pdf.pages):
#             output_path = os.path.join(output_folder, f"page_{i+1}.pdf")
#             with open(output_path, "wb") as out:
#                 out.write(page.extract_text().encode())

def convert_docx_to_pdf(input_file, output_dir):
    try:
        # 运行 LibreOffice 命令
        command = [
            "libreoffice", 
            "--headless", 
            "--convert-to", "pdf", 
            "--outdir", output_dir, 
            input_file
        ]
        
        subprocess.run(command, check=True)
        logger.info(f"{input_file} Successful conversion to folder {output_dir}")
    except subprocess.CalledProcessError as e:
        logger.error(f": conversion fail{e}")

# 定义 MinerU 识别过程的函数
def minerU_recognition(project_folder: str):
    logger.info(f"Starting minerU recognition on folder {project_folder}")
    # 在这里实现 minerU 识别逻辑
    # 示例：模拟一个长时间运行的任务
    import time
    time.sleep(10)  # 模拟耗时操作
    logger.info(f"Completed minerU recognition on folder {project_folder}")


def remove_trailing_numbers(s : str):
    """
    去除字符串末尾的连续数字。
    
    :param s: 要处理的目标字符串
    :return: 去除了末尾所有连续数字后的字符串
    """
    # 使用正则表达式替换字符串末尾的连续数字为空字符串
    return re.sub(r'\d+$', '', s)

def extract_trailing_numbers(s : str):
    """
    提取字符串末尾的连续数字。
    
    :param s: 要处理的目标字符串
    :return: 字符串末尾的连续数字（如果有的话），否则返回 None。
    """
    # 使用正则表达式查找字符串末尾的连续数字
    match = re.search(r'(\d+)$', s)
    if match:
        return match.group(0)  # 返回匹配到的数字
    else:
        return None  # 如果没有找到匹配项，则返回 None
    
def is_chinese_char(char):
    """
    判断给定字符是否为汉字。
    
    :param char: 要检查的目标字符
    :return: 如果字符是汉字，则返回 True；否则返回 False。
    """
    # 使用正则表达式匹配汉字的 Unicode 范围
    return bool(re.match(r'[\u4e00-\u9fff]', char))

def has_single_continuous_dots(s):
    """
    判断字符串s中是否仅有一串连续的点，并且这些点是唯一的连续符号组合。
    
    参数:
    s (str): 要检查的字符串
    
    返回:
    bool: 如果字符串中仅包含一串连续的点，则返回True；否则返回False。
    """
    # 使用正则表达式找到所有连续的点组成的子串
    dots_sequences = re.findall(r'\.+', s)
    
    # 检查是否只有一个连续的点序列，并且这个序列长度大于等于1
    if len(dots_sequences) == 1:
        return True
    else:
        return False

#检验有序号的一级标题 1总论
def checkHaveXu(str : str):
    if '..' not in str:
        return False
    
    if not has_single_continuous_dots(str):
        return False

    yeshu = extract_trailing_numbers(str)
    if yeshu == None:
        return False
    
    str = remove_trailing_numbers(str)
    #第一个汉字之前没有. 且至少有一个数字
    isNum = False
    isDot = False
    for ch in str:
        if is_chinese_char(ch):
            if isNum and not isDot:
                return True
            else:
                return False
        elif ch in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']:
            isNum = True
        elif ch == '.':
            isDot = True
    return False

#检验全是汉字的一级标题 附件
def checkHaveZi(str : str):
    if '..' not in str:
        return False
    
    if not has_single_continuous_dots(str):
        return False

    yeshu = extract_trailing_numbers(str)
    if yeshu == None:
        return False
    
    str = remove_trailing_numbers(str)
    # 全是字
    isquanzi = True
    for ch in str:
        if ch != '.'and ch != ' ' and not is_chinese_char(ch):
            isquanzi = False
    if isquanzi:
        return True
    return False
def retain_chinese_characters(s : str):
    """
    保留字符串中的所有汉字。
    
    :param s: 要处理的目标字符串
    :return: 只包含汉字的字符串
    """
    # 使用正则表达式匹配并保留汉字
    return ''.join(re.findall(r'[\u4e00-\u9fff]+', s))

def split_pdf_by_pages(input_pdf_path : str, output_pdf_path : str, start_page : int, end_page : int):
    # 打开原始PDF
    reader = PdfReader(open(input_pdf_path, 'rb'))
    writer = PdfWriter()

    # 使用pdfplumber检查总页数（可选）
    with pdfplumber.open(input_pdf_path) as pdf:
        total_pages = len(pdf.pages)
        #print(f"Total pages: {total_pages}")

    # 确保起始和结束页码在合法范围内
    if start_page < 1 or end_page > total_pages or start_page > end_page:
        raise ValueError("Invalid page range.")

    # 复制选定页码范围内的页面到新PDF
    for i in range(start_page - 1, end_page):  # 注意索引从0开始
        page = reader.pages[i]
        writer.add_page(page)

    # 保存新PDF
    with open(output_pdf_path, 'wb') as output_pdf:
        writer.write(output_pdf)

def split_pdf(filepath : str, storepath : str):
    #切分结果
    print(filepath)
    split_result = {}
    with pdfplumber.open(filepath) as pdf:
        #存储一级标题
        yiji = {}
        pianyi = 1
        #第一个标题名称
        diyi = ''
        #是否找到目录
        isMulu = False
        #一级标题列表
        yiji_list = []
        #上一行
        last = ''
        for inum, page in enumerate(pdf.pages):
            text = ''.join(page.extract_text().split())
            if text.startswith('目录'):
                isMulu = True
            if not isMulu:
                continue
            lines = page.extract_text_lines()
            for inum, line in enumerate(lines):
                #print(len(words))
                if checkHaveXu(line['text']):
                    #有序号的标题
                    yeshu = extract_trailing_numbers(line['text'])
                    biaoti = line['text'].split('.', 1)[0].strip()
                    yiji[retain_chinese_characters(biaoti)] = yeshu
                    yiji_list.append(retain_chinese_characters(biaoti))
                    #全是汉字的标题
                elif last != '' and '.' in last and checkHaveZi(line['text']):
                    yeshu = extract_trailing_numbers(line['text'])
                    biaoti = line['text'].split('.', 1)[0].strip()
                    yiji[retain_chinese_characters(biaoti)] = yeshu
                    yiji_list.append(retain_chinese_characters(biaoti))
                last = line['text']

        print(yiji_list)

        #开始匹配
        #设置硬字段 只匹配一次 目录一定要放之前 硬字段不包含在目录里
        yingziduan = {'目录' : False, '水资源论证报告书基本情况表' : False, '节水评价登记表' : False}



        #开始对PDF进行切割  
        now_head = '开始.pdf'
        split_result[now_head] = {'起始页号' : 1, '终止页号' : None}
        yiji_list_idx = 0
        for inum, page in enumerate(pdf.pages):
            lines = page.extract_text_lines()
            if len(lines) == 0:
                continue
            text = retain_chinese_characters(lines[0]['text'])
            if text == '':
                continue
            #先匹配硬字段 循环比对 设置85为阈值
            for ziduan in yingziduan.keys():
                if yingziduan[ziduan] == False and fuzz.ratio(ziduan, text) >= 85:
                    #保存文件
                    split_result[now_head]['终止页号'] = inum
                    split_result[ziduan + '.pdf']={'起始页号' : inum + 1} 
                    yingziduan[ziduan] = True
                    now_head = ziduan + '.pdf'
                    break
            #一级标题按照在列表中的顺序进行匹配
            if yiji_list_idx < len(yiji_list) and yiji_list[yiji_list_idx] in text:
                #保存文件
                ziduan = yiji_list[yiji_list_idx]
                print(ziduan)
                split_result[now_head]['终止页号'] = inum
                split_result[ziduan + '.pdf']={'起始页号' : inum + 1, '终止页号' : None} 
                yiji_list_idx += 1
                now_head = ziduan + '.pdf'

        split_result[now_head]['终止页号'] = len(pdf.pages)
    
    # 删除附录、附表、附图部分
    exclude_titles = {'附录', '附表', '附图','附件'}
    keys_to_remove = [key for key in split_result.keys() if os.path.splitext(key)[0] in exclude_titles]
    for key in keys_to_remove: del split_result[key]
    
    #切分文件
    for key, value in split_result.items():
        split_pdf_by_pages(filepath, os.path.join(storepath, key), value['起始页号'], value['终止页号'])
    
    #保存json文件
    json_path = os.path.join(storepath, 'split_result.json')
    with open(json_path, 'w', encoding='utf-8') as json_file:
        json.dump(split_result, json_file, ensure_ascii=False, indent=4)
    all_pdf_files = [f for f in os.listdir(storepath)   
        if f.endswith('.pdf')  and f != os.path.basename(filepath)]
    
    return [os.path.join(storepath, pdf_file) for pdf_file in all_pdf_files]

TASK_PROGRESS = {}  # 内存数据库存储任务状态 
 
def call_api_for_pdfs(pdf_files, task_id, api_url, output_dir,parseMode):
    """遍历PDF文件并调用接口进行解析"""
    total = len(pdf_files)
    for index, file_path in enumerate(pdf_files):
        try:
            data = {
                "file_paths": [file_path],
                "output_dir": output_dir,
                "parse_mode": parseMode
            }
            response = requests.post(api_url, json=data)
            # print(response)
            if response.status_code == 200:
                result = response.json()
                print(result)
                TASK_PROGRESS[task_id]['completed'] += 1
                if result[0].get('status') =='success':
                    TASK_PROGRESS[task_id]['results'].append({
                        "file": result[0].get('output_file'),
                        "status": "success"
                    })
            else:
                TASK_PROGRESS[task_id]['failed'] += 1
                TASK_PROGRESS[task_id]['results'].append({
                    "error": f"接口返回状态码: {response.status_code}",
                    "status": "failed"
                })
        except Exception as e:
            TASK_PROGRESS[task_id]['failed'] += 1
            TASK_PROGRESS[task_id]['results'].append({
                "error": str(e),
                "status": "failed"
            })
        
        # 计算实时进度
        #progress = (index + 1) / total * 100
        #TASK_PROGRESS[task_id]['progress'] = f"{progress:.1f}%"
        
        # 修改后（取整为整数百分比）
        progress = int((index + 1) / total * 100)
        TASK_PROGRESS[task_id]['progress'] = f"{progress}%"
        
def check_results(future_list, task_id):
    """带进度追踪的任务检查"""
    total = len(future_list)
    for i, future in enumerate(as_completed(future_list)):
        try:
            result = future.result() 
            TASK_PROGRESS[task_id]['completed'] += 1 
            if result[0].get('status')== 'success':
                TASK_PROGRESS[task_id]['results'].append({
                    "file": result[0].get('outputFile'),
                    "status": "success"
                })  
        except Exception as e:
            TASK_PROGRESS[task_id]['failed'] += 1 
            TASK_PROGRESS[task_id]['results'].append({
                "error": str(e),
                "status": "failed"
            })
        
        # 计算实时进度 
        #progress = (i + 1) / total * 100 
        #TASK_PROGRESS[task_id]['progress'] = f"{progress:.1f}%"
        # 修改后（取整为整数百分比）
        progress = int((i + 1) / total * 100)
        TASK_PROGRESS[task_id]['progress'] = f"{progress}%"

@router.post("/upload_and_process/")
async def upload_and_process(
                             projectId : str = Body("",description="唯一标志此项目的键值"),
                             fileId : str = Body("", description="待审查的报告id"),
                             fileName : str = Body("", description="待审查的报告名字"),
                             file : UploadFile = File(None),
                             parseMode:str = Body("mineru", description="解析模式: mineru, mineru_textin, textin")
                            ):
    '''
    1.判断上传文件是什么类型，如果是pdf则直接处理，如果是word则转成pdf再处理。如果是其他类型则直接返回文件类型错误代码
    2.满足第一步判断后，首先将文件存下，返回调用信息code200.
    3.之后在后台线程中对pdf进行切块处理并存在同一个projectId目录下
    4.返回调用信息后，要继续执行一次对切块pdf进行minerU识别的操作
    '''
    # 检查是否有文件上传
    if not file:
        raise HTTPException(status_code=400, detail="No file uploaded")
    
    temp_dir = tempfile.mkdtemp()
    
    try:
        # 读取文件内容到内存
        file_content = await file.read()
        global project_folder
        # 构建项目文件夹路径
        project_folder = os.path.join("review_report",projectId,fileId)
        # 确保项目文件夹存在
        os.makedirs(project_folder, exist_ok=True)
        
        # 构建文件保存路径
        file_extension = os.path.splitext(fileName)[1].lower()
        original_file_path = os.path.join(project_folder, fileName)
        pdf_file_path = os.path.join(project_folder, os.path.splitext(fileName)[0] + ".pdf")
        
        # 根据文件类型处理文件
        if file_extension == ".pdf":
            # 保存原始 PDF 文件
            with open(original_file_path, "wb") as f:
                f.write(file_content)
            pdf_path = original_file_path
        elif file_extension == ".docx":
            # 保存原始 DOCX 文件
            with open(original_file_path, "wb") as f:
                f.write(file_content)
            # 将 DOCX 文件转换为 PDF 文件
            #convert_docx_to_pdf(file_content, pdf_file_path)
            convert_docx_to_pdf(original_file_path, project_folder)
            logger.info('File conversion successful')
            pdf_path = pdf_file_path
        
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type")
        

        split_futures = split_pdf(pdf_path, project_folder)
        
        # # # 提交 MinerU 识别过程到线程池
        # # future = executor.submit(minerU_recognition, project_folder)
        # # logger.info(f"Submitted task for project {projectId} to thread pool")
    
        # return {
        # "code": 200,
        # "message": "待审查报告已上传至服务器，后台解析中。"
        # }
        # 创建任务追踪器 
        task_id = f"{projectId}_{datetime.now().strftime('%Y%m%d%H%M%S')}" 
        task_status = {
            "total": len(split_futures),
            "completed": 0,
            "failed": 0,
            "results": [],
            "start_time": datetime.now().isoformat() 
        }
        TASK_PROGRESS[task_id] = task_status  # 内存存储进度 
        
        # # 启动后台结果检查 
        # background_tasks.add_task(check_results,  split_futures, task_id)
        
        api_url = "http://localhost:7000/parse-files/"
        #api_url = "http://parser:7000/parse-files/"
        # 启动异步检查（不使用 BackgroundTasks）
        import threading 
        threading.Thread(
            target=call_api_for_pdfs,
            args=(split_futures, task_id, api_url, project_folder,parseMode)
        ).start()
        
        return {
            "code": 200,
            "task_id": task_id,
            "message": "待审查报告已上传至服务器，后台解析中"
        }
        
        # "message" : "文件处理中，可通过/progress接口查询进度"
    
    except Exception as e:
        # 记录异常信息
        logger.error(f"Error processing file for project {projectId}: {str(e)}")
        return {
            "code": 500,
            "message": f"{str(e)}"
        }
    
    
@router.get("/progress/{task_id}") 
async def get_progress(task_id: str):
    """进度查询接口"""
    status = TASK_PROGRESS.get(task_id, {
        "error": "任务不存在或已过期",
        "code": 404 
    })
    
    if status.get('total'): 
        
        # 计算动态进度 
        elapsed = datetime.now()  - datetime.fromisoformat(status['start_time']) 
        #status['eta'] = str(elapsed * (100/status['completed']) if status['completed'] else '--')
        
        # 计算已运行时间并格式化为 "小时:分钟:秒"
        hours, remainder = divmod(elapsed.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        status['eta'] = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        
    return {
        "code": 200 if task_id in TASK_PROGRESS else 404,
        "data": status 
    } 

# 后台任务执行器（使用asyncio处理异步任务）
async def run_background_task(task_coroutine):
    """执行后台协程任务"""
    try:
        await task_coroutine
    except Exception as e:
        # 这里可以添加错误日志记录
        print(f"后台任务执行失败: {str(e)}")

@router.post("/review_indicator/")
async def review_indicator(
        modelName: str = Body("deepseek-r1", description="调用模型名称"),
        projectId: str = Body("test", description="唯一标志此项目的键值"),
        stageId: str = Body("test", description="审查阶段id"),
        fileId: str = Body("test", description="待审查的报告id"),
        taskId: str = Body("test", description="审查任务id"),
        topK: int = Body(5, description="检索的前topK个文本块"),
        reviewItemArray: list = Body([],
                                     description="审查项信息数组",
                                     examples=[[
                                         {
                                            "reviewItemId": "1",
                                            "reviewItemName": "水资源论证审批机关权限",
                                            "reviewItemContent": "",
                                            "reviewItemContent_searchConfig": "水资源论证报告书基本情况表;水资源论证审批机关;建设项目审批单位",
                                            "reviewItemContent_prompt": "",
                                            "kbSearchConfig": "贵州省取水许可和水资源费征收管理办法 第六条取水许可实行分级审批;珠江水利委员会水行政执法事项清单（2023 年版）取水许可 第十四条 取水许可实行分级审批",
                                            "kbArray": ["1b374ac32b15d4be4ee546b0b50ad987"],
                                            "reviewItemPrompt": "判断项目的水资源论证审批机关是否符合管理要求，是否存在越权审批情况",
                                        },
                                         {
                                             "reviewItemId": "2",
                                             "reviewItemName": "论证形式与内容",
                                             "reviewItemContent": "",
                                             "reviewItemContent_searchConfig": "水资源论证报告目录;水资源论证报告书基本情况表",
                                             "reviewItemContent_prompt": "",
                                             "kbSearchConfig": "《建设项目水资源论证导则》（GB/T-35580-2017）;《建设项目水资源论证导则 第1部分：水利水电建设项目》（SL/T 525.1—2023）;《火电建设项目水资源论证导则》（SL 763-2018）",
                                             "kbArray": [],
                                             "reviewItemPrompt": "判断编制的报告是否满足对应行业的水资源论证导则编制形式和章节安排的要求",
                                         },
                                     ]]
                                     ),
        concurrency: int = Body(3, description="同时进行审查的项数"),
        similarityThreshold: float = Body(default=0.1, description="相似度阈值参数"),
        workers: int = Body(default=10)
):
    '''
    1.根据传入的信息开始对projectId下的文件逐条进行指标审核
    2.从reviewItemArray.json下读取出每个指标项。
    3.从指标项的searchConfig字段检索对应的待审查文件块，从kbsearchConfig检索对应的依赖文件。
    4.调用prompt并将待审查文件块和依赖文件输入到大模型中进行指标合规性判断
    5.大模型输出格式化的结果
    6.将结果写入中间数据库
    7.返回代码
    '''
    
    #检查重复任务并终止已存在的相同任务
    task_key = (projectId, taskId)
    
    # 检查全局任务存储中是否存在相同任务
    async with task_lock:
        if task_key in running_tasks:
            logger.warning(f"检测到重复任务 {taskId}，正在终止原有任务...")
            existing_task = running_tasks.get(task_key)
            
            # 等待原有任务完成取消流程
            try:
                # 标记任务为取消状态
                existing_task.cancel()
            
            except asyncio.CancelledError:
                logger.info(f"任务 {taskId} 已成功取消")
            
            finally:
                # 从运行任务列表中移除
                if task_key in running_tasks:
                    del running_tasks[task_key]
                    
    # 构建项目文件夹路径
    project_folder = os.path.join("review_report", projectId,fileId)
    
    # 确保项目文件夹存在
    if not os.path.exists(project_folder):
        print(f"Project folder {project_folder} does not exist.")
        return {
            "code": 400,
            "message": f"projectId:{projectId} does not exist."
        }
    
    # 构建审查任务协程
    async def review_task():
        await process_review_indicators(
            modelName, projectId, stageId, fileId, taskId, topK, reviewItemArray, concurrency,similarityThreshold,workers
        )
    
    # 启动后台任务（不阻塞接口响应）
    asyncio.create_task(run_background_task(review_task()))    
    
    # 同步调用审查指标处理过程
    # await process_review_indicators(modelName,projectId, stageId, fileId, taskId, topK,reviewItemArray, concurrency)

    return {
        "code": 200,
        "message": "文档审查已开始，后台审查中，请等待审查完成。"
    }

# 检索表达式解析模块
class SearchQueryParser:
    OPERATORS = {'&': 'AND', '+': 'OR', '-': 'NOT'}
    DELIMITERS = {'(', ')', "'", '"'}

    def __init__(self, query):
        self.query = query.strip()
        self.tokens = []
        self.pos = 0
        self._validate_query()
        self._tokenize()

    def _validate_query(self):
        if len(self.query) > 120:
            raise ValueError("检索内容超过120字符限制")
        # 检查括号匹配
        count = 0
        for c in self.query:
            if c == '(':
                count += 1
            elif c == ')':
                count -= 1
            if count < 0:
                raise ValueError("括号匹配错误")
        if count != 0:
            raise ValueError("括号匹配错误")

    def _tokenize(self):
        while self.pos < len(self.query):
            c = self.query[self.pos]
            if c in self.DELIMITERS:
                self.tokens.append(('DELIM', c))
                self.pos += 1
            elif c in self.OPERATORS:
                # 修改处：直接添加运算符，不检查前后空格
                self.tokens.append(('OPERATOR', c))
                self.pos += 1
            elif c in "'\"":
                quote = c
                self.pos += 1
                start = self.pos
                while self.pos < len(self.query) and self.query[self.pos] != quote:
                    self.pos += 1
                if self.pos >= len(self.query):
                    raise ValueError("引号未闭合")
                self.tokens.append(('QUOTE_TOKEN', self.query[start:self.pos]))
                self.pos += 1  # 跳过闭合引号
            else:
                start = self.pos
                while self.pos < len(self.query) and self.query[self.pos] not in self.DELIMITERS.union(self.OPERATORS):
                    self.pos += 1
                self.tokens.append(('TOKEN', self.query[start:self.pos]))

    def parse(self):
        # 简单递归下降解析器（此处可扩展为更复杂的语法解析）
        # 示例返回结构化的查询树，实际应用需根据需求实现
        return self.tokens


# 文本匹配函数
def regex_search(text, query):
    try:
        parser = SearchQueryParser(query)
        tokens = parser.parse()

        regex = []
        for token_type, value in tokens:
            if token_type == 'QUOTE_TOKEN':
                regex.append(re.escape(value))
            elif token_type == 'TOKEN':
                regex.append(r'\b' + re.escape(value) + r'\b')
            elif token_type == 'OPERATOR':
                if value == '*':
                    regex.append(r'.*')
                elif value == '+':
                    regex.append(r'|')
                elif value == '-':
                    regex.append(r'(?!.*\b' + re.escape(value) + r'\b)')

        pattern = ''.join(regex)
        return re.search(pattern, text, re.IGNORECASE) is not None
    except Exception as e:
        print(f"检索语法错误: {e}")
        return False


# 正则检索触发条件判断函数
def use_regex_search(query: str) -> bool:
    """判断是否需要使用正则检索（包含运算符或特殊符号）"""
    # 修改连字符位置，避免字符范围错误
    special_chars = r'[-*+()\\\'"]'
    return bool(re.search(special_chars, query))


# 加载页码元数据
def load_page_metadata(metadata_file):
    with open(metadata_file, 'r', encoding='utf-8') as f:
        return json.load(f)


# 为每个文本块添加页码和偏移量元数据
def add_page_metadata(texts, page_metadata):
    new_texts = []
    for i, text in enumerate(texts):
        file_path = text.metadata.get('source')
        logger.info(f'-----mdfile_path-----:{file_path}')
        file_name = os.path.basename(file_path)
        # 将 .md 后缀替换为 .pdf 后缀
        file_name = file_name.replace('.md', '.pdf')
        logger.info(f'-----mdfile_name-----:{file_name}')
        if file_name in page_metadata:
            start_page = page_metadata[file_name]['起始页号']
            end_page = page_metadata[file_name]['终止页号']
            # 记录文本块在原始文档中的起始偏移量
            offset = text.metadata.get('offset', i)
            new_text = {
                "page_content": text.page_content,
                "metadata": {
                    "source": text.metadata.get('source'),
                    "start_page": start_page,
                    "end_page": end_page,
                    "offset": offset
                }
            }
            new_texts.append(new_text)
            #logger.info(f'current texts:{new_texts}')
        else:
            logger.info('======存在目录中不存在的解析md文件======')
            #new_texts.append(text)
    return new_texts


# 按页码和偏移量排序检索结果
def sort_results_by_page(results):
    return sorted(results, key=lambda x: (
        x[0].metadata.get('start_page', float('inf')),
        x[0].metadata.get('offset', float('inf'))
    ))
    
def build_faiss_vectorstore(documents, embeddings, index_type="ip"):
    """手动构建FAISS向量库（兼容旧版本LangChain）"""
    texts = [doc.page_content for doc in documents]
    embeddings_list = embeddings.embed_documents(texts)
    embedding_dim = len(embeddings_list[0]) if embeddings_list else 0
    
    # 新增：手动归一化（仅当需要余弦相似度时）
    if index_type == "ip":
        embeddings_list = [vec / np.linalg.norm(vec) for vec in embeddings_list]
    
    embedding_dim = len(embeddings_list[0]) if embeddings_list else 0
    
    if index_type == "ip":
        faiss_index = faiss.IndexFlatIP(embedding_dim)
    else:
        faiss_index = faiss.IndexFlatL2(embedding_dim)

    embeddings_np = np.array(embeddings_list, dtype=np.float32)
    faiss_index.add(embeddings_np)

    docstore = InMemoryDocstore(
        {f"doc_{i}": doc for i, doc in enumerate(documents)}
    )
    index_to_docstore_id = {i: f"doc_{i}" for i in range(len(documents))}

    return FAISS(
        index=faiss_index,
        embedding_function=embeddings.embed_query,
        docstore=docstore,
        index_to_docstore_id=index_to_docstore_id
    )

# 修改发送数据库请求部分（异步化 + 取消检查）
async def send_review_result(data_to_send: dict):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url='http://172.17.100.214:85/gzszy-api/web/review/task/item/save',
                headers={
                        'Content-Type': 'application/json',
                        'App-Id': 'f5731af3-0352-4790-b671-2617e07f54bc'
                },
                json=data_to_send
            ) as response:
                # 检查是否已被取消
                await asyncio.sleep(0)  # 协作点
                    
                if response.status == 200:
                    logger.info(f"成功将审查项结果写入数据库")
                
                else:
                    logger.error(f"数据库写入失败，状态码: {response.status}")
                        
                return await response.json()
                    
    except asyncio.CancelledError:
        logger.warning("数据库写入请求被取消")
        raise
    
    except Exception as e:
        logger.error(f"数据库请求异常: {str(e)}")    
    
async def send_error_message(task_id, error_msg):
    """异步发送错误消息"""
    try:
        async with aiohttp.ClientSession() as session:
            url = "http://172.17.100.214:85/gzszy-api/web/review/task/msg"
            headers = {
                    'Content-Type': 'application/json',
                    'App-Id': 'f5731af3-0352-4790-b671-2617e07f54bc'
            }
            data = {"taskId": task_id, "errMsg": error_msg}
                
            async with session.post(url, headers=headers, json=data) as response:
                    
                if response.status != 200:
                    logger.error(f"错误消息发送失败: {await response.text()}")
                    
                logger.info(f"成功发送错误消息")
        
    except Exception as e:
        logger.error(f"发送错误消息时发生异常: {str(e)}")    

# 定义单个审查项处理过程的函数
async def process_single_review_item(semaphore, modelName, projectId, stageId, fileId, taskId,topK,review_item, idx,
                                     texts_with_metadata,reviewItemArray,vectorstore,total_tasks, completion_queue,similarityThreshold,workers
                                     ):
    
    ENCODING = tiktoken.get_encoding("cl100k_base")

    async def tokenize_length(text: str) -> int:
        
        """
        计算文本的token长度，确保输入为有效字符串
        
        Args:
            text: 需要计算长度的文本内容
            
        Returns:
            token数量
        
        """
        
        if not isinstance(text, str):
            logger.warning(f"Invalid text type: {type(text)}, converting to string")
            text = str(text)
        
        try:
            # 确保输入是字符串且非空
            if not text.strip(): return 0
                
            # 使用tokenizer的encode方法获取token长度
            return len(embeddings.client.tokenizer.encode(text))
        
        except Exception as e:
            logger.error(f"Tokenize error: {str(e)}, text sample: {text[:50]}...")
            return 0  # 出错时返回安全值

    async def extract_messages_content(messages):
        """提取 messages 中所有 content 字段内容"""
        content_list = []
        for message in messages:
            if "content" in message:
                content_list.append(message["content"])
        return content_list

    async def calculate_messages_token_length(messages):
        """计算 messages 的总 token 数量"""
        content_list = await extract_messages_content(messages)
        total_length = 0

        for content in content_list:
            total_length += await tokenize_length(content)
        
        # 添加系统开销（每条消息大约 4-7 tokens）
        system_overhead = len(messages) * 5
        return total_length + system_overhead

    async def tokenize_length_ENCODING(text: str) -> int:
        return len(ENCODING.encode(text))

    async def tokenize_get_tokens(text: str) -> list:
        """获取token列表"""
        return ENCODING.encode(text)

    async def detokenize(tokens: list) -> str:
        """将tokens转换回文本"""
        return ENCODING.decode(tokens)
    
    
    await semaphore.acquire() 
    try:
        # async with semaphore:
            # 假设已经有一个函数来加载审查项信息数组
            # 这里我们直接使用传入的 reviewItemArray
            #for idx, review_item in enumerate(reviewItemArray):
            reviewItemId = review_item.get("reviewItemId")
            reviewItemName = review_item.get("reviewItemName")
            #reviewItemContent = review_item.get("reviewItemContent")
            reviewItemPrompt = review_item.get("reviewItemPrompt")
            searchConfig = review_item.get("reviewItemContent_searchConfig")
            kbSearchConfig = review_item.get("kbSearchConfig")
            kbArray = review_item.get("kbArray")
            logger.info(f"Processing review item {reviewItemId}: {reviewItemName}")
            
            # 先消除换行符
            searchConfig = searchConfig.replace('\n', '')
            kbSearchConfig = kbSearchConfig.replace('\n', '')
            # 按中英文分号切分
            searchConfig = re.split(r'[;；]', searchConfig)
            kbSearchConfig = re.split(r'[;；]', kbSearchConfig)
            # 过滤掉空字符串
            searchConfig = [item for item in searchConfig if item]
            kbSearchConfig = [item for item in kbSearchConfig if item]
            
            # logger.info('completed embeddings')
            logger.info("start retrieve") 

            relContent = []
            
            for search_query in searchConfig:
                try:
                    if use_regex_search(search_query):
                        logger.info('---starting regex search---')
                        parser = SearchQueryParser(search_query)
                        tokens = parser.parse()
                        query_words = []
                        for token_type, value in tokens:
                            if token_type == 'TOKEN' or token_type == 'QUOTE_TOKEN':
                                query_words.append(value)
                            
                        query_embed = embeddings.embed_query(text=search_query)
                        result = vectorstore.similarity_search_with_score_by_vector(
                            embedding=query_embed, 
                            k=topK
                        )

                        # 在结果重排序部分修改：
                        if result:
                            result_with_scores = []
                            for doc, score in result:
                                #logger.info(f'doc is:{doc}')
                                #logger.info(f'score is:{score}')
                                doc_content = doc.page_content.lower()
                                hit_count = sum(1 for word in query_words if word in doc_content)
                                #logger.info(f'hit count:{hit_count}')
                                # 调整权重（示例：FAISS分数占60%，关键词命中占40%）
                                adjusted_score = 0.6 * score + 0.4 * hit_count
                                result_with_scores.append((doc, score, adjusted_score))
                            
                            result_with_scores.sort(key=lambda x: x[2], reverse=True)
                            #logger.info(f'result_with_scores:{result_with_scores}')
                            result_with_scores = result_with_scores[:topK]
                            
                            result = [(doc, score) for doc, score, _ in result_with_scores] 
                            for i in range(len(result)):
                                relContent.append(result[i])            
                        
                    else:
                        
                        logger.info('---starting faiss search---')
                
                        plain_query_words = re.findall(r'\w+', search_query.lower())
                        logger.info(f'plain_query_words:{plain_query_words}')
                    
                        segmented_query_words = []
                        
                        for word in plain_query_words:
                            segmented_query_words.extend(jieba.lcut(word))
                            segmented_query_words.append(word)
                        
                        segmented_query_words = list(set(segmented_query_words))
                        
                        logger.info(f'segmented_query_words:{segmented_query_words}')
                            
                        query_embed = embeddings.embed_query(text=search_query)
                        result = vectorstore.similarity_search_with_score_by_vector(
                            embedding=query_embed, 
                            k=len(texts_with_metadata)
                        )

                        # 在结果重排序部分修改：
                        if result:
                            #query_keywords = set(jieba.lcut(search_query.lower()))
                            #query_keywords = set(re.findall(r'\w+', search_query.lower()))
                            #logger.info(f'query_keywords:{query_keywords}')
                            result_with_scores = []
                            for doc, score in result:
                                #logger.info(f'doc is:{doc}')
                                #logger.info(f'score is:{score}')
                                doc_content = doc.page_content.lower()
                                hit_count = sum(1 for word in segmented_query_words if word in doc_content)
                                #logger.info(f'hit count:{hit_count}')
                                # 调整权重（示例：FAISS分数占60%，关键词命中占40%）
                                adjusted_score = 0.6 * score + 0.4 * hit_count
                                result_with_scores.append((doc, score, adjusted_score))
                            
                            result_with_scores.sort(key=lambda x: x[2], reverse=True)
                            #logger.info(f'result_with_scores:{result_with_scores}')
                            result_with_scores = result_with_scores[:topK]
                            
                            result = [(doc, score) for doc, score, _ in result_with_scores] 
                            for i in range(len(result)):
                                relContent.append(result[i])
                                    
                except Exception as e:
                    logger.error(f"检索失败（query={search_query}）: {str(e)}")
                    await send_error_message(taskId,f"检索失败（query={search_query}）: {str(e)}")
            
            trun_relContent = relContent
            trun_relContent = [doc[0].page_content for doc in trun_relContent]
            trun_relContent = list(dict.fromkeys(trun_relContent))
            #logger.info(f'trun_relcontent:{trun_relContent}') 
                
            relContent = sort_results_by_page(relContent)
            relContent = [doc[0].page_content for doc in relContent]
            relContent = list(dict.fromkeys(relContent))
                
            #logger.info(f"检索到的报告内容部分：{relContent}")
            #logger.info(f"检索到的报告内容部分长度：{len(relContent)}")

            
            relArray=[]
            
            if kbArray :
                
                # 检索逻辑
                kb_result = []
                for kbsearch_query in kbSearchConfig:
                    source = retrieval(kbId=kbArray,query=kbsearch_query,limit=topK,similarityThreshold=similarityThreshold,workers=workers)
                    
                    # 判断是否存在files字段
                    if 'files' not in source:
                        logger.error(f"{source['message']}")
                        await send_error_message(taskId,f"{source['message']}")
                    
                    result = source['files'] if source and 'files' in source else [] 
                    kb_result.append(result)
                
                # 去重逻辑
                unique_kb_result = []
                seen_contents = set()
                
                for sub_list in kb_result:
                    new_sub_list = []
                    
                    for item in sub_list:
                        content = item.get('content', '')
                        
                        if content not in seen_contents:
                            new_sub_list.append(item)
                            seen_contents.add(content)
                
                    unique_kb_result.append(new_sub_list)
                relArray.append(unique_kb_result)
            
            #logger.info(f'检索到的知识库内容:{relArray}')

            json_format = { 
                "reviewItemState": "0：审查通过，1：审查未通过,2：无法确认,此字段只输出数字",
                "reviewConclusion": "审查项审查结论描述,需完整呈现审查判断流程，从审查依据的引用（具体数值、条款等）开始，详细说明对待审查项审查的分析过程，包括数值比对、条款符合情况判断等，越详细越好，逐步推导至最终结论。过程中禁止生成特殊字符（如>、\"、\\、/、[ ]等）、格式标记（如 Markdown、HTML）或转义符号,尤其是所有字符串字段中的双引号，若必须要输出则需要\转义。若有分条描述,统一在单一字段内用中文句号分隔，不使用编号或项目符号。"
            }

            # 单纯用于计算token数量，不进行模型调用
            cal_messages = [
                {
                    "role": "system",
                    "content": "你是一名专业的水利科学院文档智能合规审查员，具备丰富的水资源论证报告审查经验。你的任务是对提交的水资源论证报告进行严格的合规性检查，必须严格按照指定的JSON格式输出，禁止添加任何额外内容或格式。审查结论需完整、详细地呈现审查判断流程，越详细越好，确保能通过结论清晰了解审查的依据和推理过程。"
                },
                {
                    "role": "user",
                    "content": f'''以下是进行水资源论证报告合规审查提供的信息：        
                    【审查项名称】: {reviewItemName}
                    【审查项要求】: {reviewItemPrompt}
                    【待审查文件内容】:{""}
                    【参考知识库内容】:{""}
                    请依据提供的参考知识库内容，针对待审查文件内容按照审查项要求进行合规性审查，并严格以JSON格式返回审查结果,
                    JSON格式如下: {json_format}
                    ''' 
        }
    ]      
            prompt_token_length = await  calculate_messages_token_length(cal_messages) # 已使用token数

            unuse_token_length = 57344 - prompt_token_length - 2000

            logger.info(f"prompt_token_length:{prompt_token_length}, unuse_token_length:{unuse_token_length}")
            
            # 计算可分配的token长度
            if len(trun_relContent) == 0 and len(relArray) != 0:
                relContent_max_tokens = 0
                relArray_max_tokens = unuse_token_length    # 100%给知识库内容
            
            elif len(trun_relContent) != 0 and len(relArray) == 0:
                relContent_max_tokens = unuse_token_length  # 100%给报告内容
                relArray_max_tokens = 0
            
            else:
                relContent_max_tokens = int(unuse_token_length * 0.6)  # 60%给报告内容
                relArray_max_tokens = int(unuse_token_length * 0.4)    # 40%给知识库内容

            # 1. 截断待审查文件内容 (relContent)
            truncated_relContent = []

            # 确保trun_relContent是字符串列表
            if trun_relContent and isinstance(trun_relContent[0], list):
                logger.warning(f"Unexpected nested list in trun_relContent: {trun_relContent}")
                trun_relContent = [item for sublist in trun_relContent for item in sublist]

            # logger.info(f"this_is_trun_relContent:{trun_relContent}")
            
            # 合并所有文本块
            if not trun_relContent: 
                full_text = ""
            else: 
                full_text = "\n".join(trun_relContent) if isinstance(trun_relContent[0], str) else "\n".join(str(item) for item in trun_relContent)
            
            # 修改后的truncated_relContent截断逻辑
            tokens = await tokenize_get_tokens(full_text)
            
            if len(tokens) <= relContent_max_tokens: 
                truncated_tokens = tokens
            else:
                truncated_tokens = tokens[:relContent_max_tokens]

            truncated_relContent = await detokenize(truncated_tokens)

            token_len = await tokenize_length_ENCODING(truncated_relContent)
            logger.info(f"truncated_relContent:{token_len}")

            # 2. 截断知识库内容 (relArray)
            truncated_relArray = []

            # 处理relArray为空列表的情况
            if not relArray:
                full1_text = ""
                logger.info("relArray is empty, skipping tokenization")
            else:
                full1_text = "\n".join(relArray) if isinstance(relArray[0], str) else "\n".join(str(item) for item in relArray)

            # 只有当full1_text不为空时才进行tokenization和截断
            if full1_text:
                tokens1 = await tokenize_get_tokens(full1_text)
                truncated_tokens1 = tokens1[:relArray_max_tokens]
                truncated_relArray = await detokenize(truncated_tokens1)
                
                token_len1 = await tokenize_length_ENCODING(truncated_relArray)
                logger.info(f"truncated_relArray:{token_len1}")
            else:
                logger.info("truncated_relArray: 0")
                
            messages = [
                {
                    "role": "system",
                    "content": "你是一名专业的水利科学院文档智能合规审查员，具备丰富的水资源论证报告审查经验。你的任务是对提交的水资源论证报告进行严格的合规性检查，必须严格按照指定的JSON格式输出，禁止添加任何额外内容或格式。审查结论需完整、详细地呈现审查判断流程，越详细越好，确保能通过结论清晰了解审查的依据和推理过程。"
                },
                {
                    "role": "user",
                    "content": f'''以下是进行水资源论证报告合规审查提供的信息：        
                    【审查项名称】: {reviewItemName}
                    【审查项要求】: {reviewItemPrompt}
                    【待审查文件内容】:{truncated_relContent}
                    【参考知识库内容】:{truncated_relArray}
                    请依据提供的参考知识库内容，针对待审查文件内容按照审查项要求进行合规性审查，并严格以JSON格式返回审查结果,
                    JSON格式如下: {json_format}
                    ''' 
                }
            ]      
            
            #logger.info(f'prompt is:{messages}')
            logger.info(f'-----use_model is: {modelName}-----')
            response_flag = False
            errorCode = 0
            if modelName == 'deepseek-r1':
                
                try:
                    response = ""
                    completion = await client.chat.completions.create(
                        model=modelName,  # 您可以按需更换为其它深度思考模型
                        messages=messages,
                        stream=True,
                        temperature=0,
                        top_p=0.1,
                        response_format={"type": "json_object"}
                        # stream_options={
                        #     "include_usage": True
                        # },
                    )
                    try:
                        async for chunk in completion:
                            # 添加取消检查点
                            try:
                                await asyncio.sleep(0)  # 协作式调度
                            except asyncio.CancelledError:
                                await completion.aclose()  # 主动关闭流
                                raise
                            
                            if not chunk.choices:continue

                            delta = chunk.choices[0].delta

                            # 收到content，开始进行回复
                            if hasattr(delta, "content") and delta.content:
                                response += delta.content

                    except asyncio.CancelledError:
                        # 显式关闭流
                        await completion.aclose()
                        raise

                    response_flag = True
                    
                except Exception as e:
                    
                    if hasattr(e,"response"):
                        status_code = e.response.status_code
                        if status_code == 400:
                            error_code = e.response.json().get("error").get("code")
                            if error_code == "invalid_parameter_error":
                                errorCode = 1
                            elif error_code == "RequestTimeOut":
                                errorCode = 2
                    
                    logger.error(f"审查项 {reviewItemId} 模型调用失败，错误详情: {str(e)}")
                    await send_error_message(taskId,f"审查项 {reviewItemId} 模型调用失败，错误详情: {str(e)}")
                
            else:
            
                try:
                    response = ""
                    completion = await client.chat.completions.create(
                        model=modelName,  # 您可以按需更换为其它深度思考模型
                        messages=messages,
                        # enable_thinking 参数开启思考过程，QwQ 与 DeepSeek-R1 模型总会进行思考，不支持该参数
                        extra_body={"enable_thinking": True},
                        stream=True,
                        temperature=0,
                        top_p=0.1,
                        response_format={"type": "json_object"}
                        # stream_options={
                        #     "include_usage": True
                        # },
                    )
                    try:
                        async for chunk in completion:
                            # 添加取消检查点
                            try:
                                await asyncio.sleep(0)  # 协作式调度
                            except asyncio.CancelledError:
                                await completion.aclose()  # 主动关闭流
                                raise
                            
                            if not chunk.choices:continue

                            delta = chunk.choices[0].delta

                            # 收到content，开始进行回复
                            if hasattr(delta, "content") and delta.content:
                                response += delta.content
                        
                    except asyncio.CancelledError:
                        # 显式关闭流
                        await completion.aclose()
                        raise

                    response_flag = True
                    
                except Exception as e:
                        
                    logger.error(f"审查项 {reviewItemId} 模型调用失败，错误详情: {str(e)}")
                    await send_error_message(taskId,f"审查项 {reviewItemId} 模型调用失败，错误详情: {str(e)}")
                    #continue
            # ========== 关键修复：通过队列判断最后一个任务 ==========
            current_count = completion_queue.qsize()  # 当前已完成任务数（原子性获取）
            is_last = (current_count + 1 == total_tasks)  # 判断当前任务是否是最后一个
            await completion_queue.put(None)  # 放入一个标记，表示任务完成    
            
            if response_flag:
                
                # 去除 Markdown 标记
                response = response.replace("```json", "").replace("```", "").strip()
                #logger.info(f'response: {response}')
                result_json = json.loads(response)
                
                    
                #logger.info(f"load json : {result_json}")
                #result_json = json.loads(response.message.content)
                #logger.info(f'model answer: {response.message.content}')
                complianceStatus = result_json["reviewItemState"]
                comments = result_json["reviewConclusion"]
                
                #get files:
                files = []
                #for sublist1 in extracted_relArray:
                for sublist1 in relArray:
                    for sublist2 in sublist1:
                        for item in sublist2:
                            file_info = {
                            "fileId": item["fileId"],
                            "relContent": item["content"]
                            }
                            files.append(file_info)
                
                # 构建最终要发送的数据
                data_to_send = {
                    "taskId": taskId,
                    "projectId": projectId,
                    "stageId": stageId,
                    "itemId": reviewItemId,
                    "itemState": str(complianceStatus),
                    "itemResult": comments,
                    "itemContent": '\n\n***\n\n'.join(relContent),
                    "files": files,
                    "finished": is_last
                    #"finished": idx == len(reviewItemArray)-1  
                }
            
            else:
                
                if errorCode == 0:
                    #get files:
                    files = []
                    for sublist1 in relArray:
                        for sublist2 in sublist1:
                            for item in sublist2:
                                file_info = {
                                "fileId": item["fileId"],
                                "relContent": item["content"]
                                }
                                files.append(file_info)
                                
                    # 报错构建最终要发送的数据
                    data_to_send = {
                        "taskId": taskId,
                        "projectId": projectId,
                        "stageId": stageId,
                        "itemId": reviewItemId,
                        "itemState": '2',
                        "itemResult": 'AI审查出现错误，请联系系统维护单位',
                        "itemContent": '\n\n***\n\n'.join(relContent),
                        "files": files,
                        "finished": is_last
                        #"finished": idx == len(reviewItemArray)-1    
                    }    
                
                elif errorCode == 1:
                    #get files:
                    files = []
                    for sublist1 in relArray:
                        for sublist2 in sublist1:
                            for item in sublist2:
                                file_info = {
                                "fileId": item["fileId"],
                                "relContent": item["content"]
                                }
                                files.append(file_info)
                                
                    # 报错构建最终要发送的数据
                    data_to_send = {
                        "taskId": taskId,
                        "projectId": projectId,
                        "stageId": stageId,
                        "itemId": reviewItemId,
                        "itemState": '2',
                        "itemResult": 'AI审查出现上下文超长，请联系系统维护单位',
                        "itemContent": '\n\n***\n\n'.join(relContent),
                        "files": files,
                        "finished": is_last
                        #"finished": idx == len(reviewItemArray)-1    
                    }
                
                elif errorCode == 2:
                    #get files:
                    files = []
                    for sublist1 in relArray:
                        for sublist2 in sublist1:
                            for item in sublist2:
                                file_info = {
                                "fileId": item["fileId"],
                                "relContent": item["content"]
                                }
                                files.append(file_info)
                                
                    # 报错构建最终要发送的数据
                    data_to_send = {
                        "taskId": taskId,
                        "projectId": projectId,
                        "stageId": stageId,
                        "itemId": reviewItemId,
                        "itemState": '2',
                        "itemResult": 'AI审查出现请求超时，请联系系统维护单位',
                        "itemContent": '\n\n***\n\n'.join(relContent),
                        "files": files,
                        "finished": is_last
                        #"finished": idx == len(reviewItemArray)-1    
                    }        
            
            logger.info(f'data is ready to send : {data_to_send}')
           
            
            try:
                # 替换原有的同步 requests.post 为异步调用
                await send_review_result(data_to_send)
            except asyncio.CancelledError:
                logger.warning("取消信号已传播至数据库写入阶段")
                await send_error_message(taskId,"取消数据库写入阶段")
                raise
    
    except asyncio.CancelledError:
        logger.warning(f"审查项 {reviewItemId} 被取消")
        await send_error_message(taskId,f"审查项 {reviewItemId} 被取消")
        raise
    
    except Exception as e:
        logger.error(f"审查项处理过程中发生未知错误: {str(e)}")
        await send_error_message(taskId, f"审查项处理失败: {str(e)}")
        raise
    
    finally:
        semaphore.release()  # 确保信号量释放
        
              
# 定义审查指标处理过程的函数
async def process_review_indicators(modelName: str,projectId: str, stageId: str, fileId: str, taskId: str, topK: int ,reviewItemArray: list, concurrency: int = 3,similarityThreshold:float = 0.1,workers:int = 10):
    
    async def task_wrapper():

        try:
            logger.info(f"开始进行指标审查,审查项目id为:{projectId}, task: {taskId}")
            logger.info("开始加载待审查报告")
            
            total_tasks = len(reviewItemArray)  # 总任务数
            completion_queue = asyncio.Queue(maxsize=total_tasks)  # 使用队列作为计数器（原子性保证）
            
            # 读取当前待审查报告的页码表
            metadata_file_path = os.path.join('review_report', projectId, fileId, 'split_result.json')
            page_metadata = load_page_metadata(metadata_file_path)
            #加载文件夹中的所有Markdown文件
            # loader = DirectoryLoader(os.path.join('review_report',projectId,fileId), glob='**/*.md', loader_cls=UnstructuredMarkdownLoader)
            loader = DirectoryLoader(
                os.path.join('review_report',projectId,fileId),
                glob='**/*.md',
                loader_cls=TextLoader  # 使用原始文本加载器 
            )
            
            documents = loader.load()
            
            def clean_chinese_spaces(content):
                # 仅匹配中文字符之间「仅包含半角空格或全角空格」的连续空白
                # (?<=[\u4e00-\u9fa5]) 正向回顾断言：确保左侧是中文字符
                # ([\x20\u3000]+) 匹配一个或多个半角空格（\x20）或全角空格（\u3000）
                # (?=[\u4e00-\u9fa5]) 正向展望断言：确保右侧是中文字符
                return re.sub(r'(?<=[\u4e00-\u9fa5])([\x20\u3000]+)(?=[\u4e00-\u9fa5])', '', content)

            cleaned_documents = []
            for doc in documents:
                cleaned_content = clean_chinese_spaces(doc.page_content)
                cleaned_doc = Document(page_content=cleaned_content, metadata=doc.metadata)
                cleaned_documents.append(cleaned_doc)
            
            doc_contents = [doc.page_content for doc in cleaned_documents]
            
            # 调用 process_markdown_file 进行文本切块
            chunks_sum = process_markdown_file(documents=doc_contents, max_chunk_size=4500, chunk_overlap=0)

            # 将切块结果转换为 Document 对象列表
            texts = []
            for i, chunks in enumerate(chunks_sum):
                metadata = documents[i].metadata.copy() if documents else {}
                for item in chunks:
                    texts.append(Document(page_content=item, metadata=metadata))

            # 添加页面元数据
            texts_with_metadata = add_page_metadata(texts, page_metadata)

            #########################################################################################################

            #创建嵌入模型实例
            #embeddings = HuggingFaceEmbeddings(model_name=embedding_model_path)
            
            logger.info("start create vectorstore")    
            #将文本向量化并存储在FAISS中
            #vectorstore = FAISS.from_documents(texts,embeddings)
            
            # 将文本向量化并存储在FAISS中，同时存储元数据
            documents = []
            for text in texts_with_metadata:
                if isinstance(text, dict):
                    doc = Document(page_content=text["page_content"], metadata=text["metadata"])
                else:
                    doc = text
                documents.append(doc) 
                
            vectorstore = build_faiss_vectorstore(
                documents=documents,
                embeddings=embeddings,
                index_type="ip"
            )
            
            semaphore = asyncio.Semaphore(concurrency)
            tasks = [
                process_single_review_item(semaphore, modelName, projectId, stageId, fileId, taskId, topK,review_item, idx, texts_with_metadata, reviewItemArray,vectorstore,total_tasks=total_tasks,
                    completion_queue=completion_queue,
                    similarityThreshold=similarityThreshold,workers=workers
                    )
                for idx, review_item in enumerate(reviewItemArray)
            ]
            
            await asyncio.gather(*tasks)
            
            logger.info(f"完成项目 {projectId} 的审查指标处理，任务ID: {taskId}")

        except asyncio.CancelledError: 
            logger.warning(f"任务 {taskId} 被强制取消")
            if 'vectorstore' in locals():
                del vectorstore
                torch.cuda.empty_cache()

        except Exception as e:
            logger.error(f"审查处理过程中发生未知错误: {str(e)}")
            await send_error_message(taskId, f"审查处理失败: {str(e)}")
            raise
        
    async with task_lock:
        task = asyncio.create_task(task_wrapper())
        running_tasks[(projectId, taskId)] = task
    
    logger.info('start-------')
    await task
    logger.info('finished-----')
    if 'vectorstore' in locals():
        logger.info('----delete vectorstore-----')
        del vectorstore
        torch.cuda.empty_cache()
    
# 全局任务存储（线程安全版）
running_tasks = {}
task_lock = asyncio.Lock()

@router.post("/stop_review_task/")
async def stop_review_task(taskId: str = Body("test", description="审查任务id"),
                           projectId: str = Body("test", description="唯一标志此项目的键值"),):
    """
    功能：
    1. 查找正在运行的任务
    2. 直接取消任务
    3. 不更新数据库
    """
    
    async with task_lock:
        task_key = (projectId, taskId)
        task = running_tasks.get(task_key)

        if not task:
            return {
                "code": 404,
                "message": f"任务 {taskId} 不存在或已完成"
            }
        logger.info('-----del task----')
        
        logger.info('---cancel task---')
        try:
            # 取消任务
            task.cancel() 
        except asyncio.CancelledError: 
            #logger.info('del2222')
            pass
        logger.info('----successfully del')
        # 清理记录
        del running_tasks[task_key]
        logger.info('================')
    
    return {
        "code": 200,
        "message": f"任务 {taskId} 已终止"
    }
