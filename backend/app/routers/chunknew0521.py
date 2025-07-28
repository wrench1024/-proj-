import re
from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter


#先按正常最大块限制进行切割，再遍历每个文本块
#    如果文本块中不含被切断的表格，则不做处理，
#    如果切割后的文本块含有被切断的表格，则将该表格及其前面可能存在的表XXX信息单独切分为一个文本块，此时只包含表格及其附属信息的文本块没最大字符限制，
#    文本块排列顺序符合原文上下文顺序
def process_markdown_file(file_path=None, documents=None,max_chunk_size=4500, chunk_overlap=0):

    if file_path is not None:
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                markdown_text = file.read()
                final_chunks=text_split(max_chunk_size, chunk_overlap,markdown_text,file_path)
                return final_chunks
        except FileNotFoundError:
            print(f"错误: 文件 {file_path} 未找到。")
            return []
    elif documents is not None:
        try:
            final_chunks = []
            for markdown_text in documents:
                final_chunks.append(text_split(max_chunk_size,chunk_overlap,markdown_text))
            return final_chunks
        except Exception as e:
            print(f"错误: 发生了未知错误: {e}")
            return []
    else:
        print("错误: file_path和documents至少需要一项")
        return []

def text_split(max_chunk_size, chunk_overlap,markdown_text,file_path=None):
    # 识别目录
    toc_start = -1
    lines = markdown_text.split('\n')
    search_range = max(1, len(lines) // 4)  # 只搜索前1/4部分，至少搜索1行

    pattern = re.compile(
        r'^[^\u4e00-\u9fa5]*?(目\s*录|C\s*O\s*N\s*T\s*E\s*N\s*T\s*S)[^\u4e00-\u9fa5]*$',
        re.IGNORECASE | re.MULTILINE
    )

    # 仅在前1/4的行中搜索目录标题
    for i in range(search_range):
        line = lines[i]
        if pattern.search(line):
            toc_start = i
            break

    if toc_start != -1:
        # 检查目录行的上一行和下一行是否为非汉字字符（确保是独立标题）
        prev_line = lines[toc_start - 1] if toc_start > 0 else ""
        next_line = lines[toc_start + 1] if toc_start < len(lines) - 1 else ""

        # 前后行需满足非汉字字符为主（可选增强条件）
        if re.match(r'^[^\u4e00-\u9fa5]*$', prev_line) and re.match(r'^[^\u4e00-\u9fa5]*$', next_line):
            chunk_ini = '\n'.join(lines[:toc_start - 1]) if toc_start > 1 else ""
            markdown_text = '\n'.join(lines[toc_start:])
        else:
            chunk_ini = ""  # 前后有汉字，视为普通文本
    else:
        chunk_ini = ""  # 前1/4部分未找到目录标题
    # 先按正常逻辑分割文本
    if file_path is not None:
        document = Document(page_content=markdown_text, metadata={"source": file_path})
    else:
        document = Document(page_content=markdown_text, metadata={})
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=max_chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n# ", "\n## ", "\n### ", "\n#### "],
        keep_separator=True
    )
    split_docs = text_splitter.split_documents([document])
    initial_chunks = [doc.page_content for doc in split_docs]

    final_chunks = []
    i = 0
    n = len(initial_chunks)

    while i < n:
        chunk = initial_chunks[i]
        if isinstance(chunk, list):
            print(f"Error: chunk is a list: {chunk}")  # 打印调试信息
        assert isinstance(chunk, str), f"chunk should be a string, but got {type(chunk)}"
        if len(chunk)>=8000:
            table_start_count = chunk.count('<table')
            table_end_count = chunk.count('</table>')
            if table_start_count==table_end_count and table_start_count>1:
                first_table_end = initial_chunks[i].find('</table>')
                table_end_pos = first_table_end + len('</table>')
                final_chunks.append(initial_chunks[i][:table_end_pos])
                initial_chunks[i]=initial_chunks[i][table_end_pos:]
                if len(initial_chunks[i])>=8000:
                    continue
            elif table_start_count==table_end_count and table_start_count==1:
                table_start = initial_chunks[i].find('<table')
                table_end = initial_chunks[i].find('</table>')+len('</table>')
                if len(chunk[:table_start])>len(chunk[table_end:]) and len(chunk[:table_start])>400:
                    final_chunks.append(initial_chunks[i][:table_start-1])
                    final_chunks.append(initial_chunks[i][table_start:])
                elif len(chunk[:table_start])<=len(chunk[table_end:]) and len(chunk[table_end+1:])>400:
                    final_chunks.append(chunk[:table_end])
                    final_chunks.append(chunk[table_end+1:])
                else:
                    final_chunks.append(chunk)
                i+=1
            else:
                final_chunks.append(chunk)
                i+=1
        else:
            if len(chunk) <= 500 and i+1<n:
                if chunk.strip() != '':
                    initial_chunks[i + 1] = chunk + initial_chunks[i + 1]
            else:
                final_chunks.append(chunk)
            i+=1
    #目录前的内容
    if chunk_ini.strip() != '':
        final_chunks.insert(0, chunk_ini)
    return final_chunks

if __name__ == "__main__":
    # # 请将此路径替换为你实际的 Markdown 文件路径
    # test_file_path = "/home/zyw/shuikeyuan-daily/2021年六盘水市水资源公报.md"
    # chunks = process_markdown_file(test_file_path)
    # for i, chunk in enumerate(chunks, start=1):
    #     print(f"Chunk {i} (Length: {len(chunk)}):")
    #     print(chunk)
    #     print("-" * 50)
    # test_file_path = "/home/ysdx2025/shuikeyuan/file/贵州盘江电投发电有限公司盘县电厂1、2号机组项目取水量调整水资源论证报告书  修改稿/txt/贵州盘江电投发电有限公司盘县电厂1、2号机组项目取水量调整水资源论证报告书  修改稿.md"
    test_file_path="/home/ysdx2025/shuikeyuan/file/《建设项目水资源论证导则 第6部分：造纸行业建设项目》（SLT 525.6-2021）/txt/《建设项目水资源论证导则 第6部分：造纸行业建设项目》（SLT 525.6-2021）.md"
    chunks = process_markdown_file(test_file_path)
    for i, chunk in enumerate(chunks, start=1):
        # 打开文件（'w' 模式：写入，会覆盖原有内容；'a' 模式：追加）
        with open("output_chunk.txt", "a", encoding="utf-8") as f:
            # 写入字符串到文件
            f.write(f"Chunk {i} (Length: {len(chunk)}):\n")
            f.write(chunk+"\n")
            f.write("-"*50+"\n")

    print("内容已保存到 output.txt 文件中。")







