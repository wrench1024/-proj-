"""
文件入库接口
接收用户上传文件，保存在./uploads/目录下"""

from fastapi import APIRouter, File, UploadFile
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.core.config import get_logger


router = APIRouter()
UPLOAD_DIRECTORY = "uploads/"    

# 确保上传目录存在
os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)

logger = get_logger(__name__)

@router.post("/file/")
async def upload_file(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_DIRECTORY, file.filename)
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())
    logger.info(f"Uploaded file: {file.filename} to {file_path}")
    return {"filename": file.filename, "message": "File uploaded successfully", "filePath": file_path}

# if __name__ == "__main__":
#     from fastapi import FastAPI

#     app = FastAPI()
#     app.include_router(router)
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=7000)