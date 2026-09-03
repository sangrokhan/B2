---
type: topic-doc
title: 삼성 갤럭시 AI 온디바이스/클라우드 리서치
tags: [samsung, galaxy-ai, on-device-ai, cloud-ai, network-research, mobile, assist, pcapdroid, 삼성, 조사, 정리, ee7122, tls, 클라우드]
created: 2026-09-03
updated: 2026-09-03
split: false
---

# 삼성 갤럭시 AI 온디바이스/클라우드 리서치

## Log

### 20:16 삼성 모바일 AI 서비스 조사 및 정리
<!-- topic-doc:start:slack:C0ACDPUAKN3:20260902_201653_87ee7122 -->
<!-- chapter: 리서치 -->
<!-- date: 2026-09-03 -->
- Source: session 20260902_201653_87ee7122

#### Summary
- 삼성 Galaxy AI/안드로이드 AI 기능들을 On-device AI vs Cloud AI(Public AI)로 구분해 표로 정리 요청, 2개 서브에이전트 병렬 위임
- 완전 온디바이스(Live Translate, Chat Assist, AI Zoom 등), 완전 클라우드(Circle to Search, Generative Edit, Gemini), 하이브리드(Note Assist 요약) 기능표 제공
- 실측 방법론 정리: airplane mode 스크리닝, TLS 프록시(mitmproxy), PCAPdroid(비루팅 VPN 캡처), rooted tcpdump, adb 프로파일링 등 6가지 접근
- 연속 호출(멀티턴) 입력 데이터 전송 속도 저하를 실측할 적절한 응용/모델 운영환경이 안 보인다는 지적, 출처 명시 기록 요청
- Samsung Photo Assist(Generative Edit) 심층 조사: 삼성계정 필수, 이미지가 삼성 클라우드 서버에서 처리(저장 안 함)됨을 공식자료로 확인
- mitmproxy 갤럭시 실기기 적용 방법과 한계(SSL 피닝, Knox 워런티 소실) 정리, 비루팅 대안으로 PCAPdroid 우선 제안
- 전체 비교표 + 출처(원본 링크 전체)를 [[Knowledge/Dev/삼성-갤럭시-AI-온디바이스-클라우드-비교표|삼성 갤럭시 AI On-device vs Cloud 비교표]]로 영구 정리

#### Decisions
- 루팅+TLS 프록시보다 비루팅 PCAPdroid로 트래픽 패턴을 먼저 관찰하는 것을 실용적 1단계로 채택
- 리서치 결과는 출처(URL) 포함해 기록하기로 함

#### TODO
- [ ] PCAPdroid 기반으로 Photo Assist 연속 편집 시 이미지 재업로드/TCP 세션 유지 여부 실측 실험 설계 및 실행
- [ ] 필요시 루팅 기기 + Frida/objection으로 SSL 피닝 우회 TLS 페이로드 상세 캡처
- [ ] 멀티턴 반복호출로 인한 네트워크 성능 저하를 재현할 응용/모델 운영환경 추가 조사
- [ ] 조사 결과를 출처와 함께 연구 노트에 기록
<!-- topic-doc:end:slack:C0ACDPUAKN3:20260902_201653_87ee7122 -->
