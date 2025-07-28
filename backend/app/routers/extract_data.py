from fastapi import APIRouter, Body
from app.core.config import get_logger
from typing import Optional
import json
from openai import OpenAI
import re
from fastapi import APIRouter,Body
import os
from langchain.document_loaders import DirectoryLoader
from langchain.document_loaders  import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from openai import OpenAI
from collections import defaultdict
import torch
import jieba

embedding_model_path = "backend/app/models/bge-m3"

'''
功能描述：提取文本中所要求的内容
'''

router = APIRouter()
logger = get_logger(__name__)

client = OpenAI(
    api_key="sk-762b0529add947b081778614c7fe1cda",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)


@router.post("/extract_data/")
def extract_data(
                    projectId: Optional[str] = Body(default=None, description='项目编号'),
                    fileId: Optional[str] = Body(default=None, description='文件编号,与文段内容二选一'),
                    content: Optional[str] = Body(None, description='文段内容,与文件编号二选一'),
                    extractConfig: list = Body(None, description='提取的配置'),
                    searchConfig: Optional[str] = Body(default=None, description='查询字配置，能够包含多个查询项，各个查询项需用中/英文分号分隔。通过此配置定位报告的知识块，有这个配置时必须给文件编号'),
                    prompt: Optional[str] = Body(None, description='大模型提取可配置的提示词')
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
            loader = DirectoryLoader(
            os.path.join('review_report',projectId,fileId),
            glob='**/*.md',
            loader_cls=TextLoader  # 使用原始文本加载器 
            )
        
            documents = loader.load()
        
            # 切分文档
            #text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000,chunk_overlap=200)
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
        
            texts =text_splitter.split_documents(documents)
        
            #创建嵌入模型实例
            embeddings = HuggingFaceEmbeddings(model_name=embedding_model_path)
            
            logger.info("start faiss")    
            #将文本向量化并存储在FAISS中
            vectorstore = FAISS.from_documents(texts,embeddings)

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
                #words = jieba.lcut_for_search(text.page_content.lower())
                words = jieba.lcut(text.page_content.lower())
                for word in words:
                    jieba_inverted_index[word].add(i)
            
            relContent = []
            
            for search_query in searchConfig:
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
                        result = candidate_vectorstore.similarity_search_with_score_by_vector(embedding=query_embed, k=top_k)

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
            
            relContent = list(dict.fromkeys(relContent))
            input = "\n".join(relContent)
            
            # logger.info(f"检索到的报告内容部分：{relContent}")
            # logger.info(f"检索到的报告内容部分长度：{len(relContent)}")
            logger.info(input)
        
        else :
            return {
            "code": 400,
            "message": "fileId已传入，但是未传入searchConfig"
            }
    
    elif content != None:
        input = content
        
    # prompt = prompt.format(input=input, extractConfig=extractConfig)
    
    results = []
    fields = ", ".join([config["name"] for config in extractConfig])

    # 构建 json_format
    json_format = {config["name"]: ['提取出来的要求项'] for config in extractConfig}

    json_format_many = {config["name"]: ["提取出来的要求项1","提取出来的要求项2","提取出来的要求项3"] for config in extractConfig}

    messages = [
        {
            'role': 'system',
            'content': '你现在的身份是水利科学院文档信息提取大模型。擅长对所要求的内容进行提取。'
        },
        {
            'role': 'user',
            'content': f'''文本内容如下：{input}
                            要求：
                            1. 需要提取的字段包括：{fields}
                            2. 如果字段不存在，值设为null;
                            3. 保持原始数据格式不变；
                            4. 严格以JSON格式返回审查结果。JSON格式如下：{json_format}；若提取出来内容项有多个则按照下面的JSON格式：{json_format_many}
                            5. 严格按照文本内容进行输出，禁止一切扩展说明
                            6. 严格根据提取字段寻找所需内容
                            同时也需满足以下用户提取要求：{prompt}
            '''
        },
    ]



    response = client.chat.completions.create(
        model='qwen-max-latest',
        messages=messages,
        stream=False,
        temperature=0.0,
        response_format={"type": "json_object"}
    )
    full_content = response.choices[0].message.content
    logger.info(full_content)

    try:
        result = json.loads(full_content)
    except json.JSONDecodeError as e:
        logger.error(f"JSON 解码错误: {e}")
        return {
            "code": 500,
            "message": "JSON 解码错误"
        }

    # 构建最终的响应
    results = []
    for config in extractConfig:
        results.append({
            "id": config["id"],
            "name": config["name"],
            "result": result.get(config["name"], None)
        })

    return {
        "code": 200,
        "message": "调用提取接口成功,已输出提取结果",
        "results": results
    }
    

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