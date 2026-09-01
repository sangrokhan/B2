#!/usr/bin/env python3
"""
B2 Vault Link Fixer
- 깨진 wikilink → 유사 파일명으로 자동 수정 (difflib 기반)
- 불필요한 중복 wikilink 첫 번째 제외 제거
- 재귀/자기참조 링크 제거
- index.md 누락 항목 자동 추가
"""
from __future__ import annotations
import difflib
import os
import re
import sys
from pathlib import Path

VAULT = Path(os.environ.get("B2_VAULT", "/home/han/B2"))
IGNORE_DIRS = {"_maintenance", "Templates", ".git", ".obsidian"}
WIKILINK_RE = re.compile(r"\[\[([^\]|#]+?)(\|[^\]]*)?(#[^\]]*)?\]\]")


def all_stems() -> dict[str, Path]:
    """stem → 경로 맵 (Obsidian shortest-path 방식)"""
    result = {}
    for p in VAULT.rglob("*.md"):
        parts = set(p.relative_to(VAULT).parts)
        if parts & IGNORE_DIRS:
            continue
        result[p.stem] = p
        # slug도 등록
        result[str(p.relative_to(VAULT).with_suffix(""))] = p
    return result


def suggest_fix(link: str, stems: dict[str, Path]) -> str | None:
    """유사 파일명 제안 (0.6 이상 유사도)"""
    matches = difflib.get_close_matches(link, stems.keys(), n=1, cutoff=0.6)
    if matches:
        return matches[0]
    return None


def link_resolves(link: str) -> bool:
    """Obsidian shortest-unique-path 방식으로 링크가 실제로 해석되는지 확인.

    stems 딕셔너리는 stem과 full slug만 담고 있어 "AIPT/구현" 같은 중간
    경로(폴더+stem, full slug보다 짧은) 링크를 놓친다. 그 결과 실제로는
    유효한 링크를 "깨짐"으로 오판해 difflib 유사도 매칭이 엉뚱한 후보
    (예: 부모 문서 "AIPT")로 잘못 고쳐버리는 사고가 있었다 (2026-09-01).
    링크에 "/"가 있으면 경로 suffix가 유일하게 일치하는 파일이 있는지
    먼저 확인하고, 있으면 존재하는 것으로 취급한다.
    """
    if "/" not in link:
        return False
    link_parts = tuple(link.split("/"))
    matches = []
    for p in VAULT.rglob("*.md"):
        parts = p.relative_to(VAULT).parts
        if set(parts) & IGNORE_DIRS:
            continue
        stem_parts = parts[:-1] + (p.stem,)
        if len(stem_parts) >= len(link_parts) and stem_parts[-len(link_parts):] == link_parts:
            matches.append(p)
    return len(matches) == 1


def fix_links_in_file(path: Path, stems: dict[str, Path]) -> tuple[str, list[str]]:
    """파일 내 링크 수정. (새 content, 변경 로그) 반환.

    중복 링크 제거는 "entry 블록" 단위로만 적용한다 (Daily Note/Topic Doc처럼
    한 파일에 conversation-to-obsidian:start/end 또는 topic-doc:start/end로
    구분된 여러 독립 엔트리가 있을 수 있고, 각 엔트리가 같은 문서를 가리키는
    Related 링크를 갖는 것은 의도된 정상 패턴이라 파일 전체 기준으로 dedup하면
    안 된다).
    """
    content = path.read_text(encoding="utf-8")
    source_slug = str(path.relative_to(VAULT).with_suffix(""))
    changes = []

    # 엔트리 경계(각 entry 블록의 start 마커) 기준으로 콘텐츠를 조각내어
    # 조각별로 독립적인 seen_links 카운터를 사용한다. 마커가 없는 파일은
    # 전체를 하나의 조각으로 취급(기존 동작과 동일).
    entry_boundary = re.compile(
        r"(?=<!-- (?:conversation-to-obsidian|topic-doc):start:)"
    )
    segments = entry_boundary.split(content)

    def make_replacer(seen_links: dict[str, int]):
        def replace_link(m: re.Match) -> str:
            link = m.group(1).strip()
            alias = m.group(2) or ""
            anchor = m.group(3) or ""

            # 자기 참조 링크 제거
            if link == path.stem or link == source_slug:
                changes.append(f"자기참조 제거: [[{link}]]")
                return alias[1:] if alias else link  # alias만 텍스트로 남김

            # 링크 존재 확인 (stem/slug 직접 매칭 실패 시 shortest-unique-path suffix 매칭도 시도)
            exists = (
                link in stems
                or (link + ".md") in [str(p.relative_to(VAULT)) for p in stems.values()]
                or link_resolves(link)
            )
            if not exists:
                fix = suggest_fix(link, stems)
                if fix:
                    changes.append(f"링크 수정: [[{link}]] → [[{fix}]]")
                    return f"[[{fix}{alias}{anchor}]]"
                else:
                    # 수정 불가 → 텍스트로 강등
                    changes.append(f"깨진 링크 텍스트 강등: [[{link}]]")
                    return alias[1:] if alias else link

            # 중복 링크 처리 (같은 엔트리 블록 내에서 처음 1회만 유지)
            seen_links[link] = seen_links.get(link, 0) + 1
            if seen_links[link] > 1:
                changes.append(f"중복 링크 제거: [[{link}]] (#{seen_links[link]})")
                return alias[1:] if alias else link

            return m.group(0)  # 변경 없음
        return replace_link

    new_segments = []
    for seg in segments:
        seen_links: dict[str, int] = {}
        new_segments.append(WIKILINK_RE.sub(make_replacer(seen_links), seg))
    new_content = "".join(new_segments)
    return new_content, changes


def update_index(index_path: Path, stems: dict[str, Path], vault: Path) -> list[str]:
    """index.md에 누락된 Knowledge/Projects/Dev 파일 추가"""
    if not index_path.exists():
        return []

    content = index_path.read_text(encoding="utf-8")
    changes = []
    TRACK_DIRS = ["Knowledge", "Projects", "Dev"]

    for p in vault.rglob("*.md"):
        parts = p.relative_to(vault).parts
        if not parts or parts[0] not in TRACK_DIRS:
            continue
        if p.name in {"README.md", "index.md"}:
            continue
        parts_set = set(parts)
        if parts_set & IGNORE_DIRS:
            continue

        slug_str = str(p.relative_to(vault).with_suffix(""))
        stem = p.stem

        if f"[[{slug_str}" not in content and f"[[{stem}" not in content and stem not in content:
            # 해당 섹션 찾아서 추가
            section = parts[0]  # Knowledge, Projects, Dev
            section_header = f"## 🧠 Knowledge" if section == "Knowledge" else \
                             f"## 🚀 Projects" if section == "Projects" else \
                             f"## 📁 Dev Notes"
            entry = f"- [[{slug_str}|{stem}]]"

            if section_header in content:
                # 섹션 다음 줄에 추가
                content = content.replace(
                    section_header + "\n",
                    section_header + "\n" + entry + "\n"
                )
                changes.append(f"index.md 추가: {slug_str}")
            else:
                # 섹션 없으면 맨 끝에 추가
                content = content.rstrip() + f"\n\n{section_header}\n{entry}\n"
                changes.append(f"index.md 새 섹션 추가: {slug_str}")

    if changes:
        index_path.write_text(content, encoding="utf-8")

    return changes


def main():
    stems = all_stems()
    total_changes = []

    # 1. 링크 수정 (자기참조, 깨진 링크, 중복)
    for p in VAULT.rglob("*.md"):
        parts = set(p.relative_to(VAULT).parts)
        if parts & IGNORE_DIRS:
            continue
        new_content, changes = fix_links_in_file(p, stems)
        if changes:
            p.write_text(new_content, encoding="utf-8")
            for ch in changes:
                print(f"  [{p.relative_to(VAULT)}] {ch}")
                total_changes.append(ch)

    # 2. index.md 업데이트
    index_changes = update_index(VAULT / "index.md", stems, VAULT)
    for ch in index_changes:
        print(f"  [index.md] {ch}")
        total_changes.append(ch)

    print(f"\n총 변경: {len(total_changes)}건")


if __name__ == "__main__":
    main()
