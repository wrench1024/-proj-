from fastapi import APIRouter,File,UploadFile
from app.core.config import get_logger
import torch
import json
from transformers import AutoTokenizer, AutoModel
from pymilvus.model.reranker import BGERerankFunction
from pymilvus.model.hybrid import BGEM3EmbeddingFunction
from pymilvus import (
    connections,
    utility,
    FieldSchema,
    CollectionSchema,
    DataType,
    Collection,
    MilvusException,
    AnnSearchRequest,
    WeightedRanker,
    RRFRanker,
    Function,
    FunctionType
)
from fastapi import FastAPI,Body,HTTPException
import os
from typing import Optional,List
from docx import Document
import shutil
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from routers.file_mineru import process_pdf_file
#from routers.chunk1 import process_markdown_file
from routers.chunknew0521 import process_markdown_file
from langchain.embeddings.huggingface import HuggingFaceEmbeddings
import requests
import numpy as np
from openai import OpenAI
import fcntl
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor

router = APIRouter()
logger = get_logger(__name__)
client = OpenAI(
    api_key="sk-762b0529add947b081778614c7fe1cda",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)

# 文件存储目录配置
base_dir = "/home/mengshengbo/RegDoc_System/knowledge_base"
os.makedirs(base_dir, exist_ok=True)
collection_mapping_dir = "backend/app/core/collection_mapping.json"
# 准备嵌入模型
# 指定本地模型路径
#model_path = "'app/models/bge-m3"

#md解析路径
output_dir = '/home/mengshengbo/RegDoc_System/file'

#mineru解析url
url = 'http://localhost:7000/parse-files/'
#url = "http://parser:7000/parse-files/"

def generate_embeddings(docs):
    ef = BGEM3EmbeddingFunction(model_name='backend/app/models/bge-m3',use_fp16=False, device="cuda:0")
    if isinstance(docs, str):
        docs = [docs]  # 将字符串转换为列表
    return ef(docs)

#加载或创建知识库映射表
def load_mapping(mapping_path):
    try:
        with open(mapping_path, 'r', encoding='utf-8') as f:
            collection_mapping = json.load(f)
    except FileNotFoundError:
        collection_mapping = {}
    return collection_mapping

#写回并保存知识库映射表
def save_mapping(mapping_path,collection_mapping):
    # 保存映射字典
    with open(mapping_path, 'w', encoding='utf-8') as f:
        json.dump(collection_mapping, f, ensure_ascii=False, indent=4)


# 加载或创建知识库映射表（带锁）
def load_mapping_with_lock(mapping_path):
    """带文件锁的映射表加载"""
    file_obj = open(mapping_path, "r+", encoding='utf-8')  # 保持文件打开
    fcntl.flock(file_obj, fcntl.LOCK_EX)  # 获取排他锁
    try:
        file_obj.seek(0)
        return json.load(file_obj), file_obj  # 返回映射表和保持打开的文件对象
    except json.JSONDecodeError:
        return {}, file_obj

# 保存映射表并释放锁
def save_mapping_and_unlock(file_obj, data):
    """带锁保存并释放"""
    try:
        file_obj.seek(0)
        file_obj.truncate()
        json.dump(data, file_obj, ensure_ascii=False, indent=4)
    finally:
        fcntl.flock(file_obj, fcntl.LOCK_UN)  # 显式解锁
        file_obj.close()  # 关闭文件

"""
def generate_valid_uuid():
    #生成首字符为字母或下划线的 UUID4
    #（由于 UUID4 的首字符本质上是十六进制数字，实际有效字符为 a-f 的小写字母）
    
    while True:
        # 生成标准 UUID4 并转换为字符串（去除连字符）
        uid = uuid.uuid4().hex  # 示例: "f47ac10b58cc4372a5670e02b2c3d479"
        first_char = uid[0]
        
        # 检查首字符是否为字母（a-f 的小写形式）
        if first_char.isalpha():
            return uid  # 合法 UUID
"""

# 连接 Milvus
connections.connect(uri="backend/app/core/milvus.db")


# 定义字段模式
fields = [
        FieldSchema(
            name="pk", dtype=DataType.VARCHAR, is_primary=True, auto_id=True, max_length=100
        ),
        FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535),
        FieldSchema(name="sparse_vector", dtype=DataType.SPARSE_FLOAT_VECTOR),
        FieldSchema(name="dense_vector", dtype=DataType.FLOAT_VECTOR, dim=1024),
        FieldSchema(name="filename", dtype=DataType.VARCHAR, max_length=512),
        FieldSchema(name="fileid", dtype=DataType.VARCHAR, max_length=512),
        FieldSchema(name="chunk_order", dtype=DataType.INT64)  # 新增：分块顺序（整数类型）
    ]

schema = CollectionSchema(fields)


"""创建知识库接口"""
@router.post("/create_knowledge_base")
async def create_knowledge_base(kbId: str = Body(..., embed=True),kbName: str = Body(..., embed=True)):
    logger.info(f"接收到创建知识库请求: {kbName}")
    #载入映射表
    # collection_mapping = load_mapping(collection_mapping_dir)
    collection_mapping, lock_file = load_mapping_with_lock(collection_mapping_dir)
    #首先判断传入知识库名称是否已经在映射表中存在，若存在则报错
    # ---------- 遍历所有值，检查知识库名称是否已存在 ----------
    # 初始化存在标志
    exists = False
    # 遍历所有键值对的值（即每个集合的信息字典）
    for collection_info in collection_mapping.values():
        # 检查值中是否存在 "kbName" 字段，并比对名称
        if collection_info == kbName :
            exists = True
            break

    if exists:
        error_msg = f"知识库映射表 '{kbName}' 已存在"
        logger.warning(error_msg)
        save_mapping_and_unlock(lock_file, collection_mapping)  # 提前解锁
        return {"code": 400, "message": f"知识库 {kbName} 已存在"}

    # ---------- 映射表添加并保存 ----------
    try:

        # 把知识库ID作为知识库名称
        collection_name = "_" + kbId.replace('-', '_')
        # 记录映射关系
        collection_mapping[collection_name] = kbName
        
        # 保存更新后的映射表
        # save_mapping(collection_mapping_dir,collection_mapping)
        save_mapping_and_unlock(lock_file, collection_mapping)
        
        logger.info(f"知识库 '{kbName}' 创建成功，ID: {collection_name}")
    
    except Exception as e:
        logger.error(f"创建知识库失败: {str(e)}", exc_info=True)
        save_mapping_and_unlock(lock_file, collection_mapping) # 解锁
        return {"code": 500, "message": f"内部错误: {str(e)}"}
    
    #开始新建知识库
    Knowledge_base_dir = os.path.join(base_dir, kbName)
    
    
    # 检查本地文件夹或Milvus集合是否存在
    if os.path.exists(Knowledge_base_dir) or utility.has_collection(collection_name):
        return {"code": 400, "message": f"知识库 {kbName} 已存在"}
 

    try:
        # 创建本地对应知识库目录结构
        os.makedirs(Knowledge_base_dir, exist_ok=False)
    except FileExistsError:
        return {"code": 400, "message": f"知识库 {kbName} 文件夹已存在"}
    except Exception as e:
        return {"code": 500, "message": f"创建文件夹失败: {str(e)}"}
    
    
    # 创建Milvus集合
    try:
        col = Collection(collection_name, schema, consistency_level="Strong")
        #index_params = {"index_type": "IVF_FLAT", "metric_type": "COSINE", "params": {"nlist": 16}}
        #col.create_index("vector", index_params)
        #col.load()
        
        sparse_index = {"index_type": "SPARSE_INVERTED_INDEX", "metric_type": "IP","params": {"term_threshold": 1, "top_k": 100} }
        col.create_index("sparse_vector", sparse_index)
        #sparse_index = {"index_type": "SPARSE_INVERTED_INDEX", "metric_type": "BM25"}
        #col.create_index("sparse_bm25", sparse_index)
        dense_index = {"index_type": "IVF_FLAT", "metric_type": "IP","params": {"nlist": 1024, "nprobe": 32}}
        col.create_index("dense_vector", dense_index)
        col.load()
        return {"code": 200, "message": "知识库创建成功"}
    
    except Exception as e:
        # 回滚：删除已创建的文件夹
        try:
            import shutil
            shutil.rmtree(Knowledge_base_dir)
        except Exception as cleanup_error:
            logger.error(f"清理文件夹失败: {cleanup_error}")
            return {"code": 500, "message": f"创建知识库失败: {str(e)}"}



"""更改知识库接口"""
@router.post("/update_knowledge_base")
async def update_knowledge_base(kbId: str = Body(..., embed=True),kbName: str = Body(..., embed=True)):
    
    logger.info(f"接收到修改知识库请求:")

    try:
        # 载入映射表
        # collection_mapping = load_mapping(collection_mapping_dir)
        collection_mapping, lock_file = load_mapping_with_lock(collection_mapping_dir)
        collection_name = "_" + kbId.replace('-', '_')
        logger.info(f"{collection_name}")
        #首先判断所给kbId对应的知识库是否存在
        if not utility.has_collection(collection_name):
            save_mapping_and_unlock(lock_file, collection_mapping) # 提前解锁
            return {"code": 400, "message": f"知识库不存在"}

        #接着对映射表进行修改即可
        # 初始化存在标志
        exists = False
        old_kbName=""
    
        #遍历映射表所有键值对的键
        for key in collection_mapping.keys():
            # 找到对应的位置对其值进行覆盖改写
            if key == collection_name :
                exists = True
                old_kbName = collection_mapping[key]
                collection_mapping[key] = kbName
                break
        # logger.info(f"{collection_mapping}")
        if exists :
            # 更改原知识库存储本地的文件夹名
            old_folder = base_dir + '/' + old_kbName
            new_folder = base_dir + '/' + kbName

            # 使用os.rename()函数进行重命名
            os.rename(old_folder, new_folder)
            # 保存更新后的映射表
            # save_mapping(collection_mapping_dir,collection_mapping)
            save_mapping_and_unlock(lock_file, collection_mapping)
            return {"code": 200, "message": "知识库更改成功"}
        else :
            save_mapping_and_unlock(lock_file, collection_mapping) # 用于解锁
            return {"code": 500, "message": "知识库更改失败"}
    
    except KeyError:
        save_mapping_and_unlock(lock_file, collection_mapping) # 用于解锁
        return {"code": 200, "message": "知识库不存在"}
    
    except Exception as e:
        # 处理其他可能的异常
        save_mapping_and_unlock(lock_file, collection_mapping) # 用于解锁
        return {"code": 500, "message": f"发生未知错误: {str(e)}"}
    


"""删除知识库接口"""
@router.post("/delete_knowledge_base")
async def delete_knowledge_base(kbId: str = Body(..., embed=True)):

    logger.info(f"接收到删除知识库请求:")

    try:
        # 载入映射表
        # collection_mapping = load_mapping(collection_mapping_dir)
        collection_mapping, lock_file = load_mapping_with_lock(collection_mapping_dir)
        collection_name = "_" + kbId.replace('-', '_')
        kbName = collection_mapping[collection_name]
    
    except KeyError:
        save_mapping_and_unlock(lock_file, collection_mapping) # 提前解锁
        return {"code": 200, "message": "知识库不存在"}
    
    except Exception as e:
        # 处理其他可能的异常
        save_mapping_and_unlock(lock_file, collection_mapping) # 提前解锁
        return {"code": 500, "message": f"发生未知错误: {str(e)}"}

    #首先判断所给kbId对应的知识库是否存在
    if not utility.has_collection(collection_name):
        save_mapping_and_unlock(lock_file, collection_mapping) # 提前解锁
        return {"code": 400, "message": f"知识库不存在"}

    #进行删除知识库操作
    try:
        utility.drop_collection(collection_name)
        #Delete_local_directory
        kbName = collection_mapping[collection_name]
        Knowledge_base_dir = os.path.join(base_dir, kbName)
        shutil.rmtree(Knowledge_base_dir)
        collection_mapping.pop(collection_name)
        # save_mapping(collection_mapping_dir,collection_mapping)
        save_mapping_and_unlock(lock_file, collection_mapping)
        return {"code": 200, "message": "知识库删除成功"}

    except Exception as e:
        save_mapping_and_unlock(lock_file, collection_mapping)
        return {"code": 500, "message": f"知识库删除失败: {str(e)}"}


@router.post("/delete_knowledge_base_document")
async def delete_files_from_knowledgebase(kbId: str = Body(..., embed=True), files: list[str] = Body(...)):
    """
    根据上传的 fileid 列表删除指定知识库中的对应实体
    :param kbId: 知识库 ID（Milvus collection 名称）
    :param files: 上传的 fileid 列表
    """
    try:
        # 验证输入参数
        if not kbId:
            return {"code": 400, "message": "知识库 ID (kbId) 不能为空"}
        if not files:
            return {"code": 400, "message": "没有需要删除的文件"}

        try:
            # 载入映射表
            # collection_mapping = load_mapping(collection_mapping_dir)
            collection_mapping, lock_file = load_mapping_with_lock(collection_mapping_dir)
            fcntl.flock(lock_file, fcntl.LOCK_UN) # 解锁
            collection_name = "_" + kbId.replace('-', '_')
            kbName = collection_mapping[collection_name]
        
        except KeyError:
            return {"code": 400, "message": "知识库不存在"}
        
        except Exception as e:
            # 处理其他可能的异常
            return {"code": 500, "message": f"发生未知错误: {str(e)}"}

        # 首先判断所给 kbId 对应的知识库是否存在
        if not utility.has_collection(collection_name):
            return {"code": 400, "message": f"知识库不存在"}

        collection = Collection(collection_name)

        # 构造 Milvus 查询表达式，根据 fileid 查询对应的 filename
        expr = f"fileid in {files}"
        results = collection.query(
            expr=expr,
            output_fields=["filename"]
        )
        filenames = list(set([result["filename"] for result in results]))

        if not filenames:
            return {"code": 200, "message": "所有 fileid 均未找到对应的文件名"}

        # 构造 Milvus 删除表达式
        delete_expr = f"filename in {filenames}"
        logger.info(f"构造的删除表达式: {delete_expr}")

        # 执行知识库删除操作
        try:
            collection.delete(delete_expr)
            logger.info(f"成功删除知识库 {kbName} 指定文档数据")
        except MilvusException as e:
            logger.error(f"Milvus 删除操作失败: {str(e)}")
            return {"code": 500, "message": f"Milvus 删除操作失败: {str(e)}"}

        # 删除本地文件
        local_deleted = 0
        local_failed = []
        #unique_filenames = set(filenames)  # 去除重复的文件名

        for filename in filenames:
            file_path = os.path.join(base_dir, kbName, filename)
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    local_deleted += 1
                except OSError as e:
                    logger.error(f"删除本地文件失败: {file_path} - {str(e)}")
                    local_failed.append({"filename": filename, "error": str(e)})
            else:
                logger.info(f"文件 {file_path} 不存在，跳过删除操作")

        return {
            "code": 200,
            "message": "文件删除成功",
            "data": {
                "local_deleted": local_deleted,
                "local_failed": local_failed
            }
        }

    except Exception as e:
        logger.error(f"删除过程中发生错误: {str(e)}")
        return {"code": 500, "message": f"服务器内部错误: {str(e)}"}
    

# 允许的文件类型
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt'}

def allowed_file(filename: str) -> bool:
    """检查文件扩展名是否合法"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

import io
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage

async def parse_file(file_path: str, extension: str, parseMode: str):
    """解析不同格式文件为文本列表"""
    parse_contents = []
    texts = []
    try:
        if extension == 'txt':
            file_name = os.path.basename(file_path)
            base_name = os.path.splitext(file_name)[0]
           
            # 构建输出路径（确保目录存在）
            output_dir_path = os.path.join(output_dir, f"{base_name}/txt/")
            os.makedirs(output_dir_path, exist_ok=True)  # 创建输出目录
            output_path = os.path.join(output_dir_path, file_name)  # 最终输出路径
            
            with open(file_path, 'r', encoding='utf-8') as f:
                parse_contents = [f.read()]
            
            # 将内容保存到指定输出路径
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(parse_contents[0])  # 写入解析内容
            
            logger.info(f"txt文件已保存至: {output_path}")
            
            texts = parse_contents            

        elif extension == 'pdf' or extension == 'docx':
            
            #使用file_mineru函数进行解析
            #md_list = process_pdf_file(file_path)
            
            data = {
                "file_paths": [file_path],
                "output_dir": output_dir,
                "parse_mode": parseMode
            }
            
            try:
                logger.info('start parse')
                response = requests.post(url=url, json=data)
                md_list = response.json()[0]
                md_file_path, md_content = md_list['output_file'], md_list['md_content']
                parse_contents = [md_content]
                logger.info("md文件解析成功")
                #再对md文件进行分块处理
                #file_name, merged_chunks = process_markdown_file(md_file_path)
                #parser = EnhancedMarkdownParser()
                #merged_chunks = parser.parse(md_file_path) 
                merged_chunks = process_markdown_file(md_file_path)
                logger.info("md文件完成分块处理")
                texts = merged_chunks
            
            except Exception as e:
                logger.error(f"文件解析失败: {str(e)}")
                raise HTTPException(status_code=500, detail=f"文件解析失败: {str(e)}")
        
        elif extension == 'doc':
            # 注意：python-docx 不支持.doc 格式，需要调用其他库或转换
            raise NotImplementedError("DOC 格式需要先转换为 DOCX")
    
    except Exception as e:
        logger.error(f"文件解析失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"文件解析失败: {str(e)}")

    return [parse_content for parse_content in parse_contents if parse_content.strip()],[text for text in texts if text.strip()]


"""""查找与当前上传文件相似度最高的文件接口"""
@router.post("/search_by_file")
async def search_by_file(kbId: str = Body(...),file: UploadFile = File(...),parseMode:str = Body("mineru", description="解析模式: mineru, mineru_textin, textin")):

    # 1. 验证文件类型
    if not allowed_file(file.filename):
        return {"code": 400, "message": "仅支持PDF/DOC/DOCX/TXT文件"}

    try:
        # 载入映射表
        # collection_mapping = load_mapping(collection_mapping_dir)
        collection_mapping, lock_file = load_mapping_with_lock(collection_mapping_dir)
        fcntl.flock(lock_file, fcntl.LOCK_UN) # 解锁
        collection_name = "_" + kbId.replace('-', '_')
        kbName = collection_mapping[collection_name]
    except KeyError:
        return {"code": 200, "message": "知识库不存在"}
    except Exception as e:
        # 处理其他可能的异常
        return {"code": 500, "message": f"发生未知错误: {str(e)}"}

    # 2. 保存本地文件
    file_ext = file.filename.rsplit('.', 1)[1].lower()
    temp_path = os.path.join(os.path.join(base_dir, kbName),file.filename)
    
    #if os.path.exists(temp_path):
        #return{"code":500, "message":"系统检测到相同文件名，请核实上传文件"}
    
    try:
        contents = await file.read()
        with open(temp_path, 'wb') as f:
            f.write(contents)
    
    except Exception as e:
        logger.error(f"文件保存本地失败: {str(e)}")
        return {"code": 500, "message": "文件处理失败"}
    
    # 3. 解析文件内容
    try:
        parse_contents,query_texts = await parse_file(temp_path, file_ext, parseMode)
        logger.info(f"解析内容如下: {query_texts}")
        logger.info(f"解析出{len(query_texts)}段文本")
        if not query_texts:
            os.remove(temp_path)
            return {"code": 400, "message": "文件内容为空或无法解析"}
    except Exception as e:
        os.remove(temp_path)
        return {"code": 500, "message": f"内容解析失败: {str(e)}"}
    
    # 4. 待查询文本分块
    #chunked_texts = split_text_into_chunks(query_texts, 512)
    #logger.info(f"分块后的待查询文本列表长度为:{len(chunked_texts)}")
    #logger.info(f"分块后的待查询文本列表:{chunked_texts}")

    # 5. 执行相似性搜索
    try:
        if not utility.has_collection(collection_name):
            os.remove(temp_path)
            return {"code": 400, "message": "知识库不存在"}
        col = Collection(collection_name)
        #query_embedding = emb_text(query_texts,is_query=False)
        
        #混合检索
        query_embedding = generate_embeddings(query_texts)
        
        #dense_search_params = {"metric_type": "COSINE", "params": {"nprobe": 64}}
        dense_search_params = {"metric_type": "IP", "params": {"nprobe": 64}}
        dense_req = AnnSearchRequest(
            [query_embedding["dense"][0]], "dense_vector", dense_search_params, limit=50
        )
        
        #sparse_search_params = {"metric_type": "IP", "params": {"nprobe": 16}}
        sparse_search_params = {"metric_type": "IP", "params": {"top_k": 100}}
        
        sparse_req = AnnSearchRequest(
            [query_embedding["sparse"]._getrow(0)], "sparse_vector", sparse_search_params, limit=50
        )

        rerank = RRFRanker(100)
        results = col.hybrid_search(
            [sparse_req, dense_req], 
            rerank=rerank, 
            limit=10, 
            output_fields=["text", "filename","fileid"]
        )[0]

        # 格式化结果
        formatted_results = []
        for hit in results:
            formatted_results.append({
                "text": hit.entity.get("text"),
                "filename": hit.entity.get("filename"),
                "fileid": hit.entity.get("fileid"),
                "similarity": round(hit.score, 4)  # 保留4位小数
            })
        #logger.info(f"搜索成功相似文件结果如下:{formatted_results}")
        
        final_result = []
        for result in formatted_results:
            final_result.append({"docs": result["text"],"relevantScore": result["similarity"],"relFile": result["filename"],"relFileId": result["fileid"]})
          
        
        return {"code": 200, "files":final_result,"parse_content":parse_contents}

    except Exception as e:
        os.remove(temp_path)
        logger.error(f"搜索失败: {str(e)}")
        return {"code": 500, "message": f"搜索失败: {str(e)}"}



"""确认文件入库接口"""
# 入库接口
@router.post("/upload_file_confirm")
async def upload_file_confirm(kbId: str = Body(...),fileId: str = Body(...),fileName: str = Body(...),file: UploadFile = File(...),updateContent: Optional[str] = Body(None)):

     # 1. 检查文件类型
    if not allowed_file(fileName):
        return {"code": 400, "message": "仅支持PDF/DOC/DOCX/TXT文件"}
    
    try:
        # 载入映射表
        # collection_mapping = load_mapping(collection_mapping_dir)
        collection_mapping, lock_file = load_mapping_with_lock(collection_mapping_dir)
        fcntl.flock(lock_file, fcntl.LOCK_UN) # 解锁
        collection_name = "_" + kbId.replace('-', '_')
        kbName = collection_mapping[collection_name]
    except KeyError:
        return {"code": 200, "message": "知识库不存在"}
    except Exception as e:
        # 处理其他可能的异常
        return {"code": 500, "message": f"发生未知错误: {str(e)}"}

    # 2. 获取上传文件路径以及
    file_ext = fileName.rsplit('.', 1)[1].lower()
    file_path = os.path.join(os.path.join(base_dir, kbName),fileName)

    # 3. 读取已经解析好的对应文本内容
    if file_ext == 'txt':
        #with open(file_path, 'r', encoding='utf-8') as f:
            #parse_contents = [f.read()]
        #texts = parse_contents
        
        #需要分块切分问题
        merged_chunks = process_markdown_file(file_path)
        texts = merged_chunks
        
    else:
        #读取当前文件解析后的 md文件
        filename = fileName.rsplit('.', 1)[0]
        md_file_path = os.path.join(output_dir, filename, 'txt', filename + '.md')

        #再对其md文件进行分块处理
        #_ , merged_chunks = process_markdown_file(md_file_path)
        #parser = EnhancedMarkdownParser()
        #merged_chunks = parser.parse(md_file_path) 
        merged_chunks = process_markdown_file(md_file_path)
        texts = merged_chunks

    
    #logger.info(f"分块处理:{texts}")
    
    # 4. 检查集合是否存在
    if not utility.has_collection(collection_name):
        os.remove(file_path)
        return {"code": 400, "message": "知识库不存在"}


    # 5. 生成嵌入并插入Milvus    
    try:
        col = Collection(collection_name)
        logger.info("-----开始文本向量化-----")
        #先分块
        #chunked_texts = split_text_into_chunks(texts, 512)
        #logger.info(f"分块后的文本列表:{chunked_texts}")
        #embeddings = emb_text(texts,is_query=False)
        embeddings = generate_embeddings(texts)
        #logger.info(f"向量化后的结果:{embeddings}")
        logger.info("-----完成文本向量化-----")
        
        # 生成chunk_order（从1开始的递增序列，与分块数量一致）
        chunk_orders = list(range(1, len(texts) + 1))
        logger.info(f"分块数量: {len(texts)}，chunk_order序列: {chunk_orders}")
        # 将每个元素转换为列表的列表格式
        entities = [
            texts,  #  texts 为字符串列表
            embeddings['sparse'],
            embeddings['dense'],
            [fileName] * len(texts),  # 重复文件名以匹配文本数量
            [fileId] * len(texts),  # 重复文件ID以匹配文本数量   
            chunk_orders            # 新增：分块顺序号
        ]

        col.insert(entities)
        col.flush()  # 确保数据持久化
       
        logger.info(f"文档已成功上传至知识库: --{kbName}-- ")
        return { "code": 200,"message": "文件向量化并成功入库"}

    
    except Exception as e:
        os.remove(file_path)
        logger.error(f"Milvus操作失败: {str(e)}")
        return {"code": 500, "message": f"上传失败: {str(e)}"}

"""知识检索接口"""
@router.post("/retrieve_knowledge")
def retrieval(kbId: Optional[List[str]] = Body(None),query: str = Body(...),limit: int = Body(default=20),similarityThreshold: float = Body(default=0.1),workers: int = Body(default=10)):
    """
    # 查询重构
    messages = [
        {
            'role': 'system',
            'content': '你现在的身份是珠江水利科学院智能问答大模型'
        },
        {
            'role': 'user',
            'content': f'请根据以下文本生成一段背景知识，文本为：{query}'
        },
    ]
    
    response = client.chat.completions.create(
        model='qwen-max',  # 此处以qwen-max为例，可按需更换模型名称。模型列表：https://help.aliyun.com/zh/model-studio/getting-started/models
        messages=messages,
        stream=False,
        temperature=0
    )
    
    query = response.choices[0].message.content
    """
    #查询query文本向量化
    #query_embedding = emb_text(query,is_query=True)
    query_embedding = generate_embeddings(query)
    
    # 初始化结果列表
    all_results = []
    
    try:
        # 确定需要检索的kbId列表
        if kbId is None or len(kbId) == 0:
            # 未传入kbId时检索所有知识库（保持原逻辑）
            collection_names = utility.list_collections()
            logger.info(f"未指定kbId，检索所有知识库，Collection列表: {collection_names}")
        else:
            # 传入kbId数组时，转换为对应的collection名称列表
            collection_names = ["_" + kid.replace('-', '_') for kid in kbId]
            logger.info(f"指定kbId数组，检索对应的Collection列表: {collection_names}")
        
        # 并行检索配置 - 可根据服务器资源调整最大工作线程数
        max_workers = min(workers, len(collection_names))  # 限制最大线程数避免资源耗尽
        
        # 定义单个知识库检索的任务函数
        def retrieve_from_collection(collection_name):
            try:
                # 载入映射表
                collection_mapping, lock_file = load_mapping_with_lock(collection_mapping_dir)
                fcntl.flock(lock_file, fcntl.LOCK_UN)  # 解锁
                if collection_name not in collection_mapping:
                    logger.warning(f"知识库映射不存在: {collection_name}，跳过检索")
                    return []
                
                kbName = collection_mapping[collection_name]

                # 检查collection是否存在
                if not utility.has_collection(collection_name):
                    logger.warning(f"知识库不存在: {collection_name}，跳过检索")
                    return []

                # 初始化collection
                col = Collection(collection_name)

                # 混合检索参数
                dense_search_params = {"metric_type": "IP", "params": {"nprobe": 64}}
                dense_req = AnnSearchRequest(
                    [query_embedding["dense"][0]], "dense_vector", dense_search_params, limit=(limit+50)
                )
                sparse_search_params = {"metric_type": "IP", "params": {"top_k": 100}}
                sparse_req = AnnSearchRequest(
                    [query_embedding["sparse"]._getrow(0)], "sparse_vector", sparse_search_params, limit=(limit+50)
                )
                rerank = RRFRanker(100)
                results = col.hybrid_search(
                    [sparse_req, dense_req], 
                    rerank=rerank, 
                    limit=limit, 
                    output_fields=["text", "filename","fileid"]
                )[0]

                # 格式化结果
                formatted_results = []
                for hit in results:
                    formatted_results.append({
                        "text": hit.entity.get("text"),
                        "filename": hit.entity.get("filename"),
                        "fileid": hit.entity.get("fileid"),
                        "filepath": os.path.join(base_dir, kbName, hit.entity.get("filename")),
                        "similarity": round(hit.score, 4)
                    })
                logger.info(f'完成{collection_name}知识库的检索')
                return formatted_results

            except Exception as e:
                logger.error(f"知识库{collection_name}检索失败: {str(e)}，跳过该知识库")
                return []
        
        # 使用线程池并行执行多个知识库的检索任务
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有检索任务
            future_to_collection = {executor.submit(retrieve_from_collection, col_name): col_name 
                                   for col_name in collection_names}
            
            # 收集所有任务结果
            for future in concurrent.futures.as_completed(future_to_collection):
                collection_name = future_to_collection[future]
                try:
                    results = future.result()
                    all_results.extend(results)
                except Exception as e:
                    logger.error(f"处理知识库{collection_name}的检索结果时发生异常: {str(e)}")
        
        # 重排逻辑
        documents = [res["text"] for res in all_results]
        bge_rf = BGERerankFunction(model_name='backend/app/models/bge-reranker-large', device='cuda:0')
        rerank_results = bge_rf(
            query=query,
            documents=documents,
            top_k=limit
        )

        # 构建最终结果
        final_result = []
        for i, rerank_result in enumerate(rerank_results):
            for res in all_results:
                if res["text"] == rerank_result.text and rerank_result.score >= similarityThreshold:
                    final_result.append({
                        "num": i + 1,
                        "content": res["text"],
                        "fileName": res["filename"],
                        "fileId": res["fileid"],
                        "score": rerank_result.score,
                        "filePath": res["filepath"]
                    })
                    break  # 避免重复匹配
        
        logger.info(f"检索成功，最终结果: {final_result}")
        return {"code": 200, "files": final_result}

    except Exception as e:
        logger.error(f"全局检索失败: {str(e)}")
        return {"code": 500, "message": f"检索失败: {str(e)}"}

@router.post("/retrieve_file_content")
async def retrieve_file_content(
    kbId: str = Body(..., embed=True),
    fileId: str = Body(..., embed=True),
    search: bool = Body(..., embed=True),
    query: Optional[str] = Body(None),
    page : int = Body(1,description="指定获取的页码，默认1（需为正整数）"),
    limit: int = Body(..., description="单次检索最大返回数量"),
    pageSize: int = Body(9, description="每页最大文本块数量，默认9")
):
    """
    在指定知识库的特定文件中进行内容检索或全文获取（支持混合检索）
    
    参数:
    kbId (str): 知识库ID
    fileId (str): 需要检索的文件ID
    search (bool): true-关键词检索 false-全文获取
    query (str): 检索关键词（search为true时填）
    limit (int): 检索结果最大返回数量（仅search为true时有效）
    pageSize (int): 页最大文本块数量，默认9
    
    返回:
    dict: 包含状态码、分页数量和结果列表的响应
    """
    
    #检索阈值
    similarity_threshold = 0.1
    
    # 1. 参数校验
    if search and not query:
        search = False
    
    if not kbId or not fileId:        
        return {"code": 400, "message": "kbId和fileId参数必填"}

    if page < 1:# 新增页码有效性校验
        return {"code": 400, "message": "page参数必须为正整数"}
    
    try:
        
        # 2. 加载知识库映射
        # collection_mapping = load_mapping(collection_mapping_dir)
        collection_mapping, lock_file = load_mapping_with_lock(collection_mapping_dir)
        fcntl.flock(lock_file, fcntl.LOCK_UN) # 解锁
        collection_name = "_" + kbId.replace('-', '_')
        if collection_name not in collection_mapping:
            return {"code": 404, "message": "知识库不存在"}

        # 3. 检查Milvus集合是否存在
        if not utility.has_collection(collection_name):
            return {"code": 404, "message": "知识库不存在"}
        
        col = Collection(collection_name)
        col.load()

        # 4. 构造文件筛选表达式（参考删除接口的筛选逻辑）
        filter_expr = f"fileid == '{fileId}'"
        
        totalnumber = len(col.query(
                    expr=filter_expr,
                    output_fields=["text"]
                ))
        
        if not limit:
            limit = totalnumber
        
        # 5. 根据search参数执行不同操作
        results = []
        
        if search:
            
            # 5.1 关键词混合检索模式
            if not query.strip():
                return {"code": 400, "message": "检索关键词不能为空"}
            
            # 生成查询向量（使用混合检索所需的dense和sparse向量）
            query_embedding = generate_embeddings(query)
            
            # 构造混合搜索请求（参考search_by_file接口的混合检索实现）
            dense_req = AnnSearchRequest(
                [query_embedding["dense"][0]],  # dense向量
                "dense_vector",
                {"metric_type": "IP", "params": {"nprobe": 64}},
                #limit=(limit+50),
                limit=totalnumber,
                expr=filter_expr
            )
            
            sparse_req = AnnSearchRequest(
                [query_embedding["sparse"]._getrow(0)],  # sparse向量
                "sparse_vector",
                {"metric_type": "IP", "params": {"top_k": 100}},
                #limit=(limit+50),
                limit=totalnumber,
                expr=filter_expr
            )
            
            # 混合排序（使用RRFRanker）
            rerank = RRFRanker(100)
            search_results = col.hybrid_search(
                [sparse_req, dense_req],
                rerank=rerank,
                output_fields=["text", "chunk_order", "filename"],
                limit=totalnumber
            )[0]

            # 格式化结果（包含相似度）
            raw_results = [
                {
                    "text": hit.entity.text,
                    "chunkOrder": hit.entity.chunk_order,
                    "fileName": hit.entity.filename
                }
                for hit in search_results
            ]
            
            # logger.info(f'格式化结果:{raw_results}')
            
            if raw_results:
                
                # 提取待重排的文本列表
                documents = [res["text"] for res in raw_results]
                
                # 初始化重排模型y
                bge_rf = BGERerankFunction(model_name='backend/app/models/bge-reranker-large', device='cuda:0')
                
                # 执行重排（保留原始limit数量）
                rerank_results = bge_rf(
                    query=query,
                    documents=documents,
                    top_k=limit  # 使用原始limit控制最终返回数量
                )

                # 关联重排结果与原始元数据
                final_results = []
                for rerank_item in rerank_results:
                    if rerank_item.score >= similarity_threshold:
                        
                        # 查找原始结果中对应的条目
                        original_item = next(
                            (item for item in raw_results if item["text"] == rerank_item.text),
                            None
                        )
                        
                        if original_item:
                            final_results.append({
                                "text": original_item["text"],
                                "chunkOrder": original_item["chunkOrder"],
                                "fileName": original_item["fileName"],
                                "similarity": rerank_item.score
                            })
                
                results = final_results
            
            else:
                
                results = []
                
        else:
            
            # 5.2 全文获取模式（按原文顺序返回）
            # 查询文件所有文本块并按chunk_order排序（依赖分块时记录的chunk_order字段）
            search_results = col.query(
                expr=filter_expr,
                output_fields=["text", "chunk_order", "filename"],
                order_by="chunk_order"  # 按分块顺序排序
            )

            # 按chunk_order排序（确保顺序）
            results = sorted(
                [
                    {
                        "text": item["text"],
                        "chunkOrder": item["chunk_order"],
                        "fileName": item["filename"],
                        "similarity": None  # 全文模式无相似度
                    }
                    for item in search_results
                ],
                key=lambda x: x["chunkOrder"]
            )

        # 6. 分页计算（每页9条）
        total = len(results)
        pagenumber = (total + pageSize - 1) // pageSize  # 计算总分页数（向上取整）

        # 计算当前页数据范围
        start = (page - 1) * pageSize
        end = start + pageSize
        current_page_results = results[start:end]  # 截取当前页数据
        
        # 7. 构造最终响应
        return {
            "code": 200,
            "total": total,
            "pageNumber": pagenumber,
            "currentPage": page,
            "files": [
                {
                    "text": item["text"],
                    "fileName": item["fileName"],
                    "chunkOrder": item["chunkOrder"],
                    "similarity": item["similarity"]
                }
                for item in current_page_results # 仅返回当前页数据
            ]
        }

    except KeyError as e:
        logger.error(f"映射表错误: {str(e)}")
        return {"code": 404, "message": "知识库或文件不存在"}
    
    except MilvusException as e:
        logger.error(f"Milvus操作失败: {str(e)}")
        return {"code": 500, "message": "数据库操作失败"}
    
    except Exception as e:
        logger.error(f"接口异常: {str(e)}")
        return {"code": 500, "message": f"服务器内部错误: {str(e)}"}
    
    
@router.post("/update_text_chunk")
async def update_text_chunk(
    kbId: str = Body(..., embed=True),
    fileId: str = Body(..., embed=True),
    chunkOrder: int = Body(..., embed=True, description="需要修正的原文本块顺序号（唯一标识）"),
    newText: str = Body(..., embed=True, description="修正后的文本内容")
):
    """
    修正单个文本块并重新入库，包含事务回滚和本地文件更新逻辑
    
    参数:
    kbId (str): 知识库ID
    fileId (str): 文件ID
    chunkOrder (int): 原文本块的顺序号（唯一标识）
    newText (str): 修正后的文本内容
    
    返回:
    dict: 包含状态码和操作结果的响应
    """
    
    # 1. 参数校验
    if not all([kbId, fileId, chunkOrder]):
        return {"code": 400, "message": "kbId、fileId、chunkOrder为必填参数"}
    
    # 事务回滚变量初始化
    old_chunk = None  # 存储原文本块信息用于回滚
    rollback_success = False

    try:
        # 2. 验证知识库存在
        # collection_mapping = load_mapping(collection_mapping_dir)
        collection_mapping, lock_file = load_mapping_with_lock(collection_mapping_dir)
        fcntl.flock(lock_file, fcntl.LOCK_UN) # 解锁
        collection_name = "_" + kbId.replace('-', '_')
        
        if collection_name not in collection_mapping:
            return {"code": 404, "message": "知识库不存在"}
        
        if not utility.has_collection(collection_name):
            return {"code": 404, "message": "知识库不存在"}
        
        col = Collection(collection_name)
        col.load()

        # 3. 查询原文本块（用于回滚和验证存在性）
        filter_expr = f"fileid == '{fileId}' && chunk_order == {chunkOrder}"
        old_chunks = col.query(
            expr=filter_expr,
            output_fields=["text", "filename", "sparse_vector", "dense_vector"]
        )
        
        if not old_chunks:
            return {"code": 404, "message": "指定文本块不存在"}
        
        old_chunk = old_chunks[0]  # 确保唯一

        # 4. 删除原文本块
        delete_result = col.delete(expr=filter_expr)
        logger.info(delete_result)
        if delete_result.delete_count != 1:
            return {"code": 500, "message": "原文本块删除失败"}

        # 5. 准备新文本块数据
        # final_chunk_order = newChunkOrder if newChunkOrder is not None else chunkOrder
        final_chunk_order = chunkOrder
        
        # 生成新嵌入向量
        new_embeddings = generate_embeddings([newText])
        
        # 构造插入实体（保持与原入库接口一致的字段顺序）
        new_entity = [
            [newText],  # 文本内容
            new_embeddings['sparse'],  # sparse向量
            new_embeddings['dense'],  # dense向量
            [old_chunk['filename']],  # 保持原文件名
            [fileId],  # 文件ID
            [final_chunk_order]  # 顺序号（可能更新）
        ]

        # 6. 插入新文本块（带事务回滚）
        try:
            insert_result = col.insert(new_entity)
            col.flush()
            if insert_result.insert_count != 1:
                raise MilvusException(message="新文本块插入失败")
        
        except Exception as e:
            # 插入失败时回滚原块
            rollback_entity = [
                [old_chunk['text']],
                [old_chunk['sparse_vector']],
                [old_chunk['dense_vector']],
                [old_chunk['filename']],
                [fileId],
                [chunkOrder]
            ]
            col.insert(rollback_entity)
            col.flush()
            rollback_success = True
            raise  # 重新抛出异常以便外层捕获

        # 7. 更新本地文件（拼接所有块生成新MD）
        # 7.1 查询该文件所有文本块并按顺序排序
        file_filter = f"fileid == '{fileId}'"
        all_chunks = col.query(
            expr=file_filter,
            output_fields=["text", "chunk_order"],
            order_by="chunk_order"
        )
        sorted_chunks = sorted(all_chunks, key=lambda x: x['chunk_order'])
        
        # 7.2 拼接完整内容
        full_content = "\n".join([chunk['text'] for chunk in sorted_chunks])
        
        # 7.3 获取原文件路径（从原块中获取文件名）
        original_filename = old_chunk['filename'].rsplit('.', 1)[0]  # 去除扩展名
        file_path = os.path.join(
            output_dir, 
            original_filename, 
            'txt', 
            old_chunk['filename']
        )
        
        # 7.4 删除原文件并写入新内容
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.info(f"已删除原文件: {file_path}")
            except Exception as e:
                logger.error(f"删除原文件失败: {str(e)}")
                raise  # 抛出异常触发外层错误处理
        
        # 直接写入新内容（若目录不存在会自动触发FileNotFoundError）
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(full_content)
        
        logger.info(f"新文件已保存至: {file_path}")

        return {"code": 200, "message": "文本块修正入库成功且本地文件已更新"}

    except KeyError:
        return {"code": 404, "message": "知识库不存在"}
    
    except MilvusException as e:
        logger.error(f"Milvus操作异常: {str(e)}")
        if rollback_success:
            return {"code": 500, "message": f"新块插入失败，已回滚原块；错误详情: {str(e)}"}
        return {"code": 500, "message": f"数据库操作失败，原块已删除且回滚失败；错误详情: {str(e)}"}
    
    except Exception as e:
        logger.error(f"接口异常: {str(e)}")
        return {"code": 500, "message": f"服务器内部错误: {str(e)}"}
    
@router.post("/delete_text_chunk")
async def delete_text_chunk(
    kbId: str = Body(..., embed=True),
    fileId: str = Body(..., embed=True),
    chunkOrder: int = Body(..., embed=True, description="需要删除的文本块顺序号（唯一标识）")
):
    """
    删除单个文本块并更新本地文件，包含事务回滚逻辑
    
    参数:
    kbId (str): 知识库ID
    fileId (str): 文件ID
    chunkOrder (int): 要删除的文本块顺序号（唯一标识）
    
    返回:
    dict: 包含状态码和操作结果的响应
    """
    # 1. 参数校验
    if not all([kbId, fileId, chunkOrder]):
        return {"code": 400, "message": "kbId、fileId、chunkOrder为必填参数"}
    
    old_chunk = None  # 存储原文本块信息用于回滚
    rollback_needed = False  # 标记是否需要回滚删除操作

    try:
        # 2. 验证知识库存在
        collection_mapping, lock_file = load_mapping_with_lock(collection_mapping_dir)
        fcntl.flock(lock_file, fcntl.LOCK_UN)  # 解锁
        collection_name = "_" + kbId.replace('-', '_')
        
        # 双重验证：映射存在且集合实际存在
        if collection_name not in collection_mapping or not utility.has_collection(collection_name):
            return {"code": 404, "message": "知识库不存在"}
        
        col = Collection(collection_name)
        col.load()

        # 3. 查询目标文本块（用于回滚和存在性验证）
        filter_expr = f"fileid == '{fileId}' && chunk_order == {chunkOrder}"
        old_chunks = col.query(
            expr=filter_expr,
            output_fields=["text", "filename", "sparse_vector", "dense_vector"]
        )
        
        if not old_chunks:
            return {"code": 404, "message": "指定文本块不存在"}
        
        old_chunk = old_chunks[0]  # 确保唯一

        # 4. 执行删除操作
        delete_result = col.delete(expr=filter_expr)
        col.flush()
        if delete_result.delete_count != 1:
            return {"code": 500, "message": "文本块删除失败"}
        
        rollback_needed = True  # 标记需要回滚

        # 5. 查询文件剩余文本块并更新本地文件
        # 5.1 获取文件所有剩余块（排除已删除的块）
        file_filter = f"fileid == '{fileId}'"
        all_chunks = col.query(
            expr=file_filter,
            output_fields=["text", "chunk_order"],
            order_by="chunk_order"
        )
        sorted_chunks = sorted(all_chunks, key=lambda x: x['chunk_order'])

        # 5.2 构造文件新内容（无剩余块则为空）
        full_content = "\n".join([chunk['text'] for chunk in sorted_chunks]) if sorted_chunks else ""

        # 5.3 定位原文件路径
        original_filename = old_chunk['filename']
        file_dir = os.path.join(output_dir, original_filename.rsplit('.', 1)[0], 'txt')
        file_path = os.path.join(file_dir, original_filename)

        # 5.4 处理文件更新逻辑
        if os.path.exists(file_path):
            if not sorted_chunks:
                # 无剩余块则删除文件
                os.remove(file_path)
                logger.info(f"文件无剩余块，已删除: {file_path}")
            else:
                # 有剩余块则写入新内容
                os.makedirs(file_dir, exist_ok=True)  # 确保目录存在
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(full_content)
                logger.info(f"本地文件已更新: {file_path}")
        else:
            logger.warning(f"原文件不存在，无需更新: {file_path}")

        return {"code": 200, "message": "文本块删除成功且本地文件已更新"}

    except KeyError:
        return {"code": 404, "message": "知识库不存在"}
    
    except MilvusException as e:
        logger.error(f"Milvus操作异常: {str(e)}")
        if rollback_needed and old_chunk:
            # 回滚删除操作
            rollback_entity = [
                [old_chunk['text']],
                [old_chunk['sparse_vector']],
                [old_chunk['dense_vector']],
                [old_chunk['filename']],
                [fileId],
                [chunkOrder]
            ]
            col.insert(rollback_entity)
            col.flush()
            logger.info("已回滚删除的文本块")
        
        return {"code": 500, "message": f"数据库操作失败，错误详情: {str(e)}"}
    
    except Exception as e:
        logger.error(f"接口异常: {str(e)}")
        if rollback_needed and old_chunk:
            # 通用异常回滚
            rollback_entity = [
                [old_chunk['text']],
                [old_chunk['sparse_vector']],
                [old_chunk['dense_vector']],
                [old_chunk['filename']],
                [fileId],
                [chunkOrder]
            ]
            col.insert(rollback_entity)
            col.flush()
            logger.info("已回滚删除的文本块")
        
        return {"code": 500, "message": f"服务器内部错误: {str(e)}"}
    