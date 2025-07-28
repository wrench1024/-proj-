from fastapi import FastAPI, APIRouter, Body
from langchain.document_loaders import DirectoryLoader, TextLoader
import os
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from collections import defaultdict
from langchain.embeddings import SentenceTransformerEmbeddings
from sentence_transformers import util
import re
import jieba
import torch
import json
import sys
import faiss
import numpy as np
from langchain.docstore.document import Document
from langchain.docstore.in_memory import InMemoryDocstore
from routers.chunknew0521 import process_markdown_file
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.core.config import get_logger
logger = get_logger(__name__)

app = FastAPI()
router = APIRouter()
embedding_model_path = "backend/app/models/bge-m3"

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
                self.pos += 1
            else:
                start = self.pos
                while self.pos < len(self.query) and self.query[self.pos] not in self.DELIMITERS.union(self.OPERATORS):
                    self.pos += 1
                self.tokens.append(('TOKEN', self.query[start:self.pos]))

    def parse(self):
        return self.tokens


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


def use_regex_search(query: str) -> bool:
    special_chars = r'[-*+()\\\'"]'
    return bool(re.search(special_chars, query))


def load_page_metadata(metadata_file):
    with open(metadata_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def add_page_metadata(texts, page_metadata):
    new_texts = []
    for i, text in enumerate(texts):
        file_path = text.metadata.get('source')
        logger.info(f'-----mdfile_path-----:{file_path}')
        file_name = os.path.basename(file_path)
        file_name = file_name.replace('.md', '.pdf')
        logger.info(f'-----mdfile_name-----:{file_name}')
        if file_name in page_metadata:
            start_page = page_metadata[file_name]['起始页号']
            end_page = page_metadata[file_name]['终止页号']
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
        else:
            logger.info('======存在目录中不存在的解析md文件======')
    return new_texts


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


@router.post("/search/")
async def search(projectId: str = Body("test", description="唯一标志此项目的键值"),
        fileId: str = Body("test", description="待审查的报告id"),
        reviewItemContent_searchConfig: str = Body("",description="查询字段"),
        topK: int = Body(5, description="待审查报告检索的前topK个文本块")):
    try:
        metadata_file_path = os.path.join('review_report', projectId, fileId, 'split_result.json')
        page_metadata = load_page_metadata(metadata_file_path)
        searchConfig = reviewItemContent_searchConfig.replace('\n', '')
        searchConfig = re.split(r'[;；]', searchConfig)
        searchConfig = [item for item in searchConfig if item]

        loader = DirectoryLoader(
                os.path.join('review_report',projectId,fileId),
                glob='**/*.md',
                loader_cls=TextLoader
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
        chunks_sum = process_markdown_file(documents=doc_contents, max_chunk_size=4500,chunk_overlap=0)

        # 将切块结果转换为 Document 对象列表
        texts = []
        for i, chunks in enumerate(chunks_sum):
            metadata = documents[i].metadata.copy() if documents else {}
            for item in chunks:
                texts.append(Document(page_content=item, metadata=metadata))

        texts_with_metadata = add_page_metadata(texts, page_metadata)
            
        #embeddings = HuggingFaceEmbeddings(model_name=embedding_model_path)
        embeddings = SentenceTransformerEmbeddings(model_name=embedding_model_path)
        
        logger.info("start create vectorstore")    
        documents_for_faiss = []
        for text in texts_with_metadata:
            if isinstance(text, dict):
                doc = Document(page_content=text["page_content"], metadata=text["metadata"])
            else:
                doc = text
            documents_for_faiss.append(doc)
        
        vectorstore = build_faiss_vectorstore(
            documents=documents_for_faiss,
            embeddings=embeddings,
            index_type="ip"
        )

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

                    if 'vectorstore' in locals():
                        logger.info('----delete vectorstore-----')
                        del vectorstore
                        torch.cuda.empty_cache()

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

                    if 'vectorstore' in locals():
                        logger.info('----delete vectorstore-----')
                        del vectorstore
                        torch.cuda.empty_cache()

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
            
        relContent = sort_results_by_page(relContent)
        relContent = [doc[0].page_content for doc in relContent]
        relContent = list(dict.fromkeys(relContent))
            
        #logger.info(f"检索到的报告内容部分：{relContent}")
        #logger.info(f"检索到的报告内容部分长度：{len(relContent)}")
        return {"code":200, "message": "检索成功", "relContent": relContent, "len": len(relContent)}
    
    except Exception as e:
        
        return {"code":500, "message": f'检索失败:{str(e)}'}