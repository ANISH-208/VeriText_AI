import re


def normalize_text(text: str) -> str:
    text = text.replace("\u00a0", " ").replace("\r\n", "\n").replace("\r", "\n")
    return re.sub(r"[ \t]+", " ", re.sub(r"\n{3,}", "\n\n", text)).strip()


def split_passages(text: str) -> list[str]:
    text = normalize_text(text)
    # Preserve paragraph chunks where possible, then split long paragraphs into sentences.
    parts: list[str] = []
    for paragraph in re.split(r"\n\s*\n", text):
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"'])", paragraph)
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            words = sentence.split()
            if len(words) > 160:
                parts.extend(" ".join(words[i:i + 160]) for i in range(0, len(words), 160))
            else:
                parts.append(sentence)
    return parts or ([text] if text else [])


def word_count(text: str) -> int:
    return len(re.findall(r"\b[\w’'-]+\b", text))
