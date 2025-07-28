"""
文件上传及处理接口
接收用户上传的文件，将其保存到指定工作空间目录，若为 PDF 文件或docx文件则执行 magic - pdf 命令进行处理，
若为 TXT 文件则直接解析其内容，
并尝试返回生成的文件内容 文件路径。
"""

from fastapi import APIRouter, File, UploadFile
import os
import subprocess
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.core.config import get_logger
from typing import Dict

router = APIRouter()
# 定义要处理的目录
WORKSPACE = 'uploads'
# 输出目录
OUTPUT_DIR = 'file'

# 确保工作空间目录存在
os.makedirs(WORKSPACE, exist_ok=True)
# 确保 dolmaviewer 输出目录存在
os.makedirs(OUTPUT_DIR, exist_ok=True)

logger = get_logger(__name__)
target_venv_name = 'pdf'
another_target_name = 'shuikeyuan'
conda_path = '/home/mengshengbo/.conda/envs/regdoc'

def process_uploaded_file(file: UploadFile) -> Dict[str, str]:
    try:
        # 直接使用源文件名
        uploaded_file_path = os.path.join(WORKSPACE, file.filename)
        # 保存上传的文件
        with open(uploaded_file_path, 'wb') as f:
            f.write(file.file.read())
    except Exception as e:
        logger.error(f"文件上传失败: {e}")
        return {"code": 500, "content": f"文件上传失败: {e}"}

    file_name = file.filename
    if file_name.endswith('.pdf') or file_name.endswith('.docx'):
        command = f'CUDA_VISIBLE_DEVICES=1 magic-pdf -p "{uploaded_file_path}" -o "{OUTPUT_DIR}" -m txt'
        # full_command = f'{conda_path} activate {target_venv_name} && {command} && conda activate {another_target_name}'
        full_command = f'{conda_path} run -n {target_venv_name} {command}'
        try:
            subprocess.run(full_command, shell=True, check=True)
            logger.info(f"成功执行 magic-pdf 命令，处理文件: {uploaded_file_path}")

            # 获取文件名（不包含扩展名）
            base_name = os.path.splitext(file_name)[0]

            # 构建可能包含 Markdown 文件的目录路径
            potential_dir = os.path.join(OUTPUT_DIR, base_name)

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
                                return {"code": 200, "content": md_content, "filePath": md_file_path}
                            except Exception as e:
                                logger.error(f"读取 Markdown 文件 {md_file_path} 内容时出错: {e}")
                                return {"code": 500, "content": f"读取 Markdown 文件内容时出错: {e}"}

            # 如果没有找到 Markdown 文件
            logger.warning("未找到生成的 Markdown 文件")
            return {"code": 500, "content": "未找到生成的 Markdown 文件"}

        except subprocess.CalledProcessError as e:
            logger.error(f"处理文件 {uploaded_file_path} 时，magic-pdf 命令出错: {e}")
            return {"code": 500, "content": f"magic-pdf 命令执行出错: {e}"}
    elif file_name.endswith('.txt'):
        try:
            # 读取 TXT 文件内容
            with open(uploaded_file_path, 'r', encoding='utf-8') as f:
                txt_content = f.read()
            return {"code": 200, "content": txt_content, "filePath": uploaded_file_path}
        except Exception as e:
            logger.error(f"读取 TXT 文件 {uploaded_file_path} 内容时出错: {e}")
            return {"code": 500, "content": f"读取 TXT 文件内容时出错: {e}"}
    else:
        return {"code": 200, "content": f"不支持处理 {file_name} 类型的文件"}


@router.post("/process")
async def upload_file(file: UploadFile = File(...)):
    result = process_uploaded_file(file)
    return result


if __name__ == "__main__":
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(router)
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7000)