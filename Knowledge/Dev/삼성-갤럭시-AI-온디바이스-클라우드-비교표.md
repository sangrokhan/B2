---
date: 2026-09-02
type: knowledge
project: TCP 프로토콜 연구
status: reference
tags: [samsung, galaxy-ai, on-device-ai, cloud-ai, mobile, android, network-research]
---

# 삼성 Galaxy AI / 안드로이드 AI 기능 — On-device vs Cloud AI 비교표

> TCP idle 후 cwnd reset이 LLM 멀티턴 요청에 미치는 영향 연구([[TCP 프로토콜 연구]])의
> 실제 응용 사례를 탐색하는 과정에서 삼성 모바일 AI 기능들을 조사한 참고 자료.
> 결론: Galaxy AI 개별 기능은 대부분 단발 요청이라 "멀티턴 세션 유지 중 idle" 케이스의
> 직접적 실측 대상은 아니지만, on-device/cloud 구분과 실측 방법론 자체는 재사용 가치가 있어 기록.

## 1. 기능별 On-device / Cloud 분류

| 기능 | 처리 위치 | 사용 모델(추정/공식) | 근거 |
|---|---|---|---|
| Live Translate (통화 실시간 통역) | On-device | Samsung 자체 NMT | [samsung.com/galaxy-ai](https://www.samsung.com/us/galaxy-ai/) |
| Interpreter (대면 통역) | On-device | Samsung 자체 NMT | [samsung.com/galaxy-ai](https://www.samsung.com/us/galaxy-ai/) |
| Chat Assist (메시지 번역/톤변환) | On-device | Samsung 자체 언어모델 | [samsung.com/galaxy-ai](https://www.samsung.com/us/galaxy-ai/) |
| Instant Slow-mo / 영상 AI | On-device | Samsung NPU 모델 | [samsung.com/galaxy-ai](https://www.samsung.com/us/galaxy-ai/) |
| AI Zoom | On-device | Samsung 이미지 NPU 모델 | [samsung.com/galaxy-ai](https://www.samsung.com/us/galaxy-ai/) |
| Bixby 기본 명령 | On-device | Samsung NLU | [samsung.com/apps/bixby](https://www.samsung.com/us/apps/bixby/) |
| Voice Recorder 전사(기본) | On-device | Samsung STT | [samsung.com/galaxy-ai](https://www.samsung.com/us/galaxy-ai/) |
| Note Assist (요약/서식) | 하이브리드(추정) | Gauss + 필요시 클라우드 | [samsung.com/galaxy-ai](https://www.samsung.com/us/galaxy-ai/) |
| Transcript Assist 요약 | 하이브리드(추정) | 온디바이스 STT + 클라우드 요약 | [samsung.com/galaxy-ai](https://www.samsung.com/us/galaxy-ai/) |
| Bixby 복잡 질의 | 하이브리드(추정) | 온디바이스 NLU + 클라우드 백엔드 | [samsung.com/apps/bixby](https://www.samsung.com/us/apps/bixby/) |
| Circle to Search | Cloud (공식 확인) | Google Search/Lens 백엔드 | [blog.google/circle-to-search](https://blog.google/products-and-platforms/platforms/android/google-ai-samsung-galaxy-s24/) |
| **Generative Edit / Photo Assist** | **Cloud (공식 확인)** | Samsung Gauss2 (서버), 네트워크+삼성계정 필수 | [삼성 뉴스룸 프라이버시](https://news.samsung.com/global/your-privacy-secured-how-galaxy-ai-empowers-you-to-take-control-of-your-data), [EU 커뮤니티 공지](https://eu.community.samsung.com/t5/tips-how-to/meet-generative-edit-the-new-galaxy-ai-magic-in-photo-editor/ba-p/13226659), [삼성 지원 FAQ](https://www.samsung.com/ae/support/mobile-devices/when-i-use-ai-photo-editing-features-does-my-photo-get-uploaded-to-the-internetcloud-can-someone-see-it/) |
| Sketch to Image | Cloud | Samsung Gauss2 (서버) | [news.samsung.com/gauss2](https://news.samsung.com/global/samsung-electronics-hosts-samsung-developer-conference-korea-2024-unveils-its-improved-gen-ai-model) |
| Portrait Studio | Cloud | Samsung Gauss2 (서버) | [news.samsung.com/gauss2](https://news.samsung.com/global/samsung-electronics-hosts-samsung-developer-conference-korea-2024-unveils-its-improved-gen-ai-model) |
| Gemini 통합 어시스턴트 | Cloud(+일부 Nano) | Google Gemini Pro/Advanced | [blog.google/galaxy-s24-gemini](https://blog.google/products-and-platforms/platforms/android/google-ai-samsung-galaxy-s24/) |
| Browsing Assist (Samsung Internet 요약) | Cloud | 서버 LLM | [samsunginternet.com](https://browser.samsung.com) |
| Now Bar / Now Brief (S25) | Cloud | Samsung+Google 백엔드 | [samsung.com/galaxy-s25/ai](https://www.samsung.com/us/smartphones/galaxy-s25/) |

**주의**: 삼성이 기능별 on-device/cloud 구분을 공식 명시하지 않는 경우가 많아
'하이브리드' 항목은 응답속도·오프라인 지원 여부 등 정황 근거 기반 추정. 단,
**Generative Edit/Photo Assist는 삼성 공식 발표·지원 FAQ로 클라우드 처리가
명시적으로 확인됨** (2절 참고).

## 2. 심층 확인 — Generative Edit(Photo Assist) 실제 동작

Slack 대화 중 "이미지 전체를 매번 새로 업로드하는가?"라는 질문에서 추가 조사:

- **네트워크 연결 + 삼성 계정 로그인 필수** — 오프라인 시 기능 자체 비활성화.
  Samsung Newsroom "Your Privacy, Secured"(2025-09-09) 각주 2:
  *"Generative Edit feature for Photo Assist requires a network connection and
  Samsung Account login."*
  → [원문](https://news.samsung.com/global/your-privacy-secured-how-galaxy-ai-empowers-you-to-take-control-of-your-data)
- **이미지는 서버로 전송되어 처리되고, 완료 후 즉시 삭제** — 삼성이 장기 저장하지 않음.
  Samsung EU Community 공식 안내(2025-08-03):
  *"☁️ Images are processed on a server but not stored by Samsung."*
  → [원문](https://eu.community.samsung.com/t5/tips-how-to/meet-generative-edit-the-new-galaxy-ai-magic-in-photo-editor/ba-p/13226659)
- **생성 완료 즉시 원본·결과 이미지 서버에서 삭제**. Samsung 공식 지원 FAQ(Gulf):
  *"Customer data is immediately deleted from servers as soon as the generation
  is complete."*
  → [원문](https://www.samsung.com/ae/support/mobile-devices/when-i-use-ai-photo-editing-features-does-my-photo-get-uploaded-to-the-internetcloud-can-someone-see-it/)
- **재편집 시 매번 재업로드(stateless)인지 세션 유지인지는 삼성 미공개, 공개
  리버스엔지니어링 사례도 없음 — 미확인, 실측 필요**. 일반 생성형 이미지 API
  관행(Adobe Firefly, Google Magic Editor 등)상 편집마다 별도 stateless 요청일
  가능성이 높지만, 그 아래 TCP/TLS 커넥션(HTTP/2 keep-alive 등)은 재사용될 수
  있어 둘을 구분해 검증 필요.
- Settings > Galaxy AI > "Process data only on device" 마스터 스위치로 클라우드
  처리 전면 차단 가능(단, Generative Edit 등 클라우드 의존 기능은 사용 불가).
  → [삼성 공식 지원](https://www.samsung.com/us/support/answer/ANS10000753/),
  [SamMobile 해설](https://www.sammobile.com/news/use-galaxy-ai-without-sending-data-to-samsung-heres-what-you-lose/)

## 3. 핵심 구조

- 삼성 자체 모델 Gauss/Gauss2는 경량(온디바이스) + 대형(클라우드 서버) 버전을
  병행 운영하는 하이브리드 아키텍처.
- 구글과는 Gemini Nano(온디바이스, 요약/텍스트 일부) / Gemini Pro·Advanced(클라우드,
  Circle to Search·어시스턴트 대화)로 이원화 협업.
- 2025년 말 이후 유료화 논의는 주로 클라우드 연산 비용 때문이라는 분석
  ([The Verge](https://www.theverge.com/2024/1/19/24044251/samsung-galaxy-s24-ultra-ai-features-cost-2025)).

## 4. 실측/테스트 방법론

| 방법 | 장점 | 한계 | 도구 |
|---|---|---|---|
| Airplane mode 1차 스크리닝 | root 불필요, 가장 간단 | 부분 폴백 가능성, 단독 근거로 약함 | 없음 |
| TLS 프록시 패킷 캡처 | 목적지 서버+페이로드까지 확인하는 결정적 증거 | Android 7+ 유저CA 기본 비신뢰, 삼성 시스템 앱 SSL 피닝 강함(Frida+objection 우회 필요), QUIC/HTTP3 미캡처 가능 | [mitmproxy](https://mitmproxy.org/), [Burp Suite](https://portswigger.net/burp), [HTTP Toolkit](https://github.com/httptoolkit/httptoolkit) |
| 온디바이스 VPN 캡처 앱 | root 불필요, SNI·트래픽량·타이밍 확인 | payload 내용 복호화 불가 | [PCAPdroid](https://github.com/emanuele-f/PCAPdroid) |
| Rooted tcpdump+Wireshark | 가장 로우레벨 정밀 캡처 | 루팅 시 Knox 워런티 소실, 일부 보안기능 영구 비활성화 | [tcpdump](https://www.tcpdump.org/), [Wireshark](https://www.wireshark.org/) |
| adb 배터리/네트워크 프로파일링 | 코드 계측 불필요, 앱별 트래픽/전력 델타로 간접 증거 | 백그라운드 트래픽과 혼동 가능 | [adb](https://developer.android.com/tools/adb), [Battery Historian](https://developer.android.com/topic/performance/power/battery-historian), Android Studio Energy/Network Profiler |
| 응답 지연시간(latency) 측정 | 온디바이스(수십~200ms) vs 클라우드(수백ms~초) 구분에 유효 | 단독 임계값 불안정, tc qdisc 쓰로틀링과 결합 권장 | 반복측정 스크립트, tc |

### mitmproxy 갤럭시 실기기 적용 가능 여부 (2026-09-02 확인)

- Wi-Fi 프록시 설정만으로 HTTP는 바로 캡처되나, HTTPS는 mitmproxy CA 인증서 설치 필요.
- Android 7+ 는 앱이 기본적으로 유저 설치 CA를 신뢰하지 않음(`network_security_config`
  미허용 시). 비루팅 상태에서는 시스템 CA로 못 올림.
  → [참고](https://httptoolkit.com/blog/android-14-install-system-ca-certificate/)
- 삼성 시스템 앱(Photo Assist 등)은 SSL 인증서 피닝이 강해, CA를 신뢰해도 앱이
  자체 검증으로 연결을 끊음 → 루팅 + [Frida](https://frida.re/) +
  [objection](https://github.com/sensepost/objection)으로 런타임 피닝 우회 필요.
- 루팅 시 Knox Warranty Bit 영구 소실 리스크 → 실기기 대신 별도 테스트폰 권장.
- **비루팅 대안**: PCAPdroid로 목적지(SNI)·페이로드 크기·타이밍만 우선 관찰 후,
  내용 확인이 꼭 필요할 때만 루팅 실험 고려.

**권장 실험 절차**: ① Airplane mode 1차 스크리닝 → ② 지연시간 반복측정 →
③ PCAPdroid로 트래픽 패턴(SNI/바이트량/타이밍) 1차 수집 → ④ 필요시 루팅+TLS
프록시로 payload 내용까지 확인 → ⑤ 배터리/CPU 프로파일 교차검증 → 기능별
"완전 온디바이스 / 하이브리드 / 완전 클라우드" 분류.

## 5. 한계 / 후속 조사 필요

- Galaxy AI를 특정한 학술 리버스엔지니어링/트래픽 실측 사례는 확인하지 못함 —
  대신 일반 모바일 트래픽 분석 서베이([arXiv:1708.03766](https://arxiv.org/abs/1708.03766))를
  방법론 근거로 활용.
- Generative Edit의 "매 편집마다 이미지 전체 재업로드 vs 세션/커넥션 재사용" 여부는
  미확인 — 실제 갤럭시 기기로 PCAPdroid 또는 루팅+mitmproxy 실측 필요.
- **TCP idle cwnd reset 연구 응용처 탐색**: Galaxy AI 개별 기능은 단발 요청 위주라
  "멀티턴 세션 내 idle 발생 → cwnd reset" 케이스의 전형적 테스트 대상은 아님. 다만
  Generative Edit처럼 "편집→검토(idle)→재편집" 반복 패턴이 있는 기능은 idle 구간과
  재요청 시 TCP 재활용 여부를 살펴볼 여지가 있어 후속 실측 후보로 남겨둠. 더 전형적인
  후보는 여전히 멀티턴 챗봇/에이전트 루프형 앱(Gemini 앱 대화 등). AI 코딩 에이전트는
  모바일 네이티브 실행이 아니라 PC/서버 환경 사례이므로 제외.

## 전체 출처 목록

- https://www.samsung.com/us/galaxy-ai/
- https://news.samsung.com/global/samsung-electronics-hosts-samsung-developer-conference-korea-2024-unveils-its-improved-gen-ai-model
- https://blog.google/products-and-platforms/platforms/android/google-ai-samsung-galaxy-s24/
- https://blog.google/products-and-platforms/platforms/android/google-ai-samsung-galaxy-s24/
- https://www.samsung.com/us/smartphones/galaxy-s25/
- https://www.samsung.com/us/apps/bixby/
- https://browser.samsung.com
- https://www.theverge.com/2024/1/19/24044251/samsung-galaxy-s24-ultra-ai-features-cost-2025
- https://news.samsung.com/global/your-privacy-secured-how-galaxy-ai-empowers-you-to-take-control-of-your-data
- https://www.sammobile.com/news/use-galaxy-ai-without-sending-data-to-samsung-heres-what-you-lose/
- https://www.samsung.com/us/support/answer/ANS10000753/
- https://eu.community.samsung.com/t5/tips-how-to/meet-generative-edit-the-new-galaxy-ai-magic-in-photo-editor/ba-p/13226659
- https://www.samsung.com/ae/support/mobile-devices/when-i-use-ai-photo-editing-features-does-my-photo-get-uploaded-to-the-internetcloud-can-someone-see-it/
- https://mitmproxy.org/
- https://portswigger.net/burp
- https://github.com/httptoolkit/httptoolkit
- https://httptoolkit.com/blog/android-14-install-system-ca-certificate/
- https://github.com/sensepost/objection
- https://frida.re/
- https://github.com/emanuele-f/PCAPdroid
- https://www.tcpdump.org/
- https://www.wireshark.org/
- https://developer.android.com/topic/performance/power/battery-historian
- https://developer.android.com/studio/profile/energy-profiler
- https://developer.android.com/studio/profile/network-profiler
- https://developer.android.com/reference/android/net/TrafficStats
- https://developer.android.com/tools/adb
- https://arxiv.org/abs/1708.03766

## Source
- Slack #연구 thread 1788347812.797359 (2026-09-02)
