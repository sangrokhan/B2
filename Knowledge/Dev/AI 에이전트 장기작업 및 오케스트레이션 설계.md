---
type: topic-doc
title: AI 에이전트 장기작업 및 오케스트레이션 설계
tags: [AI-에이전트, 루프-엔지니어링, Ralph-Loop, 서브에이전트, 오케스트레이션, Claude-Code, 강제, claude, hermes, 확인, 분리, c3975a6b, code, permissions]
created: 2026-09-02
updated: 2026-09-02
split: false
---

# AI 에이전트 장기작업 및 오케스트레이션 설계

## Log

### 16:07 장기작업(루프 엔지니어링) 원리와 서브에이전트 강제 메커니즘 리서치
<!-- topic-doc:start:slack:C0ACDPUAKN3:20260902_160736_c3975a6b -->
<!-- chapter: 리서치 -->
<!-- date: 2026-09-02 -->
- Source: session 20260902_160736_c3975a6b

#### Summary
- 유튜브에서 본 '장기작업/루프 엔지니어링'의 실체를 조사 — 'Ralph Loop' 패턴(매 iteration 컨텍스트 초기화 + 검증 기준으로 순회)이 핵심이며 대부분 시간이 실패-재시도 검증 루프에 소모됨을 확인
- 밤사이 무인 실행을 위해 PRD를 얼마나 촘촘히 짜야 하는지 논의 — 사람의 개별 승인 대신 '기계로 검증 가능한 완료 기준'을 task 단위로 미리 심는 방식으로 대체됨을 설명
- 메인 에이전트가 서브에이전트에게 구현을 위임하도록 '강제'하는 방법 논의 — 텍스트 지침만으로는 강제 불가, Claude Code의 permissions.deny + PreToolUse hook 같은 시스템 레벨 제약이 진짜 강제임을 확인. Hermes에는 이런 하드락 옵션이 아직 노출 안 됨
- 가이드(텍스트) vs 제약조건(하드 블록) 하이브리드 전략 정리 — 구조적 보장 필요 항목은 제약조건으로, 판단/뉘앙스 필요 항목은 가이드로 유지
- 지침이 코드/진행상황과 섞이지 않게 하는 방법(물리적 파일 분리, 레이어 분리, iteration마다 재주입) 정리
- 실무자 대부분은 '단일 에이전트 + 매회 컨텍스트 리셋(Ralph Loop류)'을 사용하며, 메인+서브 강제 오케스트레이션은 소수 파워유저 관행임을 확인

#### Decisions
- 현재 Hermes의 dev-task-guidelines 스킬은 100% 텍스트 가이드이며 강제 메커니즘이 아님을 인정
- 향후 방향은 두 옵션 중 선택 대기: (1) Claude Code 프로젝트(AIPT 등)에 실제 permissions.deny + agents 분리 + hook 설정 적용 (2) Hermes 시스템 레벨 하드 제약 옵션 존재 여부 조사 — 이번 세션에서는 실행/적용까지 진행 안 함

#### TODO
- [ ] Claude Code 프로젝트(AIPT)에 .claude/settings.json permissions.deny + implementer/verifier 서브에이전트 분리 + PreToolUse hook 실제 세팅 여부 결정
- [ ] Hermes 시스템(config.yaml 등)에 orchestrator의 write_file/patch 사용을 막는 하드락 옵션 존재 여부 확인
- [ ] dev-task-guidelines 스킬 5개 항목을 '제약조건화 가능/불가능'으로 분류하고 가능한 항목은 실제 설정 파일로 전환 (사용자 승인 대기)
<!-- topic-doc:end:slack:C0ACDPUAKN3:20260902_160736_c3975a6b -->
