---
type: topic-doc
title: TCP 프로토콜 연구
tags: [BBR, HyStart, QUIC, RTO, TCP, Vegas, congestion-control, research, ssthresh, tcp, rtt, cwnd, vegas, rto, topic-doc, slack, c0acdpuakn3]
created: 2026-08-31
updated: 2026-08-31
split: false
---

# TCP 프로토콜 연구

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

### 15:33 BBR v1, v2, v3 차이점 및 혼잡제어 알고리즘 비교
<!-- topic-doc:start:slack:C0ACDPUAKN3:20260825_153342_92f0ff41 -->
<!-- chapter: 혼잡제어알고리즘비교 -->
<!-- date: 2026-08-25 -->
- Source: session 20260825_153342_92f0ff41

#### Summary
- BBR v1/v2/v3 진화 정리: v1(순수 BW×RTT, loss 미사용, fairness 문제) → v2(loss/ECN 보조신호 도입) → v3(수렴버그 수정, 재전송률 12% 감소, Google 프로덕션 적용, IETF 표준화 진행)
- 현재 머신 커널 상태 점검: reno/cubic만 로드, BBR/Vegas는 모듈로 존재하나 미로드, default_qdisc는 fq_codel(BBR 권장은 fq)
- server.py /inference-mock 핸들러 고정크기 응답 버그 발견 및 수정 (response_bytes 파라미터 추가), 테스트 138개 통과
- Cubic vs Vegas 실측: idle_duration=0 조건에서 매 턴 cwnd가 IW=10으로 리셋되어 congestion avoidance 진입 기회 없어 알고리즘 차이가 거의 드러나지 않음 확인

#### Decisions
- mock 응답 크기 버그 수정 즉시 적용 (재빌드/재기동 완료)
- Cubic vs Vegas 차이는 idle 리셋 없는 연속 전송 조건으로 재실행해 congestion avoidance 단계에서 비교해야 함

#### TODO
- [ ] sudo modprobe tcp_bbr/tcp_vegas 실행 및 qdisc fq 변경 (Sangrok 직접 실행 필요)
- [ ] idle 없는 연속 요청 조건으로 Cubic vs Vegas 재실행
- [ ] BBR 실제 버전(v1/v2/v3) net/ipv4/tcp_bbr.c 소스 심볼 대조 확인
<!-- topic-doc:end:slack:C0ACDPUAKN3:20260825_153342_92f0ff41 -->

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

### 17:59 TCP ssthresh 값 설정 원인 분석 (HyStart 확정)
<!-- topic-doc:start:slack:C0ACDPUAKN3:20260825_175909_f42b60c9 -->
<!-- chapter: ssthresh분석 -->
<!-- date: 2026-08-25 -->
- Source: session 20260825_175909_f42b60c9

#### Summary
- ssthresh가 무한대에서 특정값으로 바뀌는 3가지 커널 진입점: tcp_enter_loss(RTO), tcp_enter_recovery(Fast Retransmit), tcp_enter_cwr(ECN CE)
- "손실 없는데 ssthresh 하락" 3가지 원인: ① ECN CE 마킹 ② Spurious RTO ③ RACK reordering 오판
- 실측 데이터 분석 결과 확정 원인은 CUBIC 전용 HyStart(Hybrid Slow Start)의 ACK-train detection — hystart_update()가 WRITE_ONCE(snd_ssthresh, snd_cwnd)로 직접 세팅
- HyStart ACK-train 판정 로직(tcp_cubic.c) 정리: ACK 간격 2ms 이내면 "train" 유지, 라운드 경과시간이 threshold 초과 시 트리거
- (정정) 초반 spurious RTO 가설이 유력했으나 ca_state=open 지속, loss/sacked/retrans 불변으로 HyStart로 정정됨

#### Decisions
- HyStart ACK-train detection이 확정 원인으로 정리됨 (spurious RTO 가설은 데이터로 반증)

#### TODO
- [ ] nstat -az로 TCPHystartTrainDetect/TCPHystartTrainCwnd 카운터 실측 확인
- [ ] cwnd.csv에서 ssthresh 세팅 순간 snd_cwnd 값과 세팅된 ssthresh 값 일치 대조
<!-- topic-doc:end:slack:C0ACDPUAKN3:20260825_175909_f42b60c9 -->

### 13:39 QUIC with Vegas/Cubic congestion control test
<!-- topic-doc:start:slack:C0ACDPUAKN3:20260826_133938_d8d786a3 -->
<!-- chapter: 혼잡제어알고리즘비교 -->
<!-- date: 2026-08-26 -->
- Source: session 20260826_133938_d8d786a3

#### Summary
- QUIC에 커널 수정 없이 TCP Vegas/Cubic 대신 응용 수준 혼잡제어 적용 가능 여부 확인 — QUIC은 유저스페이스 라이브러리에 혼잡제어를 구현하도록 설계되어 커널 모듈 수정 불필요
- aioquic(Python) 소스 조사: QuicCongestionControl 추상클래스 + register_congestion_control() 레지스트리 패턴, cubic/reno 내장, Vegas는 4개 콜백만 구현하면 추가 가능
- quiche(Rust)/quic-go(Go)와 비교해 aioquic이 언어/구조 면에서 가장 적합하다고 제안
- 실험 설계 제안: aioquic 기반 서버/클라이언트 + Vegas CC 클래스 직접 구현 + qlog 기반 cwnd/RTT 로깅

#### Decisions
- 결정 없음 (조사 및 제안까지 진행, 사용자 응답 없이 세션 종료)

#### TODO
- [ ] aioquic 기반 QUIC+Vegas 실험 prototype 제작 여부 결정 필요
- [ ] aioquic 소스에서 Vegas 관련 기존 구현/PR 조사 여부 결정 필요
<!-- topic-doc:end:slack:C0ACDPUAKN3:20260826_133938_d8d786a3 -->
