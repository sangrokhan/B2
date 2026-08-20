# B2 Knowledge Context

> Claude Code, Hermes 등 AI 도구가 이 파일을 읽어 현재 프로젝트 상태를 파악한다.
> Wikilink 없이 자립적으로 유지. 대화 후 Hermes가 자동 업데이트.

---

## Active Projects

| 프로젝트 | 경로 | 스택 | 상태 |
|---|---|---|---|
| ai-imps | `Projects/ai-imps/` | Python, AI 알고리즘 구현/연구 | 진행중 |
| fin_calculator | `Projects/fin_calculator/` | React, 금융 계산기 | 진행중 |
| remote_work/stat_graph_vis | `Projects/remote_work/` | NetworkX, Pyvis, 통계 시각화 | 진행중 (PR#38) |

---

## Key Decisions

<!-- Hermes가 대화 후 여기에 중요 결정사항을 추가함 -->

- **Vault 경로**: `/home/han/B2` (GitHub: sangrokhan/B2)
- **지식저장소 구조**: Wikilink 사용, `_context/`만 flat하게 유지
- **AI 컨텍스트 진입점**: 이 파일(`_context/AGENTS.md`)
- **LangGraph Workflow 시각화**: `Dev/LangGraph Workflow 실행 시각화 설계.md` 참고
- **AI Coding CLI I/O 추상화**: `Dev/AI coding CLI 입출력 추상화 설계.md` 참고

---

## Current Focus

<!-- 지금 집중 중인 것. Hermes가 대화 후 업데이트 -->

- Obsidian 지식저장소 구축 및 워크플로우 정립

---

## Vault Structure

```
B2/
├── _context/         ← AI 진입점 (이 파일)
├── Daily Notes/      ← Hermes 대화 요약 자동 저장
├── Knowledge/
│   ├── Dev/          ← 개발 패턴, 기술 결정, 스펙
│   ├── Ideas/        ← 아이디어 정제본
│   └── Business/     ← 창업/비즈니스 지식
├── Projects/
│   ├── ai-imps/
│   ├── fin_calculator/
│   └── remote_work/
├── Dev/              ← 기존 개발 노트 (이전)
├── Templates/        ← 노트 템플릿
└── Dashboard.md      ← 홈 대시보드
```

---

## Rules for AI Tools

1. Wikilink(`note`)를 보면 vault에서 해당 파일을 검색해 읽을 것
2. 새 결정/아이디어는 `Daily Notes/YYYY-MM-DD.md`에 기록됨
3. 정제된 지식은 `Knowledge/` 하위에 위치
4. 이 파일(`AGENTS.md`)은 항상 최신 상태 유지
