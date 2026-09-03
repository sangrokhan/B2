---
type: topic-doc
title: 퀀트 자율 연구 에이전트 (quant-agent)
tags: [quant-agent, quant, vectorbt, gatekeeper, backtesting, research-loop, 기각, 가설, 실패, sharpe, 퀀트, 실행, 사용량]
created: 2026-09-03
updated: 2026-09-03
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
