---
type: topic-doc-chapter
parent: Knowledge/Dev/TCP 프로토콜 연구.md
chapter: ssthresh분석
part: 1
tags: [ssthresh, tcp, hystart, rto, 분석, f42b60c9, enter, spurious]
---
# TCP 프로토콜 연구 — ssthresh분석

## Log

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

