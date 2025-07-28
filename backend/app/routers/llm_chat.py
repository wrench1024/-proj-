"""
writer: feilong zhao
date: 2025/3/11
"""

from fastapi import APIRouter, Request,Body,Response
from app.core.config import get_logger

from sse_starlette.sse import EventSourceResponse

import asyncio
import json
from openai import OpenAI

import aiohttp
import requests
# 设置 OpenAI 的 API key 和 API base 来使用 vLLM 的 API server.
openai_api_key = ""  # 如果不需要 API key，可以留空或设置为 "EMPTY"
openai_api_base = "http://localhost:8000/v1"

#api_key="sk-762b0529add947b081778614c7fe1cda", 
#base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
#url = "http://localhost:8000/v1/chat/completions"
#url = 'http://localhost:7001/generate_text/'
#model_path = '/home/ysdx2025/shuikeyuan/model/qwen/Qwen/Qwen2___5-14B-Instruct'
router = APIRouter()

logger = get_logger(__name__)

from openai import AsyncOpenAI,OpenAIError
client = AsyncOpenAI(
    api_key="sk-762b0529add947b081778614c7fe1cda",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)

@router.options("/llm_chat/")
async def options_llm_chat(request: Request):
    response = Response(status_code=204)
    response.headers["Allow"] = "POST"
    return response


@router.post("/llm_chat/")
async def llm_chat(
                   query: str = Body(...,desription='用户输入',examples=["你是谁"]),
                   history:list = Body([],description="历史对话记录"),
                   stream:bool=Body(False,description="是否流式输出"),
                   modelName:str = Body('qwq-plus',description='模型名称'),
                   temperature:float = Body(0.1,description="LLM 采样温度"),
                   show_reasoning: bool = Body(True, description="是否输出模型思考过程（仅支持特定思考类模型）")
                   ):
    
    
    # 纯大模型问答接口
    async def event_generator(query,history,stream,modelName,temperature):
        try:
            
            max_length = 129024 if modelName == 'qwen-max-latest' else 57344
            if len(query) > max_length:
                query = query[:max_length]
                    
            messages = [
            {
                'role': 'system',
                'content': '你现在的身份是珠江水利科学院智能问答大模型'
            },
            {
                'role': 'user',
                'content': f'{query}'
            },
        ]
        
            # 将history中的字典数据插入到messages列表的第二个位置
            messages[1:1] = history
           
            # 模型调用逻辑（流式/非流式分支）
            if stream:
                async for part in await client.chat.completions.create(
                    model=modelName,
                    messages=messages,
                    stream=True,
                    temperature=temperature,
                    max_tokens=4096
                ):
                    if not part.choices:
                        continue  # 跳过无内容的chunk
                    
                    delta = part.choices[0].delta
                    response_data = {}  # 保持原有格式的基础数据

                    # 提取答案内容（原有逻辑）
                    if hasattr(delta, 'content') and delta.content:
                        response_data["answer"] = delta.content
                    
                    # 提取思考过程（仅当show_reasoning=True且模型返回时）
                    if show_reasoning and hasattr(delta, 'reasoning_content') and delta.reasoning_content:
                        response_data["reasoning"] = delta.reasoning_content
                    
                    # 仅当有有效内容时返回（保持原有格式）
                    if response_data:
                        yield {"data": json.dumps(response_data, ensure_ascii=False)}

            else:
                
                response = await client.chat.completions.create(
                    model=modelName,
                    messages=messages,
                    temperature=temperature
                )
                
                # 构造原有格式的响应
                response_data = {
                    "answer": response.choices[0].message.content
                }
                
                # 添加思考过程（仅当show_reasoning=True且模型支持时）
                if show_reasoning and hasattr(response.choices[0].message, 'reasoning_content'):
                    response_data["reasoning"] = response.choices[0].message.reasoning_content
                
                yield {"data": json.dumps(response_data, ensure_ascii=False)}
            """
            if stream:
                async for part in await client.chat.completions.create(
                    model=modelName,
                    messages=messages,
                    stream=True,
                    temperature=temperature
                ):
                    delta_content = part.choices[0].delta.content
                    
                    logger.info(delta_content)
                    yield { "data": json.dumps({"answer": delta_content}, ensure_ascii=False) }
                
            else:
                response = await client.chat.completions.create(
                    model=modelName,
                    messages=messages,
                    stream=False,
                    temperature=temperature
                )
                full_content = response.choices[0].message.content
                logger.info(full_content)
                yield { "data": json.dumps({"answer": full_content}, ensure_ascii=False) }
        """
        except OpenAIError as e:
            error_msg = f"模型调用错误: {str(e)}"
            logger.error(error_msg)
            yield {"data": json.dumps({"answer": error_msg}, ensure_ascii=False)}

        except Exception as e:
            error_msg = f"系统异常: {str(e)}"
            logger.error(error_msg, exc_info=True)
            yield {"data": json.dumps({"answer": error_msg}, ensure_ascii=False)}
        
        """
        data = {
        "model": modelName,
        "messages": messages,
        "stream": stream
    }
        try:
            response = requests.post(url=url,json=data,stream=stream)
            response.raise_for_status()
            if stream:
                for line in response.iter_lines(decode_unicode=True):

                    if line:
                        
                        # 处理 "data: " 前缀
                        if line.startswith("data: "):
                            line = line[len("data: "):]
                        
                        if line == "[DONE]":
                            break
                        
                        try:
                            chunk = json.loads(line)
                            token = chunk["choices"][0]["delta"].get("content", "")
                            logger.info(f"{token}")
                            yield { "data": json.dumps({"answer": token},ensure_ascii=False)}
                        except json.JSONDecodeError as e:
                            logger.error(f"Failed to decode JSON: {line}")
                            yield {"code": 500, "message": f"Failed to decode JSON: {str(e)}"}
            else:
                result = response.json()["choices"][0]["message"]["content"]
                logger.info(f'{result}')
                yield {"data": json.dumps({"answer": result},ensure_ascii=False)}
                

        except requests.RequestException as e:
            logger.error(f"Request error: {e}")
            yield {"code": 500, "message": f"Request error: {e}"}
        """
        """
        async with aiohttp.ClientSession() as session:
            async with session.post(url=url, json=data) as response:
                if stream:
                    async for line in response.content:
                        line = line.decode('utf-8').strip()
                        if line:
                            try:
                                result = json.loads(line)
                                logger.info(f'{result}')
                                yield result
                            except json.JSONDecodeError:
                                logger.error(f"Failed to decode JSON: {line}")
                else:
                    result = await response.json()
                    logger.info(f'{result}')
                    yield result
        """
        """
        data = {
        "model_path": model_path,
        "messages": messages,
        "stream": stream
    }
        try:
            response = requests.post(url=url, json=data)
            if stream:
                for line in response.iter_lines():
                    line = line.decode('utf-8').strip()
                    if line:
                        try:
                            result = json.loads(line)
                            logger.info(f'{result}')
                            yield result
                        except json.JSONDecodeError as e:
                            logger.error(f"Failed to decode JSON: {line}")
                            yield {"code": 500, "message": f"Failed to decode JSON: {str(e)}"}
            else:
                result = response.json()
                logger.info(f'{result}')
                yield result
        
        except requests.RequestException as e:
            logger.error(f"Request error: {e}")
            yield {"code": 500, "message": f"Request error: {e}"}
        """
        """
        client = OpenAI(api_key=openai_api_key,base_url=openai_api_base)
        
        if stream:
            
            # 创建 Completion 请求
            logger.info("创建流式 Completion 请求")
            async for part in await client.chat.completions.create(model=modelName,messages=messages,stream=stream):
                token = part.choices[0].delta.content or ''
                logger.info(token)
                
                yield { "data": json.dumps({"answer": token},ensure_ascii=False)}
            
        else:
            
            logger.info("创建非流式 Completion 请求")
            response = await client.chat.completions.create(model=modelName,messages=messages)
            logger.info(response.choices[0].message.content)
            
            yield {"data": json.dumps({"answer": response.choices[0].message.content},ensure_ascii=False)}
        """
    
    return EventSourceResponse(event_generator(query=query,history=history,stream=stream,modelName=modelName,temperature=temperature))
    
    
    """(ollama version)
    async def event_generator(query,history,stream,modelName,temperature):
        messages = [
        {
            'role': 'system',
            'content': '你现在的身份是水利科学院文档智能合规审查大模型，擅长对用户给出的文件进行合规性判断。'
        },
        {
            'role': 'user',
            'content': f'{query}'
        },
    ]
    
    # 将history中的字典数据插入到messages列表的第二个位置
        messages[1:1] = history
        
        if stream:
            
            client = AsyncClient()
            async for part in await client.chat(model=modelName, messages=messages, stream=stream):
                token = part['message']['content']
                logger.info(token)
                
                yield { "data": json.dumps({"answer": token},ensure_ascii=False)}
            
        else:
            
            client = AsyncClient()
            response = await client.chat(model=modelName, messages=messages)
            logger.info(response['message']['content'])
            
            yield {
                "data": json.dumps({"answer": response['message']['content']},ensure_ascii=False)
                }
        """
        
    


    