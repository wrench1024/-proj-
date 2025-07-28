"""
writer: shengbo meng
date: 2025/5/8
合并后的智能问答接口（布尔模式区分纯大模型和知识库问答，保留原始messages构建逻辑）
"""

from fastapi import APIRouter, Request, Body, Response
from app.core.config import get_logger
from sse_starlette.sse import EventSourceResponse
from openai import AsyncOpenAI
from typing import Optional,List
from routers.knowledge_inter import retrieval
import json

client = AsyncOpenAI(
    api_key="sk-762b0529add947b081778614c7fe1cda",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)

router = APIRouter()
logger = get_logger(__name__)

@router.options("/intelligent_chat/")
async def options_intelligent_chat(request: Request):
    response = Response(status_code=204)
    response.headers["Allow"] = "POST"
    return response

@router.post("/intelligent_chat/")
async def intelligent_chat(
    useKnowledgeBase: bool = Body(True, description="选择问答模式：True=知识库问答，False=纯大模型问答（默认True）"),
    kbId: Optional[List[str]] = Body(None, description="知识库编号（仅知识库问答模式需要）"),
    query: str = Body(..., description='用户输入', examples=["你是谁"]),
    history: list = Body([], description="历史对话记录"),
    stream: bool = Body(True, description="是否流式输出"),
    modelName: str = Body('deepseek-r1', description='模型名称'),
    temperature: float = Body(0.1, description="LLM 采样温度"),
    limit: int = Body(10, description="查询最相关的limit个结果（仅知识库问答模式有效）"),
    show_reasoning: bool = Body(True, description="是否输出模型思考过程（仅支持特定思考类模型）"),
    similarityThreshold: float = Body(default=0.1, description="相似度阈值参数"),
    workers: int = Body(default=10)
):
    async def event_generator():
        
        try:
            
            if not useKnowledgeBase:  # 纯大模型模式
                async for item in handle_pure_llm(query, history, stream, modelName, temperature, show_reasoning):
                    yield item
            
            else:  # 知识库问答模式
                async for item in handle_knowledge_qa(query, history, stream, modelName, temperature, kbId, limit, show_reasoning, similarityThreshold):
                    yield item
        
        except Exception as e:
            error_msg = f"系统异常: {str(e)}"
            logger.error(error_msg, exc_info=True)
            yield {"data": json.dumps({"answer": error_msg}, ensure_ascii=False)}

    async def handle_pure_llm(query, history, stream, modelName, temperature, show_reasoning):
        # 纯大模型逻辑
        max_length = 129024 if modelName == 'qwen-max-latest' else 57344
        if len(query) > max_length:
            query = query[:max_length]
        messages = [
            {"role": "system", "content": "你现在的身份是珠江水利科学院智能问答大模型"},
            {"role": "user", "content": query}
        ]
        messages[1:1] = history
        #logger.info(f"完整的对话消息: {messages}")
        # 迭代LLM调用生成器并传递结果
        async for chunk in call_llm(messages, stream, modelName, temperature, show_reasoning):
            yield chunk

    async def handle_knowledge_qa(query, history, stream, modelName, temperature, kbId, limit, show_reasoning, similarityThreshold):
        # 知识库问答逻辑
        if not kbId:
            logger.warning("知识库问答模式未提供kbId，使用默认知识库检索")
        source = retrieval(kbId=kbId, query=query, limit=limit, similarityThreshold=similarityThreshold,workers=workers)
        files = source.get("files", [])
        input_prompt = f"请依据检索结果，精准回答用户问题，若检索结果与问题无关，可直接基于知识作答。用户问题:{query}\n检索结果:{files}\n"
        
        max_length = 129024 if modelName == 'qwen-max-latest' else 57344
        if len(input_prompt) > max_length:
            input_prompt = input_prompt[:max_length]
        
        messages = [
            {"role": "system", "content": "你现在的身份是水利科学院文档智能问答大模型"},
            {"role": "user", "content": input_prompt}
        ]
        
        # 将history插入到system消息之后、user消息之前（原始逻辑）
        messages[1:1] = history
        #logger.info(f"完整的对话消息: {messages}")
        
        # 迭代LLM调用生成器并传递结果
        async for chunk in call_llm(messages, stream, modelName, temperature, show_reasoning, files=files):
            yield chunk
    
    async def call_llm(messages, stream, modelName, temperature, show_reasoning, files=None):
        # 通用LLM调用逻辑（处理两种模式的响应）
        if stream:
            async for part in await client.chat.completions.create(
                model=modelName,
                messages=messages,
                stream=True,
                temperature=temperature,
                max_tokens=4096
            ):
                
                if not part.choices:
                    continue
                
                delta = part.choices[0].delta
                chunk_data = {}
                
                if hasattr(delta, 'content') and delta.content:
                    chunk_data["answer"] = delta.content
                
                # 提取思考过程（仅当show_reasoning=True且模型返回时）
                if show_reasoning and hasattr(delta, 'reasoning_content'):
                    delta_reasoning = getattr(delta, 'reasoning_content', None)
                    if delta_reasoning:
                        chunk_data["reasoning"] = delta_reasoning
                
                if chunk_data:
                    #logger.info(chunk_data)
                    yield {"data": json.dumps(chunk_data, ensure_ascii=False)}
            
            # 知识库模式补充files信息（仅在流式结束后发送一次）
            if useKnowledgeBase:
                yield {"data": json.dumps({"files": files}, ensure_ascii=False)}
                
        else:
            
            response = await client.chat.completions.create(
                model=modelName,
                messages=messages,
                temperature=temperature
            )
            
            result = {"answer": response.choices[0].message.content}
            
            if show_reasoning and hasattr(response.choices[0].message, 'reasoning_content'):
                result["reasoning"] = response.choices[0].message.reasoning_content
            
            if useKnowledgeBase:
                result["files"] = files
           
            #logger.info(result)   
            yield {"data": json.dumps(result, ensure_ascii=False)}

    return EventSourceResponse(event_generator())
    