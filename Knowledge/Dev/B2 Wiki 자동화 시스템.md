---
type: topic-doc
title: B2 Wiki 자동화 시스템
tags: [B2, b2, bugfix, cron, d5e, doc, frontmatter, github-actions, keyword_extractor, maintenance, obsidian, topic, topic-doc, 누적, 분할, 실행, 주제, 챕터, keyword, extractor, github]
created: 2026-08-31
updated: 2026-09-02
split: false
---

# B2 Wiki 자동화 시스템

## Log

### 10:42 Topic Doc(누적 주제 문서) 시스템 설계 및 구현
<!-- topic-doc:start:slack:C0ACDPUAKN3:20260831_104259_00217d5e -->
<!-- chapter: 설계 -->
<!-- date: 2026-08-31 -->
- Source: session 20260831_104259_00217d5e

#### Summary
- 기존 cron(b2-wiki-maintenance)이 대화를 날짜별 Daily Note로만 요약하고, 같은 목적/프로젝트의 대화가 하나의 문서로 누적되지 않는 문제를 지적
- 목표: 같은 주제 대화를 하나의 누적 문서(Topic Doc)로 계속 쌓고, 문서가 커지면 챕터 단위 서브페이지로 자동 분할해 목차(TOC)로 탐색 가능하게 함
- 설계 결정: 주제/챕터 매칭은 고정 목록 없이 매 실행 LLM이 기존 Knowledge/Projects 폴더를 스캔해 동적으로 판단
- 저장 위치는 새 최상위 폴더 대신 기존 Knowledge/{Dev,Ideas,Business}/, Projects/<name>/ 구조를 그대로 사용
- 분할 기준: 챕터(논리 단계) 우선 분할 + 챕터 자체가 커지면 줄수 기준 추가 분할(파트 롤오버)
- Daily Note는 유지하고 Topic Doc과 상호 wikilink로 연결

#### Decisions
- 신규 스크립트 topic_doc.py(upsert/split/status) 작성 및 /tmp/testvault에서 생성→멱등성→분할→롤오버까지 실제 실행 검증 완료
- conversation-to-obsidian 스킬에 Workflow D(Topic Doc) 추가, b2-wiki-maintenance 스킬 파이프라인을 8→10단계로 갱신
- cron job(9d85ae79a8f7) 프롬프트에 PHASE 2.5(Topic Doc 누적), PHASE 2.6(분할 점검) 단계 삽입 및 즉시 1회 실행 트리거

#### TODO
- [ ] 실제 운영 데이터로 Topic Doc이 올바른 주제/챕터에 매칭되는지 몇 차례 실행 후 점검
- [ ] 문서 분할이 실제로 발생했을 때 TOC/서브페이지 링크가 Obsidian/Quartz에서 정상 렌더링되는지 확인
<!-- topic-doc:end:slack:C0ACDPUAKN3:20260831_104259_00217d5e -->

### 18:11 keyword_extractor.py frontmatter 오프바이-N 버그로 GitHub Pages 빌드 실패 진단·수정
<!-- topic-doc:start:slack:C0ACDPUAKN3:20260901_181154_ecf0aa33 -->
<!-- chapter: 이슈해결 -->
<!-- date: 2026-09-02 -->
- Source: session 20260901_181154_ecf0aa33

#### Summary
- Sangrok이 "문서 업데이트 로직이 돌았는데 문제가 생긴 것 같다"고 보고, B2 wiki 유지보수 크론(18:04 실행분)의 오류를 진단·수정한 세션
- 원인: keyword_extractor.py의 frontmatter tags 삽입 로직에 오프바이-N 버그가 있어, 닫는 `---` 대신 의미없는 `-` 한 줄을 남겨 YAML frontmatter가 깨짐 — Topic Doc 자동 분할이 처음 실행되며 새로 생성된 AIPT 챕터 파일 6개(구현/문서화/이슈해결/설계/테스트환경/검토)가 오염됨
- 이 YAML 손상으로 GitHub Actions "Deploy Quartz to GitHub Pages" 빌드가 `end of the stream or a document separator is expected` 에러로 2회 연속 실패
- keyword_extractor.py의 frontmatter 삽입 로직을 수정하고, vault 전체를 스캔해 오염 파일이 이 6개뿐임을 확인 후 손상된 `-` 줄만 정확히 제거(본문 내용은 무손상)
- YAML 파싱 검증 통과, keyword_extractor 재실행 회귀 없음, vault_lint critical=0 확인 후 커밋(7f6db55) 푸시, GitHub Actions 빌드 실제 성공(build 35s + deploy 10s)까지 확인
- 결론: 오늘 발생한 두 문제(broken_links 오탐 + 빌드 실패)는 같은 원인 사슬 — Topic Doc 자동 분할 기능이 처음 실행되며 그동안 숨어있던 유지보수 스크립트 3개(vault_lint, link_fixer, keyword_extractor)의 버그가 동시에 드러난 것

#### Decisions
- keyword_extractor.py의 frontmatter 삽입 오프바이-N 버그를 근본 수정 (커밋 7f6db55)
- 오염된 6개 AIPT 챕터 파일은 손상된 `-` 줄만 정밀 제거해 복구, 본문은 건드리지 않음
- 수정 후 GitHub Pages 빌드까지 실제로 성공하는지 확인하는 것을 완료 기준으로 삼음

#### TODO
- [ ] 없음 (해당 세션에서 원인 파악·수정·검증까지 완료)
<!-- topic-doc:end:slack:C0ACDPUAKN3:20260901_181154_ecf0aa33 -->
