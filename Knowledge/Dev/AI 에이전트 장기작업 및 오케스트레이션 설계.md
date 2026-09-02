---
type: topic-doc
title: AI 에이전트 장기작업 및 오케스트레이션 설계
tags: [AI-에이전트, Claude-Code, Ralph-Loop, a2a, agent-protocol, c3975a6b, claude, code, hermes, multi-agent, orchestration, permissions, 강제, 루프-엔지니어링, 분리, 서브에이전트, 오케스트레이션, 확인, 호출, 에이전트, 가능한]
created: 2026-09-02
updated: 2026-09-03
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

### 19:31 A2A 호출 가능한 코딩 Agent 존재 여부
<!-- topic-doc:start:slack:C0ACDPUAKN3:20260902_193105_cfe13c44 -->
<!-- chapter: 멀티 에이전트 상호운용 프로토콜 -->
<!-- date: 2026-09-03 -->
- Source: session 20260902_193105_cfe13c44

#### Summary
- A2A(Agent2Agent) 프로토콜로 호출 가능한 코딩 에이전트 존재 여부 질문
- claude-a2a, codex-a2a, opencode-a2a, swival, a2a-bridge 등 커뮤니티 wrapper 구현체 다수 확인 (1st-party 공식 지원은 없음)
- 로컬/동일 머신에서는 headless CLI 호출(claude -p, codex exec)이 A2A보다 가볍고 직접적임을 설명
- A2A는 shell 접근 권한 없는 외부 프로세스/조직 경계·다중 벤더 표준화가 필요한 경우에만 의미 있음
- 현재 Hermes 환경 기준 delegate_task/headless CLI가 A2A보다 우선순위 높다는 잠정 결론, 구체적 유스케이스는 미확정

#### Decisions
- 로컬 shell 접근 가능한 현재 환경에서는 A2A 래퍼 도입보다 delegate_task/headless CLI 호출 방식을 잠정 우선 (최종 결정 아님)

#### TODO
- [ ] A2A 연동 검토 중인 구체적 유스케이스(외부에서 Hermes 호출 vs Hermes가 외부 A2A 에이전트 호출) 확인 필요
<!-- topic-doc:end:slack:C0ACDPUAKN3:20260902_193105_cfe13c44 -->
