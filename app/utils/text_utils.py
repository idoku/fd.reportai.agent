
import re
from typing import List

def extract_user_prompt(text):
    # 如果有 <think>...</think>，去掉它和中间内容，只取后面有效部分
    pattern = r'<think>.*?</think>\s*'
    cleaned = re.sub(pattern, '', text, flags=re.DOTALL)
    # 再去掉多余的空行
    return cleaned.strip()

import re
import json

def extract_clean_json(text: str) -> str:
    # 1. 清除 <think>...</think> 块
    cleaned = re.sub(r'<think>.*?</think>\s*', '', text, flags=re.DOTALL)

    # 2. 清除 markdown 的 ```json 包裹
    cleaned = re.sub(r'^```json\s*', '', cleaned.strip(), flags=re.IGNORECASE)
    cleaned = re.sub(r'\s*```$', '', cleaned.strip())

    # 3. 替换掉字符串里的 \n（而不是实际换行）
    cleaned = cleaned.replace("\\n", " ")

    # 4. 去掉 JSON 里末尾的逗号（对象或数组结尾）
    cleaned = re.sub(r',\s*([}\]])', r'\1', cleaned)

    # 5. 去掉可能单独出现的引号+换行符片段（如 "\"\n    "）
    cleaned = re.sub(r'"\s*\n\s*"', '', cleaned)
    cleaned = re.sub(r'(?m)(?<!")\b([A-Za-z_][A-Za-z0-9_]*)\b(?=\s*:)', r'"\1"', cleaned)
    # 6. 尝试加载一次 JSON，确保合法
    try:
        obj = json.loads(cleaned)
        # 再 dump 回来，保证格式标准化（避免多余空格）
        cleaned = json.dumps(obj, ensure_ascii=False, indent=3)
    except Exception:
        # 如果不能解析，就原样返回（至少清理过了）
        pass

    return cleaned.strip()



def split_by_tokens(text: str, max_tokens: int = 2000) -> List[str]:
    """
    粗略按 token 长度估算将文本分段（中文 1 字 ≈ 1 token，英文词 ≈ 1-2 token）
    :param text: 原始文本
    :param max_tokens: 每段最大长度（默认2000 token）
    :return: 文本段落列表
    """
    # 先按自然段落（标点或换行）粗切
    # 中文句号、分号、换行、英文句号
    sentences = re.split(r'(?<=[。；;\\.!?？])|\\n', text)

    chunks = []
    current_chunk = ""
    current_length = 0

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        # 粗略估算：1汉字=1 token，1英文单词≈1.3 token
        sentence_length = len(sentence)

        if current_length + sentence_length > max_tokens:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = sentence
            current_length = sentence_length
        else:
            current_chunk += sentence
            current_length += sentence_length

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks
