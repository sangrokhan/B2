---
type: topic-doc-chapter
parent: Knowledge/Dev/TCP 프로토콜 연구.md
chapter: idle-cwnd-reset
part: 1
---

# TCP 프로토콜 연구 — idle-cwnd-reset

## Log

### 11:12 TCP 단말측 최적화 이슈 및 AI 서비스 영향 조사
<!-- topic-doc:start:slack:C0ACDPUAKN3:20260824_111230_ff9e49f6 -->
<!-- chapter: idle-cwnd-reset -->
<!-- date: 2026-08-24 -->
- Source: session 20260824_111230_ff9e49f6

#### Summary
- TCP 프로토콜에서 서버측 최적화와 단말측 최적화의 구조적 비대칭성 조사: 서버는 통제된 환경(BBR, MPTCP 등)에서 최적화 가능하나 단말은 OS가 의도적으로 보수적 파라미터 유지
- netem 기반 실험 환경에서 20ms/40ms RTT 측정 불일치 문제를 pcap 캡처 시점 및 egress qdisc 특성으로 규명
- idle 이후 cwnd 재시작 시 probe RTT를 이용해 baseline 대비 변화를 관측하여 cwnd 유지/리셋을 결정하는 delay-based 아이디어를 TCP Vegas/FAST TCP/Copa/BBR RTprop 등 선례와 비교 분석
- 손실 시 cwnd를 "절반"으로 줄이는 이유(Chiu-Jain 공정성 수렴 증명)와 idle 후 재시작 로직(Linux tcp_cwnd_restart의 RTO 경과 기반 지수감쇠)을 커널 코드 레벨로 분석
- baseline RTT 초과 비율(%) 기반 감쇠 알고리즘 제안: decay_factor = clamp(1 - excess_ratio, floor=IW/cwnd, 1)
- Linux 커널 소스(tcp_input.c, tcp.h) 직접 확인: 실제 RTO 계산은 (srtt_us>>3) + rttvar_us, RTTVAR 초기값 200ms 최소 하한 보장
- 커널의 RTTVAR은 EWMA 근사치로 원본 RTT 샘플을 보존하지 않음을 확인 — 프로젝트 자체 probe.py가 원본 RTT 샘플 보존 중이므로 직접 표준편차 계산이 더 정확함을 실측 검증

#### Decisions
- idle 후 cwnd 재시작 로직에 "baseline RTT 대비 초과 비율 기반 연속적 감쇠" 알고리즘 채택 방향 확정
- RTT variation 판단 시 커널 rttvar_us 재사용 대신 프로젝트 자체 probe 샘플의 원본 RTT로 직접 표준편차 계산하기로 결정
- 이 로직은 "idle 복구 시점 1회성 초기값 설정"으로 범위 한정

#### TODO
- [ ] idle 도중 netem delay 값을 동적으로 변경하는 기능 실험 lab에 추가
- [ ] counterfactual cwnd 계산기 분석 도구 추가
- [ ] probe.py 원본 RTT 샘플로 mean/stdev/percentile 계산하는 분석 모듈 추가
- [ ] baseline RTT 온라인 추정 로직(BBR RTprop 유사) 검증 필요
<!-- topic-doc:end:slack:C0ACDPUAKN3:20260824_111230_ff9e49f6 -->

