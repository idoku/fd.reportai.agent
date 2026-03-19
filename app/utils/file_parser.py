import pandas as pd
import os
from typing import Any
from pathlib import Path
from docx import Document

EXPORT_DIR = Path(os.getcwd()) / "exports"


def load_txt_lines(file_path: str) -> list[str]:
    with open(file_path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]
    

def load_txt(file_path: str) -> str:
    """读取 txt 文件内容"""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {file_path}")
    
    # 读取时显式声明编码，防止中文乱码
    with path.open("r", encoding="utf-8") as f:
        content = f.read()
    return content


def load_docx(file_path: str) -> str:
    """
    读取 .doc 或 .docx 文件内容并返回纯文本。
    - .docx 直接用 python-docx 解析。
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {file_path}")

    ext = path.suffix.lower()
    text = ""

    if ext == ".docx":
        doc = Document(str(path))
        text = "\n".join(p.text.strip() for p in doc.paragraphs if p.text.strip())
    else:
        raise ValueError(f"不支持的文件类型: {ext}")

    return text.strip()

def load_excel(file_path: str, columns: list = None):
    """
    加载并打印指定列的Excel文件内容。
    :param file_path: Excel文件的路径
    :param columns: 需要读取的列名或列索引
    """
    if not os.path.exists(file_path):
        print(f"错误: 文件 '{file_path}' 不存在。")
        return
    
    try:
        # 使用pandas读取Excel文件
        df = pd.read_excel(file_path)
        
        # 如果指定了需要的列，筛选出来
        missing_columns = [col for col in columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"缺少以下列: {', '.join(missing_columns)}")
        return df[columns]
        # 打印文件内容（前几行）
        # print(f"文件内容（前几行）：\n{df.head()}")
        return df
    except Exception as e:
        print(f"错误: 无法读取文件 '{file_path}'，原因: {e}")



def export_to_excel(data: list[Any], file_name: str = "output.xlsx"):
    """
    通用对象列表导出为 Excel（支持 Pydantic 或有 .dict() 方法的类）

    Args:
        data: list[Any] - 一组拥有 .dict() 方法的对象（如 Pydantic/BaseModel）
        file_path: str - 保存路径（支持绝对或相对路径）
    """
    if not data:
        raise ValueError("导出数据为空")
    # 尝试将对象转换为 dict
    try:
        rows = [obj.dict() for obj in data]
    except AttributeError as e:
        raise TypeError("所有对象必须具有 .dict() 方法（如 Pydantic 模型）") from e
    df = pd.DataFrame(rows)
    file_path = EXPORT_DIR / file_name
    Path(file_path).parent.mkdir(parents=True, exist_ok=True)       
    df.to_excel(file_path, index=False, engine="openpyxl")