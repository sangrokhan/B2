#!/usr/bin/env python3
"""
B2 Vault Lint & Maintenance Script
- 깨진 wikilink 탐지
- 고아 페이지(inbound 링크 없음) 탐지
- 재귀/순환 참조 탐지
- frontmatter 누락 검사
- index.md 누락 항목 탐지
- 페이지 크기 초과 검사 (200줄)
- 중복 wikilink 탐지

출력: JSON (stdout)
"""
from __future__ import annotations
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

VAULT = Path(os.environ.get("B2_VAULT", "/home/han/B2"))

# 유지보수 스크립트가 신경 쓸 폴더 (Templates, _context, _maintenance 제외)
WIKI_DIRS = ["Daily Notes", "Knowledge", "Projects", "Dev"]
# index.md에서 관리되어야 할 폴더
INDEX_DIRS = ["Knowledge", "Projects", "Dev"]

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---", re.DOTALL)
WIKILINK_RE = re.compile(r"\[\[([^\]|#]+?)(?:[|#][^\]]*?)?\]\]")
IGNORE_DIRS = {"_maintenance", "Templates", ".git", ".obsidian"}


def all_md_files() -> list[Path]:
    """vault 전체 .md 파일 수집 (ignore 폴더 제외)"""
    results = []
    for p in VAULT.rglob("*.md"):
        parts = set(p.relative_to(VAULT).parts)
        if parts & IGNORE_DIRS:
            continue
        results.append(p)
    return results


def slug(path: Path) -> str:
    """파일의 vault-relative 경로 (확장자 없이)"""
    return str(path.relative_to(VAULT).with_suffix(""))


def resolve_wikilink(link: str, source_path: Path) -> Path | None:
    """wikilink → 실제 파일 경로 (Obsidian shortest-path 방식)

    Obsidian은 "/"가 포함된 링크도 vault 루트 기준 절대경로 하나만 보는 게
    아니라, 경로 suffix가 유일하게 일치하는 파일을 찾는 shortest-unique-path
    매칭을 쓴다 (예: "AIPT/구현"은 실제로 "Projects/AIPT/AIPT/구현.md"처럼
    더 깊은 폴더에 있어도 매칭됨). 그래서 절대경로 매칭이 실패하면 suffix
    매칭으로 한 번 더 시도한다.
    """
    link = link.strip()
    # 1) 절대 경로(vault 루트 기준) 형식
    if "/" in link:
        candidate = VAULT / (link + ".md")
        if candidate.exists():
            return candidate
        # 2) suffix 매칭: 경로 끝부분이 링크와 일치하는 파일을 vault 전체에서 탐색
        link_parts = tuple(link.split("/"))
        matches = []
        for p in VAULT.rglob("*.md"):
            parts = p.relative_to(VAULT).parts
            if set(parts) & IGNORE_DIRS:
                continue
            stem_parts = parts[:-1] + (p.stem,)
            if len(stem_parts) >= len(link_parts) and stem_parts[-len(link_parts):] == link_parts:
                matches.append(p)
        if len(matches) == 1:
            return matches[0]
        return None
    # 최단 경로: vault 전체에서 stem 매칭
    for p in VAULT.rglob(f"{link}.md"):
        parts = set(p.relative_to(VAULT).parts)
        if not (parts & IGNORE_DIRS):
            return p
    return None


def parse_frontmatter(content: str) -> dict:
    m = FRONTMATTER_RE.match(content)
    if not m:
        return {}
    fm = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            fm[k.strip()] = v.strip()
    return fm


def extract_wikilinks(content: str) -> list[str]:
    return WIKILINK_RE.findall(content)


def find_circular_refs(graph: dict[str, set[str]]) -> list[list[str]]:
    """DFS로 순환 참조 탐지 (짧은 사이클만)"""
    cycles = []
    visited = set()
    path = []
    path_set = set()

    def dfs(node):
        if node in path_set:
            idx = path.index(node)
            cycle = path[idx:] + [node]
            if len(cycle) <= 4:  # 너무 긴 사이클은 노이즈
                cycles.append(cycle)
            return
        if node in visited:
            return
        visited.add(node)
        path.append(node)
        path_set.add(node)
        for neighbor in graph.get(node, set()):
            dfs(neighbor)
        path.pop()
        path_set.discard(node)

    for node in list(graph.keys()):
        if node not in visited:
            dfs(node)
    # 중복 제거
    seen = set()
    unique = []
    for c in cycles:
        key = frozenset(c)
        if key not in seen:
            seen.add(key)
            unique.append(c)
    return unique


def main():
    files = all_md_files()
    file_slugs = {slug(f): f for f in files}

    # 링크 그래프 구성
    outlinks: dict[str, list[str]] = {}  # slug → [linked slug]
    broken: list[dict] = []
    all_wikilinks_per_file: dict[str, list[str]] = {}

    for f in files:
        content = f.read_text(encoding="utf-8")
        links = extract_wikilinks(content)
        resolved = []
        for link in links:
            target = resolve_wikilink(link, f)
            if target is None:
                broken.append({"file": slug(f), "link": link})
            else:
                resolved.append(slug(target))
        outlinks[slug(f)] = resolved
        all_wikilinks_per_file[slug(f)] = links

    # inbound 링크 맵
    inbound: dict[str, list[str]] = defaultdict(list)
    for src, targets in outlinks.items():
        for tgt in targets:
            inbound[tgt].append(src)

    # 고아 페이지 (inbound 없고, index/dashboard/daily notes 제외)
    orphans = []
    for s, f in file_slugs.items():
        parts = f.relative_to(VAULT).parts
        skip_prefixes = ("Daily Notes", "_context", "index", "Dashboard", "README", "_maintenance")
        if any(s.startswith(p) for p in skip_prefixes):
            continue
        if not inbound.get(s):
            orphans.append(s)

    # 순환 참조
    graph = {s: set(ts) for s, ts in outlinks.items()}
    cycles = find_circular_refs(graph)

    # frontmatter 누락
    no_frontmatter = []
    for f in files:
        parts = f.relative_to(VAULT).parts
        if parts[0] in ("Daily Notes", "_context", "_maintenance"):
            continue
        content = f.read_text(encoding="utf-8")
        fm = parse_frontmatter(content)
        if not fm:
            no_frontmatter.append(slug(f))

    # 페이지 크기 초과
    oversized = []
    for f in files:
        lines = f.read_text(encoding="utf-8").count("\n")
        if lines > 200:
            oversized.append({"file": slug(f), "lines": lines})

    # 중복 wikilink
    # Daily Note/Topic Doc처럼 entry 블록(conversation-to-obsidian/topic-doc
    # start~end)이 여러 개 있는 파일은 "같은 문서를 가리키는 Related 링크가
    # 엔트리마다 반복되는 것"이 의도된 정상 패턴이므로, 파일 전체가 아니라
    # entry 블록 단위로 중복을 판정한다. 엔트리 마커가 없는 일반 파일은
    # 기존처럼 파일 전체 기준으로 판정.
    entry_boundary_re = re.compile(
        r"(?=<!-- (?:conversation-to-obsidian|topic-doc):start:)"
    )
    duplicate_links = []
    for s, links in all_wikilinks_per_file.items():
        f = file_slugs[s]
        content = f.read_text(encoding="utf-8")
        if entry_boundary_re.search(content):
            dups: dict[str, int] = {}
            for seg in entry_boundary_re.split(content):
                seg_links = extract_wikilinks(seg)
                counts = defaultdict(int)
                for lnk in seg_links:
                    counts[lnk] += 1
                for lnk, cnt in counts.items():
                    if cnt > 1:
                        dups[lnk] = max(dups.get(lnk, 0), cnt)
        else:
            counts = defaultdict(int)
            for lnk in links:
                counts[lnk] += 1
            dups = {lnk: cnt for lnk, cnt in counts.items() if cnt > 1}
        if dups:
            duplicate_links.append({"file": s, "duplicates": dups})

    # index.md 누락 항목
    index_path = VAULT / "index.md"
    index_content = index_path.read_text(encoding="utf-8") if index_path.exists() else ""
    missing_from_index = []
    for s, f in file_slugs.items():
        parts = f.relative_to(VAULT).parts
        if parts[0] not in INDEX_DIRS:
            continue
        stem = f.stem
        if f"[[{s}" not in index_content and f"[[{stem}" not in index_content and stem not in index_content:
            missing_from_index.append(s)

    result = {
        "total_files": len(files),
        "broken_links": broken,
        "orphan_pages": orphans,
        "circular_refs": cycles,
        "missing_frontmatter": no_frontmatter,
        "oversized_pages": oversized,
        "duplicate_links": duplicate_links,
        "missing_from_index": missing_from_index,
        "severity": {
            "critical": len(broken) + len(cycles),
            "warning": len(orphans) + len(missing_from_index) + len(no_frontmatter),
            "info": len(oversized) + len(duplicate_links),
        }
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
