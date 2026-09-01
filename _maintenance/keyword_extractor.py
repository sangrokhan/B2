#!/usr/bin/env python3
"""
B2 Vault Keyword Extractor
각 .md 파일에서 키워드를 추출해 frontmatter tags에 추가/갱신.
- 한국어/영어 혼합 텍스트 지원
- 기존 tags는 보존하고 새 키워드만 추가
- stopword 필터링
- 빈도 기반 상위 N개 추출
"""
from __future__ import annotations
import os
import re
import sys
from collections import Counter
from pathlib import Path

VAULT = Path(os.environ.get("B2_VAULT", "/home/han/B2"))
IGNORE_DIRS = {"_maintenance", "Templates", ".git", ".obsidian", "_context", "Daily Notes"}
IGNORE_FILES = {"index.md", "Dashboard.md", "README.md"}

# 한국어 & 영어 stopwords
KO_STOPS = {
    "이", "그", "저", "것", "수", "등", "및", "또한", "하지만", "그리고", "또는",
    "에서", "으로", "에게", "에", "은", "는", "이", "가", "을", "를", "의", "와", "과",
    "도", "만", "까지", "부터", "에서", "한", "하는", "된", "되는", "있는", "없는",
    "있다", "없다", "한다", "된다", "되다", "하다", "이다", "아니다",
    "때", "후", "전", "중", "안", "밖", "위", "아래", "함", "함께", "통해", "대한",
    "관한", "위한", "따른", "기반", "사용", "구현", "설계", "작업", "방식", "방법"
}
EN_STOPS = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could", "should",
    "may", "might", "shall", "can", "need", "dare", "ought", "used",
    "and", "but", "or", "nor", "for", "yet", "so", "at", "by", "in", "of",
    "on", "to", "up", "as", "it", "its", "this", "that", "these", "those",
    "with", "from", "into", "through", "during", "before", "after", "above",
    "below", "between", "out", "off", "over", "under", "again", "further",
    "then", "once", "here", "there", "when", "where", "why", "how", "all",
    "each", "both", "few", "more", "most", "other", "some", "such", "no",
    "not", "only", "same", "than", "too", "very", "just", "because", "if",
    "while", "about", "against", "also", "use", "using", "used", "based",
    "design", "implementation", "approach", "method", "way", "work", "task"
}
STOPS = KO_STOPS | EN_STOPS

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\s*\n?", re.DOTALL)
TAGS_RE = re.compile(r"^tags:\s*\[(.+?)\]", re.MULTILINE)
TAGS_LIST_RE = re.compile(r"^tags:\s*\n((?:\s+-\s*.+\n?)+)", re.MULTILINE)


def extract_text(content: str) -> str:
    """frontmatter 및 코드 블록 제거 후 텍스트 반환"""
    text = FRONTMATTER_RE.sub("", content)
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    text = re.sub(r"`[^`]+`", "", text)
    text = re.sub(r"\[\[([^\]|#]+?)(?:[|#][^\]]*?)?\]\]", r"\1", text)  # wikilink → 텍스트
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)  # markdown link → 텍스트
    text = re.sub(r"[#*_~>|]", " ", text)  # 마크다운 기호 제거
    return text


def tokenize(text: str) -> list[str]:
    """단어 토큰 추출 (한국어 어절 + 영어 단어)"""
    tokens = []
    # 영어 단어
    for word in re.findall(r"[a-zA-Z][a-zA-Z0-9\-]{2,}", text):
        tokens.append(word.lower())
    # 한국어 명사류 패턴 (2글자 이상 한글)
    for word in re.findall(r"[가-힣]{2,}", text):
        tokens.append(word)
    return tokens


def top_keywords(tokens: list[str], n: int = 8) -> list[str]:
    filtered = [t for t in tokens if t not in STOPS and len(t) >= 2]
    counts = Counter(filtered)
    return [kw for kw, _ in counts.most_common(n)]


def get_existing_tags(content: str) -> list[str]:
    # tags: [a, b, c] 형식
    m = TAGS_RE.search(content)
    if m:
        return [t.strip().strip('"').strip("'") for t in m.group(1).split(",")]
    # tags:\n  - a\n  - b 형식
    m = TAGS_LIST_RE.search(content)
    if m:
        return [re.sub(r"^\s*-\s*", "", l).strip() for l in m.group(1).splitlines() if l.strip()]
    return []


def add_tags_to_frontmatter(content: str, new_tags: list[str]) -> tuple[str, bool]:
    """tags를 frontmatter에 추가/갱신. 변경 여부 반환."""
    if not new_tags:
        return content, False

    existing = get_existing_tags(content)
    all_tags = list(dict.fromkeys(existing + [t for t in new_tags if t not in existing]))

    if all_tags == existing:
        return content, False

    tags_line = f"tags: [{', '.join(all_tags)}]"

    # 기존 tags 라인 교체
    if TAGS_RE.search(content):
        new_content = TAGS_RE.sub(tags_line, content, count=1)
        return new_content, True
    if TAGS_LIST_RE.search(content):
        new_content = TAGS_LIST_RE.sub(tags_line + "\n", content, count=1)
        return new_content, True

    # frontmatter에 tags 없음 → 추가
    fm_match = FRONTMATTER_RE.match(content)
    if fm_match:
        fm_body = fm_match.group(1)
        rest = content[fm_match.end():]
        new_fm = f"---\n{fm_body}\n{tags_line}\n---\n"
        new_content = new_fm + rest
        return new_content, True

    # frontmatter 자체 없음 → 맨 앞에 삽입
    new_content = f"---\n{tags_line}\n---\n\n" + content
    return new_content, True


def process_file(path: Path) -> dict:
    content = path.read_text(encoding="utf-8")
    text = extract_text(content)
    tokens = tokenize(text)
    keywords = top_keywords(tokens)
    updated, changed = add_tags_to_frontmatter(content, keywords)
    if changed:
        path.write_text(updated, encoding="utf-8")
    return {"file": str(path.relative_to(VAULT)), "keywords": keywords, "changed": changed}


def main():
    results = []
    changed_files = []
    for p in VAULT.rglob("*.md"):
        parts = set(p.relative_to(VAULT).parts)
        if parts & IGNORE_DIRS:
            continue
        if p.name in IGNORE_FILES:
            continue
        r = process_file(p)
        results.append(r)
        if r["changed"]:
            changed_files.append(r["file"])

    print(f"처리: {len(results)}개 파일")
    print(f"키워드 업데이트: {len(changed_files)}개")
    for cf in changed_files:
        print(f"  ✎ {cf}")
    for r in results:
        print(f"  [{r['file']}] → {', '.join(r['keywords'])}")


if __name__ == "__main__":
    main()
