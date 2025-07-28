from fastapi import APIRouter, Request,Body,Response
from app.core.config import get_logger
from fastapi import FastAPI
from sse_starlette.sse import EventSourceResponse
from typing import Optional
from routers.knowledge_inter import retrieval
import json

from openai import OpenAI,AsyncOpenAI
import aiohttp
import requests
import re


import subprocess
from fastapi import APIRouter, Request,Body,Response,UploadFile,File,HTTPException
from pypdf import PdfReader, PdfWriter
from app.core.config import get_logger
import json
import tempfile
import os
import shutil
from concurrent.futures import ThreadPoolExecutor
from docx2pdf import convert
from concurrent.futures  import as_completed
from datetime import datetime
import requests
import sys
from fuzzywuzzy import fuzz
#from ollama import chat
#from ollama import AsyncClient
import requests
from langchain.document_loaders import DirectoryLoader,UnstructuredMarkdownLoader
from langchain.document_loaders  import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from routers.knowledge_inter import retrieval
from openai import OpenAI
import aiohttp
from openai import AsyncOpenAI
from collections import defaultdict
import torch
import jieba




'''
功能描述：
'''

router = APIRouter()
logger = get_logger(__name__)

client = OpenAI(
    api_key="sk-762b0529add947b081778614c7fe1cda",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)

embedding_model_path = "backend/app/models/bge-m3"

@router.post("/document_classify/")
def document_classify(fileId: Optional[str] = Body(default=None,description='文件编号,与文段内容二选一'),
                            projectId: Optional[str] = Body(default=None, description='项目编号'),
                            content: Optional[str] = Body(None,description='文段内容,与文件编号二选一'),
                            classifyConfig: list = Body(None,description='分类的配置'),
                            searchConfig: Optional[str] = Body(default=None,description='查询字配置，能够包含多个查询项，各个查询项需用中/英文分号分隔。通过此配置定位报告的知识块，有这个配置时必须给文件编号'),
                            prompt: Optional[str] = Body(None,description='大模型分类可配置的提示词')
                            ):
    
    
    input = ''
    
    if (fileId == None and content == None) or (fileId and content):
        return {
            "code": 400,
            "message": "fileId，content中请选择传入一个参数"
        }
    
    if fileId != None:
        if searchConfig:
            # 先消除换行符
            searchConfig = searchConfig.replace('\n', '')
            
            # 按中英文分号切分
            searchConfig = re.split(r'[;；]', searchConfig)
            
            # 过滤掉空字符串
            searchConfig = [item for item in searchConfig if item]
            
            res = ""
            ######################################################################################################################################milvus改成FAISS
            loader = DirectoryLoader(
                os.path.join('review_report', projectId, fileId),
                glob='**/*.md',
                loader_cls=TextLoader  # 使用原始文本加载器
            )

            documents = loader.load()

            # 切分文档
            # text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000,chunk_overlap=200)
            text_splitter = RecursiveCharacterTextSplitter(
                # 每个文本块最大字符数，根据文件具体情况调整
                chunk_size=8000,
                # 相邻文本块重叠字符数
                chunk_overlap=200,
                # 分隔符列表，按照优先级排列
                separators=["\n# ", "\n## ", "\n### ", "\n#### "],
                # 保留分隔符
                keep_separator=True
            )

            texts = text_splitter.split_documents(documents)

            # 创建嵌入模型实例
            embeddings = HuggingFaceEmbeddings(model_name=embedding_model_path)

            logger.info("start faiss")
            # 将文本向量化并存储在FAISS中
            vectorstore = FAISS.from_documents(texts, embeddings)

            # logger.info('completed embeddings')

            # 构建普通倒排索引（使用正则匹配单词）
            plain_inverted_index = defaultdict(set)
            for i, text in enumerate(texts):
                words = re.findall(r'\w+', text.page_content.lower())
                for word in words:
                    plain_inverted_index[word].add(i)

            # 构建使用jieba的倒排索引
            jieba_inverted_index = defaultdict(set)
            for i, text in enumerate(texts):
                # 使用jieba进行中文分词
                # words = jieba.lcut_for_search(text.page_content.lower())
                words = jieba.lcut(text.page_content.lower())
                for word in words:
                    jieba_inverted_index[word].add(i)

            relContent = []
            for index,search_query in enumerate(searchConfig):
                try:
                    if len(search_query) > 120:
                        return {"code": "400", "message": "检索内容超过120字符限制"}

                    if use_regex_search(search_query):
                        logger.info('---starting regex search---')
                        # 提取查询词
                        parser = SearchQueryParser(search_query)
                        tokens = parser.parse()
                        query_words = []
                        for token_type, value in tokens:
                            if token_type == 'TOKEN' or token_type == 'QUOTE_TOKEN':
                                query_words.append(value)

                        # 普通倒排索引查询预处理
                        plain_query_words = [word.lower() for word in query_words]
                        # jieba倒排索引查询预处理
                        segmented_query_words = []
                        for word in query_words:
                            segmented_query_words.extend(jieba.lcut(word))

                        # 先通过普通倒排索引查找候选文档
                        candidate_indices = set()
                        for word in plain_query_words:
                            if word in plain_inverted_index:
                                candidate_indices.update(plain_inverted_index[word])

                        if not candidate_indices:
                            # 若普通倒排索引未找到候选文档，使用jieba倒排索引查找
                            for word in segmented_query_words:
                                if word in jieba_inverted_index:
                                    candidate_indices.update(jieba_inverted_index[word])

                        if candidate_indices:
                            candidate_texts = [texts[i] for i in candidate_indices]
                            candidate_vectorstore = FAISS.from_documents(candidate_texts, embeddings)
                            logger.info('-----has an candidate_indices-----')
                        else:
                            candidate_vectorstore = vectorstore
                            logger.info('-----no candidate_indices-----')

                        # 设置检索待审查文档的前top_k个文档数
                        top_k = 3

                        # 查询文本向量化
                        query_embed = embeddings.embed_query(text=search_query)

                        # 相似查询
                        result = candidate_vectorstore.similarity_search_with_score_by_vector(embedding=query_embed,k=top_k)

                        # 释放不再使用的candidate_vectorstore
                        if 'candidate_vectorstore' in locals():
                            logger.info('----delete vectorstore-----')
                            del candidate_vectorstore
                            torch.cuda.empty_cache()

                        if result:
                            for i in range(len(result)):
                                relContent.append(result[i][0].page_content)
                    else:
                        logger.info('---starting faiss search---')
                        # 提取查询词
                        # 普通倒排索引查询预处理
                        plain_query_words = re.findall(r'\w+', search_query.lower())
                        # logger.info(f"plain_query_words:{plain_query_words}")

                        # jieba倒排索引查询预处理
                        # 使用正则表达式按多种分隔符分割并去重
                        query_words = list(set(re.split(r'[_\-]', search_query)))
                        query_words = [word for word in query_words if word]
                        # logger.info(f"query_words:{query_words}")

                        segmented_query_words = []
                        for word in query_words:
                            segmented_query_words.extend(jieba.lcut(word))
                        # logger.info(f"segmented_query_words:{segmented_query_words}")

                        # 先通过普通倒排索引查找候选文档
                        candidate_indices = set()
                        for word in plain_query_words:
                            if word in plain_inverted_index:
                                candidate_indices.update(plain_inverted_index[word])

                        if not candidate_indices:
                            # 若普通倒排索引未找到候选文档，使用jieba倒排索引查找
                            for word in segmented_query_words:
                                if word in jieba_inverted_index:
                                    candidate_indices.update(jieba_inverted_index[word])

                        if candidate_indices:
                            candidate_texts = [texts[i] for i in candidate_indices]
                            candidate_vectorstore = FAISS.from_documents(candidate_texts, embeddings)
                            logger.info('-----has an candidate_indices-----')
                        else:
                            candidate_vectorstore = vectorstore
                            logger.info('-----no candidate_indices-----')

                        # 设置检索待审查文档的前top_k个文档数
                        top_k = 3

                        # 查询文本向量化
                        query_embed = embeddings.embed_query(text=search_query)

                        # logger.info(f"completed text embedding:{query_embed}")

                        # 相似查询
                        result = candidate_vectorstore.similarity_search_with_score_by_vector(embedding=query_embed, k=top_k)

                        # 释放不再使用的candidate_vectorstore
                        if 'candidate_vectorstore' in locals():
                            logger.info('----delete vectorstore-----')
                            del candidate_vectorstore
                            torch.cuda.empty_cache()

                    if result:
                        for i in range(len(result)):
                            relContent.append(result[i][0].page_content)

                except Exception as e:
                    logger.error(f"检索失败（query={search_query}）: {str(e)}")

                relContent_list = list(dict.fromkeys(relContent))
                relContent = "\n".join(relContent_list)
                input = relContent

                logger.info(f"检索到的报告内容部分：{relContent}")
                logger.info(f"检索到的报告内容部分长度：{len(relContent)}")

                # res += retrieval(kbId=fileId, query=q, limit=1)
                # input = res
        
        else:
            return {
            "code": 400,
            "message": "fileId已传入，但是未传入searchConfig"
        }

    elif content != None:
        input = content
    
    # prompt = prompt.format(input=input, classifyConfig=classifyConfig)
    json_example=[
            {
            "id": "1563281",
            "name": "水资源管理类",
            "score": "0.92"
            },
            {
            "id": "1563282",
            "name": "水利工程建设类",
            "score": "0.85"
            },
            {
            "id": "1563283",
            "name": "水生态保护类",
            "score": "0.78"
            }
        ]
    messages = [
            {
                'role': 'system',
                'content': '你现在的身份是水利科学院文档分类大模型,可以依据我提供的分类类别，对我提供的待分类段落/文本块进行分类匹配分数计算。'
            },
            {
            'role': 'user',
            'content': f'''我将给定你待匹配文本块，以及分类的类别及类别对应的编号，请计算文本块在给定类别上的匹配度得分，需要匹配的文本段落和分类类别及其对应的id如下：
            【待匹配文本块】:{input}
            【分类类别信息】:{classifyConfig}
             请给出该文本块与给定分类类别的匹配分数，结果请返回标准的json组数据格式，每个json数据代表一个类，
             包含"id","name","score"三个字段，id的值为classifyConfig中的id，name的值为classifyConfig中的name，score的值为你计算出的对应的匹配度得分，
             返回的数据格式示例如下：{json_example}
             #注意，只返回以上json格式的数据，不要带有其他字段
             同时也需满足以下用户分类要求：{prompt}                         
            '''
            },
            ]
    response = client.chat.completions.create(
                model='qwen-max-latest',
                messages=messages,
                stream=False,
                temperature=0.01,
            )
    #full_content = response.choices[0].message.content
    
    
    #logger.info(full_content)
    # result = extract_json_from_prompt(content = full_content)
    #result=full_content
    #print(result)
    
    full_content = response.choices[0].message.content
    full_content = full_content.replace("'", "\"")

    result = json.loads(full_content)
    
    # 新增：按score降序排序（将字符串转为浮点数排序）
    result = sorted(result, key=lambda x: float(x['score']), reverse=True)
    
    logger.info(f'分类结果：{result}')
    
    return { 
        "code": 200,
        "message": "调用分类接口成功,已输出分类结果",
        "result": result
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


def extract_json_from_prompt(content):
    # 正则表达式模式，用于匹配 JSON 部分
    json_pattern = r'```json\n([\s\S]*?)\n```'
    
    # 查找匹配的部分
    match = re.search(json_pattern, content)
    
    if match:
        json_str = match.group(1).strip()
        try:
            json_data = json.loads(json_str)
            return json_data
        except json.JSONDecodeError as e:
            print(f"JSON 解码错误: {e}")
            return None
    else:
        print("未找到 JSON 部分")
        return None


if __name__=='__main__':
    document_classify(content="受贵州盘江电投发电有限公司委托之后，2023年3月项目承担单位组织相关技术人员成立项目组，在仔细分析项目技术资料的基础上，开展了现场查勘、资料收集，完成了项目工作大纲编制和内审，根据《建设项目水资源论证导则》（GB/T-35580-2017）《火电建设项目水资源论证导则》（SL763-2018）等相关要求，认真分析了盘县电厂的生产工艺流程、用水环节及用水效率，对电厂的取用水方案进行重新核定，本次论证根据区域水资源的特征，通过分析计算取水河段来水量和可供水量，重点论证电厂取水水源的合理性、可靠性和可行性以及电厂取水对区域水资源的可能影响，并经与委托方充分沟通协调后，于2024年8月编制完成了《报告书》（送审稿）。2024年10月，贵州盘江电投发电有限公司向贵州省水利厅报送了《报告书》（送审稿），经初步审核，贵州省水利厅于2024年11月向水利部珠江水利委员会报送了初审意见。2024年11月，珠江水利委员会珠江水利综合技术中心在贵州省盘州市组织开展了《报告书》评审工作，形成专家评审意见。会后，编制单位根据专家评审意见和相关部门代表意见，认真修改完善了报告，完成了《报告书》（报批稿），提交水利部珠江水利委员会。",classifyConfig=[{"id":86591,"name":"增容节能一体化改造项目承担单位与工作过程"},{"id":56725,"name":"水利科学院的水利项目"},{"id":11132,"name":"计算机领域的重点难题"}])