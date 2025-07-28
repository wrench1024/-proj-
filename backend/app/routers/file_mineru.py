"""
wzq 2025/3/11
文件解析接口
接收文件路径作为输入，对指定路径的文件进行markdown格式处理。
具体处理逻辑如下：
1. 接收用户传入的文件路径，检查该文件是否存在。
2. 对文件使用 `magic - pdf` 命令对其进行处理，并将处理结果输出到指定的输出目录。
3. 处理完成后，在输出目录中查找生成的 Markdown 文件，若找到则返回其路径；若未找到则返回处理失败信息。
4. 若文件不是 PDF或word 格式，则直接返回文件的原始路径。
整个过程中会使用日志记录关键信息，包括命令执行等情况，方便后续的调试和监控。
"""

from fastapi import APIRouter
import os
import subprocess
from typing import Dict
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.core.config import get_logger

router = APIRouter()
# 定义 dolmaviewer 输出目录
output_dir = 'file'

# 创建 dolmaviewer 输出目录（如果不存在）
os.makedirs(output_dir, exist_ok=True)

logger = get_logger(__name__)

target_venv_name = 'pdf'
another_target_name = 'shuikeyuan'
conda_path = '/home/mengshengbo/.conda/envs/regdoc'

def process_pdf_file(filePath: str) -> Dict[str, str]:
    if not os.path.exists(filePath):
        logger.error(f"文件路径 {filePath} 不存在")
        return {"status": "failed", "message": "文件路径不存在"}

    file_name = os.path.basename(filePath)

    if file_name.endswith('.pdf') or file_name.endswith('.docx'):
        # 构建并执行 magic-pdf 命令
        command = f'CUDA_VISIBLE_DEVICES=1 magic-pdf -p "{filePath}" -o "{output_dir}" -m txt'
        # full_command = f'{conda_path} activate {target_venv_name} && {command} && conda activate {another_target_name}'
        full_command = f'{conda_path} run -n {target_venv_name} {command}'
        try:
            subprocess.run(full_command, shell=True, check=True)
            logger.info(f"成功执行 magic-pdf 命令，处理文件: {filePath}")

            # 获取文件名（不包含扩展名）
            base_name = os.path.splitext(file_name)[0]

            # 构建可能包含 Markdown 文件的目录路径
            potential_dir = os.path.join(output_dir, base_name)

            # 检查该目录是否存在
            if os.path.exists(potential_dir) and os.path.isdir(potential_dir):
                # 遍历该目录下的所有文件
                for root, dirs, files in os.walk(potential_dir):
                    for file in files:
                        if file.endswith('.md'):
                            # 找到 Markdown 文件，返回其完整路径
                            mdFilepath = os.path.join(root, file)
                            try:
                                # 读取 Markdown 文件内容
                                with open(mdFilepath, 'r', encoding='utf-8') as f:
                                    md_content = f.read()
                                return {"status": "success", "outputFile": mdFilepath, "mdContent": md_content}
                            except Exception as e:
                                logger.error(f"读取 Markdown 文件 {mdFilepath} 内容时出错: {e}")
                                return {"status": "failed", "message": f"读取 Markdown 文件内容时出错: {e}"}

            # 如果没有找到 Markdown 文件
            logger.warning("未找到生成的 Markdown 文件")
            return {"status": "failed", "message": "未找到生成的 Markdown 文件"}

        except subprocess.CalledProcessError as e:
            logger.error(f"处理文件 {filePath} 时，magic-pdf 命令出错: {e}")
            return {"status": "failed", "message": "magic-pdf 命令执行出错"}
    else:
        return {"status": "success", "outputFile": filePath}


@router.post("/process_file_path/")
async def process_file_path(filePath: str):
    result = process_pdf_file(filePath)
    return result

if __name__ == "__main__":
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(router)
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7000)