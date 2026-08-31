---
type: topic-doc
title: AIPT 프로젝트
tags: [AIPT, TCP, Vegas, architecture, dev, docker, incident, local-llm, refactor, review, sse, testing, todo, ui, aipt, tcp, congestion, topic-doc, slack, c0acdpuakn3, 커밋]
created: 2026-08-31
updated: 2026-08-31
split: false
---

# AIPT 프로젝트

## Log

### 14:13 AIPT 프로젝트 통합 및 설계 (tcp_congestion + token_traffic 병합)
<!-- topic-doc:start:slack:C0ACDPUAKN3:20260826_141333_1641fd55 -->
<!-- chapter: 설계 -->
<!-- date: 2026-08-26 -->
- Source: session 20260826_141333_1641fd55

#### Summary
- tcp_congestion(FastAPI, mock idle-reset cwnd 실측)과 token_traffic(Flask, 실제 Gemini/OpenAI API 측정) 두 프로젝트를 AIPT(AI Protocol Traffic lab)로 완전 병합
- 아키텍처를 3-backend(public_ai/mock/local_llm) + Network Gateway(tc netem) + C 기반 정밀 측정 원칙으로 확립, DESIGN.md/ARCHITECTURE.md/MIGRATION.md 작성
- 14개 서브태스크 개별 dispatch + 완료 즉시 메인 에이전트 재검증 워크플로우로 병렬 진행, 13/14 완료, 410 passed/1 skipped
- 서브에이전트 자체보고를 그대로 믿지 않고 직접 재검증하여 실버그(local_llm tests/__init__.py 누락) 발견·수정
- tcp_congestion이 git 미커밋(untracked) 상태 발견 → 삭제 전 먼저 커밋 후 원본 삭제하기로 결정

#### Decisions
- AIPT 프로젝트 구조 확정: aipt/{backends/{public_ai,mock,local_llm},core,export,gateway,web}/
- 웹 UI는 FastAPI 단일 앱으로 통합, git 히스토리는 끊고 새로 복사
- Network Gateway 컨테이너 도입: mock/local_llm 경로는 반드시 Gateway 경유
- C 기반 정밀 측정을 "TCP/네트워크 타이밍은 별도 C 프로세스가 담당" 원칙으로 격상
- tcp_congestion 먼저 git 커밋(히스토리 보존) 후 삭제 → AIPT 커밋 순서로 진행 (사용자 승인)

#### TODO
- [ ] routes_run.py의 mock_fixtures 미해결 참조 오류 수정 완료 필요
- [ ] 원본 token_traffic/tcp_congestion 폴더 최종 삭제 및 README/docs 정리
- [ ] AIPT 전체 스위트 최종 재검증 및 커밋
<!-- topic-doc:end:slack:C0ACDPUAKN3:20260826_141333_1641fd55 -->

### 16:41 TCP 단말측 최적화 세션 — tcp_congestion→AIPT 병합 발견 및 대응
<!-- topic-doc:start:slack:C0ACDPUAKN3:20260824_111230_ff9e49f6-cont -->
<!-- chapter: 이슈해결 -->
<!-- date: 2026-08-26 -->
- Source: session 20260824_111230_ff9e49f6-cont

#### Summary
- (0824 세션 연속) tcp_congestion docker compose 재기동 시도 중 원본 소스 파일이 전부 삭제된 상태 발견
- 원인: 병렬 진행 중이던 다른 세션(AIPT 통합 작업)이 tcp_congestion+token_traffic을 AIPT로 병합하며 원본을 정리(삭제)함 — 커밋 3d393be2로 확인
- docker compose up 실패는 tcp_congestion/docker-compose.yml 부재로 상위 디렉토리의 엉뚱한 프로젝트 compose 설정을 잘못 집어든 것이 원인
- AIPT는 이미 광범위 마이그레이션되어 기능이 더 발전된 상태(Network Gateway, cwnd 모니터링 등) 확인
- 사용자에게 AIPT 즉시 기동/먼저 검토/tcp_congestion git 복구 3가지 선택지 제시했으나 "멈추도록 해" 응답으로 작업 중단

#### Decisions
- 사용자 지시로 추가 작업 중단, 현재 상태 유지하며 다음 지시 대기

#### TODO
- [ ] AIPT를 바로 기동할지, 먼저 검토할지, tcp_congestion을 git에서 복구해 독립 유지할지 결정 필요
<!-- topic-doc:end:slack:C0ACDPUAKN3:20260824_111230_ff9e49f6-cont -->

### 18:08 AIPT 병합 마무리 — 실컨테이너 검증 및 최종 커밋
<!-- topic-doc:start:slack:C0ACDPUAKN3:20260826_141333_1641fd55-cont2 -->
<!-- chapter: 구현 -->
<!-- date: 2026-08-26 -->
- Source: session 20260826_141333_1641fd55-cont2

#### Summary
- (14:13 세션 연속) mock backend "fixture" 입력 모드를 "record" 모드로 완전 통일(7개 파일), 433 tests passed
- tcp_congestion 먼저 git 커밋(히스토리 보존, pcap 14개는 root 소유 권한 문제로 gitignore 제외) 후 원본 삭제, AIPT 신규 커밋(refactor: merge token_traffic + tcp_congestion into AIPT)까지 완료·푸시
- docker compose up --build로 web/gateway/mock-server 3-service 실컨테이너 기동, 실버그 2건 발견·수정: (1) Dockerfile.mockserver iproute2 누락으로 ip route add 조용히 실패 (2) mock-server 고정 IP 미설정으로 L3 라우팅 비결정적
- 실제 web→gateway→mock-server L3 라우팅(NAT 없이 원본 IP 보존) + 양방향 netem(3g 프로파일) 파이프라인 실동작 확인
- 최종 커밋(02092b97) 푸시 완료, http://localhost:10000 정상 서빙 확인 — AIPT 병합 프로젝트 전체 완료

#### Decisions
- mock backend 입력 모드를 "record" 단일 모드로 통일 확정
- pcap 14개(root 소유, 읽기 권한 없음)는 커밋 제외, 삭제하지 않고 파일시스템 보존
- AIPT 프로젝트(14개 서브태스크, docker 3-service) 최종 완료로 확정

#### TODO
- [ ] (낮은 우선순위) tcp_congestion/data/pcaps root 소유 파일 14개 권한 정리 또는 백업 검토
- [ ] AIPT README/문서에 최종 아키텍처 반영 여부 확인
<!-- topic-doc:end:slack:C0ACDPUAKN3:20260826_141333_1641fd55-cont2 -->

### 11:46 AIPT: API Type 선택 순서 변경
<!-- topic-doc:start:slack:C0ACDPUAKN3:20260827_104814_62443c8f -->
<!-- chapter: 구현 -->
<!-- date: 2026-08-27 -->
- Source: session 20260827_104814_62443c8f

#### Summary
- 백엔드 선택 UI 구조 변경: flat "Arm" 드롭다운 대신 "API Type" → "Context Handle" 2단계 선택 방식 도입
- Local LLM/Mock도 동일한 api_types 구조로 통일해 4개 백엔드 카드 arm-resolution 경로 일관화
- 혼잡제어 알고리즘 선택을 Mock 전용에서 전체 백엔드로 확장 — aipt/core/congestion.py 신규 작성(/proc/sys/net/ipv4/tcp_available_congestion_control 실시간 조회), wire.py에 TCP_CONGESTION 소켓 옵션 연결
- Mock 더미 byte-size sweep 기본값을 스트레스 시나리오로 변경
- 전체 테스트 444 passed, local_llm 대상 실제 소켓 algorithm.actual == requested 검증 완료, 커밋(9da9cdcf) push 완료

#### Decisions
- Arm 선택 폐지, API Type → Context Handle 2단계 UI로 전환 (사용자 명시 지시)
- 혼잡제어 알고리즘 선택 기능을 모든 백엔드에 적용
- MIGRATION.md는 과거 병합 체크리스트로 간주, 이번 변경은 갱신 대상 아님

#### TODO
- [ ] (특별한 후속 TODO 없음 — 작업 완료 및 push까지 마무리)
<!-- topic-doc:end:slack:C0ACDPUAKN3:20260827_104814_62443c8f -->

### 12:00 온디바이스 소형 모델 메모리 요구사항 확인 (API 테스트용)
<!-- topic-doc:start:slack:C0ACDPUAKN3:20260827_114816_e5845421 -->
<!-- chapter: 테스트환경 -->
<!-- date: 2026-08-27 -->
- Source: session 20260827_114816_e5845421

#### Summary
- API 테스트 목적으로 온디바이스 소형 LLM 메모리 요구사항 확인 요청
- Qwen2.5-0.5B-Instruct(Q4_K_M, GGUF ~400MB)를 llama.cpp llama-server로 로컬 구동(포트 8090)
- OpenAI 호환 /v1/chat/completions 엔드포인트 정상 응답 확인
- 실측: RSS ≈ 512MB(모델 400MB + context 4096 오버헤드), CPU 8코어 기준 prompt ~94 tok/s, generation ~42 tok/s
- 필요 시 Llama-3.2-1B(~800MB), Qwen2.5-1.5B(~1GB)로 교체 가능

#### Decisions
- API 테스트용으로 Qwen2.5-0.5B-Instruct를 8090 포트에 우선 구동

#### TODO
- [ ] 테스트 종료 후 서버 계속 켜둘지 중지할지 결정 필요 (process kill: proc_4733e25cf299)
<!-- topic-doc:end:slack:C0ACDPUAKN3:20260827_114816_e5845421 -->

### 13:05 AIPT 남은 작업 리스트업 (TODO.md SSoT 도입)
<!-- topic-doc:start:slack:C0ACDPUAKN3:20260827_130529_d3175ce0 -->
<!-- chapter: 구현 -->
<!-- date: 2026-08-27 -->
- Source: session 20260827_130529_d3175ce0

#### Summary
- 이관/병합 이후 남은 작업 리스트업, TODO.md를 신규 SSoT로 생성
- MIGRATION.md/DESIGN.md/README.md 전수 검토해 미해결 항목 6개 추출
- TODO #3 run 이력 영속화 구현: 메모리(OrderedDict) + 디스크(RUN_STORE_DIR) 이중 저장, 재시작 시 자동 rehydrate
- 신규 유닛테스트 7개 추가, 전체 446 passed, 커밋/푸시(8a06adae, 4268a032)
- 동시에 다른 세션이 mock backend/SSE 작업 진행 중임을 발견해 TODO.md에 충돌 방지 메모 남김

#### Decisions
- TODO.md를 AIPT 프로젝트 남은 작업 단일 소스(SSoT)로 신규 도입
- run 이력 저장 정책: 메모리(MAX_RUNS=50) + 디스크(data/runs/) 이중화

#### TODO
- [ ] TODO #4 /api/run/stream SSE 엔드포인트 구현 (착수 전 다른 세션 작업 여부 재확인)
- [ ] TODO #5 routes_run.py pcap 응답 필드 미배선
- [ ] TODO #6 원본 tcp_congestion/ 디렉터리 삭제 또는 archive 방침 확정
<!-- topic-doc:end:slack:C0ACDPUAKN3:20260827_130529_d3175ce0 -->

### 13:14 AIPT perf.json 20턴 확장 및 fixture→record 리네임
<!-- topic-doc:start:slack:C0ACDPUAKN3:20260827_131454_5ca56f45 -->
<!-- chapter: 구현 -->
<!-- date: 2026-08-27 -->
- Source: session 20260827_131454_5ca56f45

#### Summary
- perf.json(AIPT Gemini fixture)을 10턴에서 20턴으로 확장
- fixtures/ 디렉터리를 records/로 리네임, Fixture→ScenarioRecord, FixtureWriter→RecordWriter 전체 네이밍 통일
- aipt/backends/mock/replay.py 재작성: 실측 캡처를 로드해 답변 텍스트는 동일 길이 placeholder로 치환
- records.load_scenario_record()가 steps-shaped/turns-shaped 양쪽 스키마 모두 로드 가능하도록 확장
- 관련 테스트 전량 갱신, MIGRATION.md에 작업 이력 기록, 커밋 d1feaf8f 푸시 완료

#### Decisions
- "fixture" 용어를 프로젝트 전체에서 "record"로 통일
- replay는 답변 바이트 크기만 재현, 지연시간은 별도 파라미터로 제어하는 정책 유지

#### TODO
- [ ] (해당 세션에서 별도 TODO 없음 — MIGRATION.md에 완료 기록됨)
<!-- topic-doc:end:slack:C0ACDPUAKN3:20260827_131454_5ca56f45 -->

### 13:40 AIPT TODO #4 확인 및 SSE 엔드포인트 구현
<!-- topic-doc:start:slack:C0ACDPUAKN3:20260827_134056_b97c7750 -->
<!-- chapter: 구현 -->
<!-- date: 2026-08-27 -->
- Source: session 20260827_134056_b97c7750

#### Summary
- TODO #4 /api/run/stream SSE 엔드포인트 실제 구현: _run_conversation_stream() 제너레이터로 리팩터링, threadpool↔이벤트루프 브리지, 턴마다 SSE 이벤트 전송
- 사용자 지시로 프론트엔드 소비자는 불필요 — 모든 스트림 이벤트를 서버측에서 <exec_id>.stream.jsonl로 영속 로깅
- 신규 테스트 5개 추가, 전체 448 passed, 커밋(98e4314f)

#### Decisions
- SSE 스트림은 프론트엔드 소비자 없이 서버 로깅(jsonl) 목적으로만 사용

#### TODO
- [ ] (해당 세션에서 완료 처리 — 별도 후속 TODO 없음)
<!-- topic-doc:end:slack:C0ACDPUAKN3:20260827_134056_b97c7750 -->

### 14:15 AIPT 구현-문서 TODO 검토 + TCP Vegas RTT 혼잡제어 분석
<!-- topic-doc:start:slack:C0ACDPUAKN3:20260827_141514_b62a3d96 -->
<!-- chapter: 검토 -->
<!-- date: 2026-08-27 -->
- Source: session 20260827_141514_b62a3d96

#### Summary
- AIPT 구현 내용과 문서(TODO.md) 간 차이 전수 재검토, 완료 항목 표기 갱신
- TODO #4(SSE 스트림) 이미 구현 확인, [x] 완료로 갱신(커밋 98e4314f 근거)
- pytest 448 passed 재검증, 문서와 실측 일치 확인
- 사이드 대화: TCP Vegas 혼잡제어 RTT 기반 로직을 커널 소스(tcp_vegas.c) 분석 — baseRTT/minRTT 필터링, cong_avoid RTT당 1회 조정, idle 재시작 시 상태 초기화 메커니즘
- Vegas가 idle 재시작 시 baseRTT까지 완전 리셋하고 새 ACK를 기다리는 보수적 설계임을 확인, AIPT 실험에 참고할 변형 아이디어(baseRTT 보존) 제안

#### Decisions
- TODO.md 항목은 완료 확인 시 코드/문서 재검증 근거를 남기고 [x]로 갱신하는 방식 유지

#### TODO
- [ ] TODO #5 routes_run.py pcap 응답 필드 미배선 (여전히 미해결)
- [ ] TODO #6 원본 tcp_congestion/ 디렉터리 삭제 또는 archive 방침 확정 필요 (디스크 64M 잔존)
- [ ] (선택) Vegas 기반 idle-RTT 보존 실험 모듈 제작 여부 — 사용자 확인 대기 중이었음
<!-- topic-doc:end:slack:C0ACDPUAKN3:20260827_141514_b62a3d96 -->
