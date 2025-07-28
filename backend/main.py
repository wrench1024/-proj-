"""
writer: feilong zhao
date: 2025/3/10
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers.file_upload_router import router as file_upload_router
from app.routers.knowledge_inter import router as knowledge_base
from app.routers.knowledge_base_chat import router as knowledge_base_chat
from app.routers.intelligent_chat import router as intelligent_chat
# from routers.query_response_router import router as query_response_router
# from routers.knowledge_base_router import router as knowledge_base_router
from app.routers.llm_chat import router as llm_chat
from app.routers.file_mineru import router as process_file_path
from app.routers.file_process import router as file_process
from app.routers.review_report import router as review_report
from app.routers.retrieve import router as search
from app.routers.classify import router as document_classify
from app.routers.extract_data import router as extract_data
from app.routers.llm_extract_key_elements import router as llm_extract_key_elements
from app.core.config import get_logger,settings
import uvicorn


app = FastAPI(title=settings.app_name,version=settings.app_version)

# 获取主应用的日志记录器
logger = get_logger(__name__)

# 配置 CORS 中间件
origins = [
    "http://10.21.22.107",
    "https://10.21.22.107",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/info")
def get_info():
    logger.info("Accessed /info endpoint")
    return {
        "name": settings.app_name,
        "version": settings.app_version
    }

# 文件上传接口
app.include_router(file_upload_router, prefix="/upload", tags=["File Upload"])

# 包含query_response_router中的所有路由
# app.include_router(query_response_router, prefix="/query", tags=["Query Response"])

# 包含knowlege_base中的所有路由
app.include_router(knowledge_base, prefix="/knowledge_base", tags=["Knowledge Base"])

# 纯大模型问答接口
app.include_router(llm_chat, prefix="/llm_chat", tags=["LLM Chat"])

# 文件解析接口
app.include_router(process_file_path, prefix="/process_file_path", tags=["file process"])

# 文件上传并解析接口
app.include_router(file_process, prefix="/file_process", tags=["file upload and process"])

# 知识库问答接口
app.include_router(knowledge_base_chat,prefix="/knowledge_base_chat", tags=["Knowledge baseChat"])

#纯大模型/知识问答接口
app.include_router(intelligent_chat,prefix="/intelligent_chat", tags=["intelligent Chat"])

# 待审查报告相关接口
app.include_router(review_report,prefix="/review_report", tags=["Review Report"])

# 待审查报告的检索接口
app.include_router(search, prefix="/review_report", tags=["report search"])

# 报告/文段内容数据抽取接口
app.include_router(extract_data, prefix="/extract_data", tags=["report or text extract"])

# 报告/文段内容分类接口
app.include_router(document_classify, prefix="/classify", tags=["report or text classify"])

#关键信息抽取接口
app.include_router(llm_extract_key_elements,prefix="/extract_key_elements", tags=["llm extract key elements"])

if __name__ == "__main__":
    
    # 默认绑定到0.0.0.0:8443，可以通过命令行覆盖
    uvicorn.run(
        app, 
        host="10.21.22.107",
        port=8443,
        log_level="info"
        )