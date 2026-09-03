---
type: topic-doc
title: Hermes 에이전트 인프라 유지보수
tags: [hermes, ddgs, websearch, infra, bugfix, brave, bing, google, duckduckgo, abee96, auto, yahoo]
created: 2026-09-04
updated: 2026-09-04
split: false
---

# Hermes 에이전트 인프라 유지보수

## Log

### 19:05 DuckDuckGo(ddgs) 검색 백엔드 실패 원인파악 및 수정
<!-- topic-doc:start:slack:C0ACDPUAKN3:20260903_190516_54abee96 -->
<!-- chapter: 이슈해결 -->
<!-- date: 2026-09-04 -->
- Source: session 20260903_190516_54abee96

#### Summary
- DuckDuckGo(ddgs) 웹서치 백엔드가 계속 실패한다는 보고를 받아 원인 조사
- ddgs 패키지의 backend="auto"가 duckduckgo/yahoo/brave/bing/google을 순환하는데, 이 호스트 IP가 DDG/Brave의 안티봇 차단에 걸려(DDG/Brave는 빈 결과, Yahoo는 TLS 리셋) auto가 계속 죽은 백엔드를 골라 실패
- hermes-agent plugins/web/ddgs/provider.py의 _run_ddgs_search()에서 client.text() 호출을 backend="bing,google"로 명시 고정하도록 수정
- _search_worker.py(자식 프로세스 방식) 및 DDGSWebSearchProvider 클래스 경로 양쪽으로 실제 검색 실행해 정상 동작 검증(TCP idle reset, LLM agent 관련 쿼리로 실측 성공)
- 검색마다 새 자식 프로세스를 스폰하는 구조라 hermes-gateway 데몬 재시작 없이 즉시 반영됨을 확인

#### Decisions
- ddgs 백엔드를 "auto" 대신 "bing,google"로 고정 (DDG/Brave/Yahoo가 이 호스트에서 이미 차단·불안정 상태로 확인됨)
- 재시작 없이 다음 검색부터 즉시 반영되는 구조 확인 (별도 배포 조치 불필요)

#### TODO
- [ ] bing/google 스크레이핑도 ddgs의 비공식 HTML 스크레이핑 방식이라 향후 이 IP가 차단될 가능성 있음 — 재발 시 공식 API 기반 백엔드(Brave Search API 무료티어, Tavily 등)로 전환 검토
<!-- topic-doc:end:slack:C0ACDPUAKN3:20260903_190516_54abee96 -->
