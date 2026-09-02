---
type: topic-doc-chapter
parent: Knowledge/Dev/TCP 프로토콜 연구.md
chapter: RTO계산
part: 1
tags: [rto, tcp, srtt, rttvar, d7a31b11, rtt, rfc, 계산]
---
# TCP 프로토콜 연구 — RTO계산

## Log

### 14:56 TCP RTO SRTT/RTTVAR 코드 분석
<!-- topic-doc:start:slack:C0ACDPUAKN3:20260825_145615_d7a31b11 -->
<!-- chapter: RTO계산 -->
<!-- date: 2026-08-25 -->
- Source: session 20260825_145615_d7a31b11

#### Summary
- Linux 커널 RTO 계산 코드(tcp_rtt_estimator, __tcp_set_rto) 직접 분석해 RFC 6298와의 차이 규명
- RTO 최종식은 (srtt_us>>3) + rttvar_us — RFC의 K=4 곱셈이 명시적으로 보이지 않음, mdev를 4배 스케일로 저장해 흡수한 설계
- SRTT는 실제값×8 fixed-point 방식, RTTVAR는 RFC처럼 매 샘플 지수평활이 아니라 "1 RTT 구간 내 최대 편차" 사용
- RTT 감소 시(m<0) mdev 갱신 gain을 추가 축소하는 비대칭 처리(Eifel 변형)로 RTO가 너무 빨리 줄어드는 것 방지

#### Decisions
- 없음 (코드 분석/설명 위주 세션)
<!-- topic-doc:end:slack:C0ACDPUAKN3:20260825_145615_d7a31b11 -->

