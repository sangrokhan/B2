---
type: topic-doc
title: 퀀트 자율 연구 에이전트 (quant-agent)
tags: [backtesting, dashboard, gatekeeper, iteration, jsonl, knowledge-base, quant, quant-agent, research-loop, sharpe, ui, vectorbt, 가설, 검색, 검색구조, 구조, 기각, 사용량, 실패, 실행, 인덱스, 컨텍스트, 퀀트, 태그, 토큰최적화, slack, 대시보드, topic-doc, c0acdpuakn3]
created: 2026-09-03
updated: 2026-09-04
split: false
---

# 퀀트 자율 연구 에이전트 (quant-agent)

## Log

### 16:16 퀀트 자율 연구 에이전트 구현 인터뷰 및 첫 실행
<!-- topic-doc:start:slack:C0ACDPUAKN3:20260903_161608_0182dd37 -->
<!-- chapter: 설계및초기실행 -->
<!-- date: 2026-09-03 -->
- Source: session 20260903_161608_0182dd37

#### Summary
- Ouroboros interview 방식으로 "퀀트 자율 연구 에이전트" 요구사항을 정리: 완전 신규 프로젝트, `~/repo/quant-agent`(독립 새 git 레포)로 확정
- 구조: `RESEARCH_LOOP.md`(Hermes cronjob의 LLM turn이 매 iteration 따르는 절차서), `gatekeeper/check_gate.py`(실행 승인 게이트), `knowledge_base/strategies_log.jsonl`(append-only 가설/결과 로그), `strategies/`(전략코드), `validation/validators.py`(vectorbt 기반 검증 함수), `backtests/`(백테스트 리포트), `paper_trading/simulator.py`, `data/loaders.py`(yfinance/ccxt cache-first 래퍼), `SAFETY.md`(실주문 코드 절대 금지 원칙)
- Gatekeeper 정책: 평일 10-18시 KST는 5시간 롤링 사용량 75% 이하일 때만 승인(실패 시 fail-closed), 그 외 시간은 100% 도달 전까지 승인(사용량 조회 실패 시 fail-open, light workload)
- Gatekeeper를 mock `usage_state.json` 전용에서 Hermes 내장 `agent.account_usage.fetch_account_usage("anthropic")` 호출로 교체 — Anthropic 공식(비공개) OAuth usage 엔드포인트(`five_hour.utilization`)에서 실제 사용량을 가져옴. mock 파일은 실패 시 폴백으로만 유지. 실측 검증(29.0%→30.0%→32.0% 순차 확인, approved: true, workload: normal) 후 커밋 `5868ace` 푸시
- 수동 1회 RESEARCH_LOOP 전체 절차 실행: knowledge_base(과거 시도 2건 — SPY SMA crossover는 walk-forward 실패로 기각, BTC funding-rate는 데이터 부재로 기각) 확인 → novelty 체크 → QQQ Bollinger-Band 평균회귀 + 20일 실현변동성 레짐 필터 가설 수립 → 전략 코드 작성(`strategies/2026-09-03_bb_meanrev_qqq_volregime.py`)
- 실행 중 발견/수정한 실제 결함: vectorbt가 venv에 미설치(uv add로 설치), 최신 plotly(7.0.0)가 vectorbt 1.1.0의 테마 초기화 코드와 충돌해 import 자체가 실패 → `plotly<5.24` pin 추가, `validators.py`의 `check_sharpe_ratio`/`check_max_drawdown`이 DatetimeIndex freq 미지정으로 vectorbt 호출 실패 → `freq="D"` 명시로 수정, 전략 코드의 `entry_idx=None` 초기값이 특정 분기에서 타입 에러를 낼 수 있는 버그 → `entry_idx=0`으로 수정
- 백테스트 결과: QQQ 2019-2026 전체기간에서 14회 진입, 시장 참여일 81/1927일(4.2%), 누적수익률 -8.8%, Sharpe -0.30(기준 1.0 대비 명확히 미달) → **기각(reject)**. 최대낙폭은 15%로 기준(25%) 이내였으나 첫 관문인 Sharpe에서 탈락해 walk-forward/파라미터 민감도 검증은 스킵, `backtests/2026-09-03_bb_meanrev_qqq_volregime.md`에 정직하게 기록
- 기각 사유 분석 메모: QQQ의 강한 상승추세 때문에 "시장에 없는 날이 많은" 전략은 구조적으로 불리할 수 있어, 향후 루프에서는 포트폴리오 전체 Sharpe 대신 "거래한 날만" 벤치마크와 비교하는 지표 보완이 필요하다는 개선 아이디어 메모

#### Decisions
- 퀀트 에이전트는 완전 신규 독립 레포(`~/repo/quant-agent`)로 진행, B2 wiki와는 지식 문서만 이쪽에 기록하고 코드는 별도 저장소 유지
- Gatekeeper 사용량 판정은 mock이 아닌 실제 Anthropic API 기반으로 전환
- 평일 business hours 75% 사용량 캡 정책 확정, 그 외 시간은 100%까지 허용
- 수동 1회 트리거 + cronjob 등록을 동시에 진행해 자동 트리거 관찰
- 첫 가설(BB 평균회귀+변동성 레짐)은 Sharpe 미달로 기각 확정, 억지로 나머지 검증 강행하지 않고 정직하게 reject 기록

#### TODO
- [ ] quant-agent cronjob(1시간 간격)이 정상 자동 트리거되는지 확인
- [ ] BB 평균회귀 가설 기각 이후 새 가설(더 넓은 밴드, 짧은 타임프레임, 혹은 완전히 다른 접근) 탐색
- [ ] validators.py에 "거래일만 벤치마크 비교" 방식의 보조 지표 추가 검토
- [ ] SAFETY.md/RESEARCH_LOOP.md가 실제 무인 루프 반복 상황에서도 안전장치로 충분한지 몇 회 반복 후 재점검
<!-- topic-doc:end:slack:C0ACDPUAKN3:20260903_161608_0182dd37 -->

### 09:30 컨텍스트 과다 사용 원인 분석 및 검색구조 재설계
<!-- topic-doc:start:slack:C0ACDPUAKN3:20260904_093046_8f4175b9 -->
<!-- chapter: 컨텍스트최적화 -->
<!-- date: 2026-09-04 -->
- Source: session 20260904_093046_8f4175b9

#### Summary
- quant-agent가 컨텍스트를 과다 사용하는 원인을 진단: `RESEARCH_LOOP.md` Step 1이 매 iteration마다 knowledge base(`strategies_log.jsonl` 296KB, `visited_pages.jsonl` 141KB, 합산 약 11만 토큰)를 통째로 읽도록 강제하는 구조가 원인
- append-only 로그 + 자연어 장문 `notes` 필드(엔트리당 최대 2KB) 때문에 파일이 선형적으로 계속 커지며, cron trigger당 최대 10 iteration이 반복될 때마다 누적 소모가 증가
- 실측: `usage_tracking.md` 기준 iteration 3~5회 진행 동안 사용량 46%→65%로 상승(iteration당 +3~8%p)
- Sangrok 지적: 압축/요약 접근은 손실이 생겨(grid breakdown, 근거 문서 등 뭉개짐) novelty check 정확도가 떨어질 위험 → "압축 없이, 키워드로 검색 가능한 구조로 바꿔서 필요한 것만 상세 로드"하는 방향으로 재설계하기로 함
- Ouroboros clarify 인터뷰로 세부 설계 확정: (1) id+hypothesis+tags만 담은 경량 index.jsonl을 별도 유지해 먼저 검색 후 원본 라인만 lookup, (2) Step 9 로깅 시 indicator_family/technique 등 구조화된 태그 필드 명시적 추가, (3) visited_pages.jsonl도 동일하게 2단계 검색 구조 적용(URL만 별도 경량 리스트로 분리), (4) 기존 90개 엔트리도 태그 필드를 소급 backfill

#### Decisions
- knowledge base 검색 구조를 "전체 읽기"에서 "경량 index.jsonl 검색 → 원본 라인 lookup" 방식으로 전환하기로 결정
- 엔트리에 구조화된 태그(indicator_family, technique, asset_class 등) 필드를 명시적으로 추가하기로 결정 — 자연어 grep 대신 정확도 높은 태그 매칭 사용
- visited_pages.jsonl에도 동일한 2단계 검색 구조 적용 결정 (URL만 별도 경량 리스트로 분리)
- 기존 90개 엔트리도 태그 필드를 소급 backfill하기로 결정 (1회성 작업, 정확도 우선)

#### TODO
- [ ] RESEARCH_LOOP.md Step 1/9 절차 수정: index.jsonl 기반 2단계 검색·lookup 구조 구현
- [ ] strategies_log.jsonl 스키마에 indicator_family/technique/asset_class 등 구조화 태그 필드 추가 및 Step 9 로깅 절차 갱신
- [ ] visited_pages.jsonl도 URL 전용 경량 인덱스로 분리하는 2단계 구조 적용
- [ ] 기존 90개 strategies_log 엔트리에 태그 필드 소급 backfill 작업 수행
- [ ] 새 구조 적용 후 실제 iteration당 컨텍스트 사용량 감소 효과 재측정
<!-- topic-doc:end:slack:C0ACDPUAKN3:20260904_093046_8f4175b9 -->

### 17:08 작업 대시보드 구축 요구사항 인터뷰
<!-- topic-doc:start:slack:C0ACDPUAKN3:20260904_170842_69e8ac57 -->
<!-- chapter: 대시보드 -->
<!-- date: 2026-09-04 -->
- Source: session 20260904_170842_69e8ac57

#### Summary
- Sangrok이 퀀트 에이전트(quant-agent)의 작업 내역을 볼 수 있는 대시보드 구축을 요청
- 현재 quant-agent 저장소 구조 확인: knowledge_base/(strategies_log.jsonl, strategies_index.jsonl, visited_pages/visited_urls.jsonl), backtests/, strategies/, validation/ 등에 이미 다수의 전략 실험 데이터 축적됨(9/3~9/4 기준 20개 이상의 전략 백테스트 리포트)
- dev-task-guidelines 스킬에 따라 기본 개발 경로(PRD 인터뷰 → progress.md 승인 → Claude Code subagent loop)를 적용하기 위해 Ouroboros 방식 clarify 인터뷰 시작
- clarify 질문 3가지 제시: (1) 대시보드 핵심 콘텐츠 - 전략 탐색/검증 이력 vs 게이트키퍼 실행 이력 vs 통합, (2) 접근 방식 - 로컬 웹 대시보드 vs 정적 리포트 vs Slack 요약, (3) 기술 스택 선호도
- 대화가 clarify 질문 제시 단계에서 종료됨 — 사용자 답변 대기 중 (미완료, 다음 세션에서 이어질 가능성)

#### Decisions
- 없음 (요구사항 확정 전, clarify 인터뷰 단계에서 대화 중단)

#### TODO
- [ ] Sangrok의 clarify 답변(대시보드 콘텐츠/접근방식/기술스택 선택) 확인 후 PRD 인터뷰 이어서 진행
- [ ] progress.md 초안 작성 및 승인 게이트 통과 후 대시보드 구현 착수
<!-- topic-doc:end:slack:C0ACDPUAKN3:20260904_170842_69e8ac57 -->
