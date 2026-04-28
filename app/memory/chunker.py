import re


# 将文本分割成多个段落，每个段落不超过max_chars个字符，并且段落之间有overlap个字符的重叠
# 分割逻辑
def chunk_text(text: str,max_chars: int = 512, overlap: int = 64) -> list[str]:
    paragraphs = [p.strip() for p in re.split(r'\n{2,}', text) if p.strip()]
    chunks, buffer = [], ""
    for para in paragraphs:
        if len(buffer) + len(para) <= max_chars:
            buffer = (buffer + "\n\n" + para).strip()
        else:
            if buffer:
                chunks.append(buffer.strip())
            if len(para) <= max_chars:
                buffer = para.strip()    
            
            else:
                for i in range(0, len(para), max_chars - overlap):
                    chunks.append(para[i:i+max_chars].strip())

                buffer = ""

    if buffer: 
        chunks.append(buffer)

    return chunks                    
