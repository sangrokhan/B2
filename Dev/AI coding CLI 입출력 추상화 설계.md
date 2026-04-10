---
type: dev-note
topic: AI coding CLI 입출력 추상화 설계
created: 2026-04-09 09:31
tags:
  - dev
  - ai-coding
  - cli
  - abstraction
---

# AI coding CLI 입출력 추상화 설계

## 요약

Claude Code, Codex CLI, Gemini CLI를 공통 컴포넌트로 추상화해 사용할 수 있는지, 특히 *CLI 관점의 입출력 형식*을 기준으로 분석했다.

결론은 다음과 같다.

- 세 도구 모두 *headless 실행*이 가능하다.
- 세 도구 모두 *작업 경로(cwd) 지정*이 가능하다.
- 세 도구 모두 *headless 실행 시 모델 지정*이 가능하다.
- 세 도구 모두 *JSON 계열 출력*을 받을 수 있다.
- 세 도구 모두 *파일 기반 컨텍스트 제공*은 가능하지만, 완전히 동일한 네이티브 인터페이스는 아니다.
- 따라서 공통 설계는 *파일 직접 첨부 추상화*보다, *파일 내용을 읽어 하나의 프롬프트로 합성한 뒤 stdin으로 전달*하는 방식이 가장 안정적이다.

즉, 공통 분모는 아래 3가지다.

1. 작업 디렉터리 지정
2. stdin 기반 입력 제공
3. stdout 기반 JSON 수집

## 도구별 관찰 결과

### 1) Claude Code

- headless 실행 가능
  - `claude -p "..."`
- headless에서 모델 지정 가능
  - CLI reference에 `--model <model>` 전역 플래그가 있고, `-p` print/headless 모드와 함께 사용할 수 있는 구조다.
  - 실무적으로는 `claude --model <MODEL> -p "..."` 형태로 보는 것이 맞다.
- 파일/컨텍스트 제공 방식
  - `cat file | claude -p "..."` 형태의 stdin 파이프 가능
  - `--add-dir` 로 추가 디렉터리 접근 가능
  - `--append-system-prompt-file` 계열 플래그 존재
- 출력
  - `--output-format json` / `stream-json` 가능
- 특징
  - 세 도구 중 *시스템 프롬프트 파일 주입*에 가장 직접적인 기능을 제공한다.

### 2) Codex CLI

- headless 실행 가능
  - `codex exec "..."`
- headless에서 모델 지정 가능
  - `codex exec --help` 기준 `-m, --model <MODEL>` 지원
  - 예: `codex exec -m gpt-5.4 "..."`
  - 추가로 `-c model=...` 계열 설정 override도 가능
- 파일/컨텍스트 제공 방식
  - 프롬프트를 stdin으로 받을 수 있음
  - stdin을 추가 컨텍스트로 붙일 수 있음
  - `-C` 로 cwd 지정 가능
  - `--add-dir` 로 추가 디렉터리 접근 가능
  - 이미지 입력은 `-i/--image`
- 출력
  - `--json` 으로 JSONL 출력 가능
  - `-o/--output-last-message` 로 최종 메시지 파일 저장 가능
- 특징
  - 텍스트 파일을 위한 범용 `--file` 플래그보다는, *workspace 노출 + stdin* 패턴이 자연스럽다.

### 3) Gemini CLI

- headless 실행 가능
  - `-p` / `--prompt`
  - non-TTY 환경에서도 headless
- headless에서 모델 지정 가능
  - `gemini --help` 기준 `-m, --model` 지원
  - docs에도 `--model` 플래그로 특정 Gemini 모델 지정 가능하다고 명시
  - 예: `gemini -m gemini-2.5-pro -p "..."`
  - 주의: docs 기준 `--model` 은 sub-agents가 쓰는 모델까지 강제로 덮어쓰지는 않음
- 파일/컨텍스트 제공 방식
  - stdin 입력 가능
  - `--include-directories` 로 추가 디렉터리 포함 가능
- 출력
  - `--output-format json` / `stream-json` 가능
- 특징
  - Codex와 유사하게, *파일 첨부형*보다 *디렉터리 접근 + stdin* 패턴이 공통 분모다.

## 핵심 해석

### 1. 공통적으로 가능한 것

세 도구 모두 다음 인터페이스는 공통으로 맞출 수 있다.

- `cwd`: 작업 루트 경로
- `input`: stdin으로 전달할 합성 프롬프트
- `outputFormat`: json 또는 stream-json 계열
- `model`: 선택 사항
- `extraArgs`: 도구별 세부 옵션

## 모델 지정 조사 결과

headless에서 기본 모델만 호출되는지 확인한 결과, *세 도구 모두 headless 입력 명령 수준에서 모델 지정이 가능하다.*

- Claude Code: `--model`
- Codex CLI: `-m`, `--model`
- Gemini CLI: `-m`, `--model`

다만 의미상 차이는 있다.

- Claude Code: 세션 시작 플래그 성격이 강함
- Codex CLI: non-interactive 실행에서 직접 모델 override 가능
- Gemini CLI: headless에서도 모델 지정 가능하지만, 문서 기준 sub-agent 모델까지 완전히 동일하게 고정되지는 않을 수 있음

따라서 공통 추상화에서는 아래 전제를 둘 수 있다.

- `model?: string` 을 공통 요청 필드로 둔다.
- adapter는 이를 각 도구의 CLI 플래그로 매핑한다.
- 단, *모델 강제성의 semantics는 도구별로 동일하다고 가정하지 않는다.*

### 2. 공통적으로 완전히 같지 않은 것

세 도구 모두 *파일을 제공*할 수는 있지만, 그 의미가 완전히 같지는 않다.

예를 들어 `persona.md` 와 `task.md` 를 준비해 두었다고 해도:

- Claude Code는 system prompt file 계열로 다룰 수 있다.
- Codex/Gemini는 보통 user prompt 또는 stdin 컨텍스트로 다루게 된다.

즉, 아래 같은 인터페이스를 그대로 네이티브 매핑하기는 어렵다.

```ts
{
  personaFile: "/prompts/persona.md",
  taskFile: "/prompts/task.md"
}
```

왜냐하면 각 CLI가 이 파일들을 *같은 우선순위와 같은 의미*로 받지 않기 때문이다.

## 권장 추상화 방식

### 설계 원칙

공통 계층에서는 *파일을 도구에 직접 전달하는 것*이 아니라, *파일 내용을 읽어서 하나의 표준 입력 문서로 합성*하는 방식으로 본다.

권장 순서:

1. `personaFile`, `taskFile`, `contextFiles[]` 읽기
2. 내부 표준 포맷으로 합성
3. 합성 결과를 stdin으로 주입
4. CLI는 cwd 안에서 실행
5. stdout JSON을 수집 및 파싱

### 내부 표준 프롬프트 예시

```text
[Persona]
당신은 신중한 코드 리뷰어다.
[/Persona]

[Task]
변경사항을 검토하고 위험 요소를 JSON으로 반환하라.
[/Task]

[Context File: diff.patch]
...
[/Context File]

[Context File: spec.md]
...
[/Context File]

[Output Contract]
Return valid JSON only.
```

이 방식의 장점:

- 세 도구 모두 동일한 입력 생성 로직 사용 가능
- 도구별 차이는 *실행 어댑터*에만 한정됨
- 파일 경로나 첨부 방식을 추상화 레벨에 노출하지 않아도 됨
- 테스트가 쉬움

## 공통 인터페이스 초안

초기 분석은 세 도구를 모두 비교했지만, *v1 구현 범위는 `codex` 와 `gemini` 두 도구만 포함*한다.
Claude Code는 비교 분석 결과만 남기고, 실제 adapter 구현은 후속 버전으로 미룬다.

```ts
export type AiCodingTool = 'codex' | 'gemini';

export interface PromptSpec {
  personaFile?: string;
  taskFile: string;
  contextFiles?: string[];
  extraInstructions?: string[];
}

export interface RunRequest {
  tool: AiCodingTool;
  cwd: string;
  prompt: PromptSpec;
  outputFormat: 'final-json';
  model?: string;
  extraArgs?: string[];
}

export interface RunResult {
  stdout: string;
  stderr: string;
  exitCode: number;
  parsed?: unknown;
}
```

## 입력 합성기 초안

```ts
import { readFile } from 'node:fs/promises';

async function maybeRead(path?: string): Promise<string | null> {
  if (!path) return null;
  return readFile(path, 'utf8');
}

export async function buildCompositePrompt(spec: PromptSpec): Promise<string> {
  const parts: string[] = [];

  const persona = await maybeRead(spec.personaFile);
  if (persona) {
    parts.push('[Persona]');
    parts.push(persona.trim());
    parts.push('[/Persona]');
    parts.push('');
  }

  const task = await readFile(spec.taskFile, 'utf8');
  parts.push('[Task]');
  parts.push(task.trim());
  parts.push('[/Task]');
  parts.push('');

  for (const file of spec.contextFiles ?? []) {
    const content = await readFile(file, 'utf8');
    parts.push(`[Context File: ${file}]`);
    parts.push(content.trim());
    parts.push('[/Context File]');
    parts.push('');
  }

  if (spec.extraInstructions?.length) {
    parts.push('[Extra Instructions]');
    parts.push(...spec.extraInstructions);
    parts.push('[/Extra Instructions]');
    parts.push('');
  }

  parts.push('[Output Contract]');
  parts.push('Return valid JSON only.');
  parts.push('[/Output Contract]');

  return parts.join('\n');
}
```

## 실행 어댑터 방향

### Claude adapter

```ts
function buildClaudeArgs(req: RunRequest): string[] {
  return [
    '--print',
    '--output-format',
    req.outputFormat,
    ...(req.model ? ['--model', req.model] : []),
    ...(req.extraArgs ?? []),
  ];
}
```

주의:
- Claude는 필요 시 `--append-system-prompt-file` 같은 고급 기능을 별도 옵션으로 확장할 수 있다.
- 하지만 공통 계층에서는 stdin 합성 방식을 기본값으로 두는 편이 단순하다.

### Codex adapter

```ts
function buildCodexArgs(req: RunRequest): string[] {
  return [
    'exec',
    ...(req.outputFormat === 'stream-json' ? ['--json'] : []),
    ...(req.model ? ['--model', req.model] : []),
    '-C', req.cwd,
    ...(req.extraArgs ?? []),
    '-',
  ];
}
```

주의:
- Codex의 `--json` 은 JSONL 스트림에 가깝다.
- 단일 JSON 객체가 필요하면 wrapper에서 후처리하거나 마지막 메시지만 파싱하는 계층이 필요하다.

### Gemini adapter

```ts
function buildGeminiArgs(req: RunRequest): string[] {
  return [
    '--prompt',
    '',
    '--output-format',
    req.outputFormat,
    ...(req.model ? ['--model', req.model] : []),
    ...(req.extraArgs ?? []),
  ];
}
```

주의:
- 실제 구현에서는 `--prompt` 직접 전달보다 stdin 기반 구성을 우선 고려해야 한다.
- 또는 wrapper가 합성 프롬프트를 `--prompt` 값으로 넣고, 큰 파일은 cwd 안에서 읽도록 유도하는 방식도 가능하다.

## 출력 해석 원칙

### JSON 출력은 기본적으로 stdout

세 도구 모두 JSON 출력은 기본적으로 *stdout으로 나온다*.

즉 아래처럼 사용할 수 있다.

```bash
tool ... > result.json
```

해석:
- `json` 출력은 보통 단일 JSON 객체 또는 최종 응답 중심
- `stream-json` / `--json` 은 보통 JSONL 이벤트 스트림

### 실무 권장

wrapper 기준으로는 다음 두 모드를 분리하는 것이 좋다.

1. `final-json`
   - 최종 결과만 필요할 때
   - 후처리 단순
2. `event-stream`
   - 진행 상황, tool call, 중간 이벤트까지 수집할 때
   - 실행 기록 및 디버깅에 유리

## 병렬 실행 관점

세 도구 모두 여러 프로세스를 동시에 띄우는 방식의 병렬 실행은 가능하다.

다만 공통 설계에서는 아래 원칙을 강하게 두는 편이 안전하다.

- 각 실행은 *서로 다른 worktree 또는 격리 디렉터리* 사용
- stdout/stderr 로그 파일 분리
- 산출 파일 경로 분리
- 세션 파일을 남기는 도구는 `ephemeral` 또는 독립 세션 전략 고려

즉, 병렬성은 도구가 아니라 *런타임 격리 설계*의 문제로 다루는 편이 맞다.

## 최종 결론

### 가능한 공통 추상화

가능하다. 다만 공통 인터페이스는 아래 수준으로 잡아야 한다.

- `cwd`
- `prompt files` 입력 스펙
- `stdin` 합성 입력
- `stdout JSON` 수집
- `tool-specific adapter`

### 피해야 할 추상화

아래는 공통 인터페이스처럼 보이지만 실제로는 잘 깨질 수 있다.

- “모든 도구가 동일한 의미로 persona file을 system prompt로 받는다”는 가정
- “모든 도구가 범용 file attachment 플래그를 가진다”는 가정
- “모든 JSON 출력 형식이 동일 구조다”는 가정

### 추천 설계 문장

*세 도구의 공통 분모는 `파일 자체 전달`이 아니라 `파일 내용을 합성한 표준 입력`과 `표준 출력 JSON 수집`이다.*

이 문장을 기준으로 구현하면, Claude/Codex/Gemini를 하나의 상위 orchestration 레이어 아래에 안정적으로 묶을 수 있다.

## 원문 메모

- 분석 대상: Claude Code, Codex CLI, Gemini CLI
- 초점: headless, 경로 지정, JSON 출력, 파일 기반 작업 지시 제공 가능 여부
- 설계 관점: 추상화 레이어를 가진 실행 어댑터 구현

---

## 개발 Spec

이 섹션은 실제 구현을 위한 기준 spec이다.
이미 합의된 결정 사항은 본문에 반영했고, 남은 항목만 별도 체크리스트로 관리한다.

### 1. 목적

Claude Code, Codex CLI, Gemini CLI를 하나의 공통 인터페이스 아래에서 실행할 수 있는 runner 계층을 만든다.

이 계층의 목표는 다음과 같다.

- 도구별 실행 옵션 차이를 adapter로 감춘다.
- 상위 호출자는 공통 입력 스펙만 전달한다.
- 파일 기반 작업 지시를 공통 방식으로 취급한다.
- 결과를 `final-json` 형태로 일관되게 수집한다.
- 이후 오케스트레이션, 큐잉, 병렬 실행, 재시도 로직을 쉽게 얹을 수 있도록 한다.

### 2. 비목표

이번 spec 범위에서 아래는 우선 제외한다.

- GUI/TUI 기반 상호작용 지원
- 각 도구의 세션 히스토리 완전 통합
- 툴 내부 subagent 기능의 공통 추상화
- 웹 로그인, 인증 UI 자동화
- 결과 품질 평가 시스템
- 비용 최적화 정책 자동화

### 3. 핵심 설계 원칙

#### 3.1 공통 입력은 파일 첨부가 아니라 프롬프트 합성으로 본다

상위 계층은 `persona file`, `task file`, `context files[]` 를 입력으로 받되, 실제 CLI 전달 전에는 하나의 합성 프롬프트로 만든다.

#### 3.2 공통 출력은 stdout 기준으로 본다

기본 출력 채널은 stdout으로 통일한다.
필요하면 wrapper 내부에서 파일 저장, 파싱, 후처리를 수행한다.

#### 3.3 도구 차이는 adapter에 한정한다

- 명령어 이름
- cwd 지정 방식
- JSON 출력 옵션
- stdin 처리 방식
- stream-json 여부

이 차이는 adapter 레이어에서만 처리한다.

#### 3.4 병렬 실행은 런타임 격리로 해결한다

병렬 실행 시 각 런은 서로 다른 디렉터리 또는 worktree를 사용해야 한다.

### 4. 사용자 관점 요구사항

상위 호출자는 최소한 아래 정보만 주면 된다.

- 사용할 도구 종류
- 작업 디렉터리
- 페르소나 파일 경로
- 작업 내용 파일 경로
- 추가 컨텍스트 파일 목록
- 선택적 모델 지정
- 선택적 도구별 추가 인자

### 5. 기능 요구사항

#### FR-1. 도구 선택

v1 시스템은 다음 도구를 지원해야 한다.

- Codex CLI
- Gemini CLI

Claude Code는 분석 대상에는 포함하지만, 구현 범위에서는 제외한다.

#### FR-2. 작업 디렉터리 지정

시스템은 실행별로 cwd를 지정할 수 있어야 한다.

#### FR-3. headless 모델 지정

시스템은 headless 실행 시 모델을 명시적으로 지정할 수 있어야 한다.

- `model?: string`
- 지정하지 않으면 각 도구의 기본 모델 또는 profile/config 값을 사용
- 지정하면 adapter가 해당 도구의 모델 지정 플래그로 매핑

#### FR-4. 파일 기반 입력 스펙 지원

시스템은 아래 파일 입력을 받을 수 있어야 한다.

- `personaFile?: string`
- `taskFile: string`
- `contextFiles?: string[]`

#### FR-5. 프롬프트 합성

시스템은 위 파일 내용을 읽어 하나의 표준 프롬프트 문자열로 합성해야 한다.

#### FR-6. JSON 출력 표준

v1의 표준 출력은 `final-json` 으로 고정한다.

- 상위 호출자는 도구별 스트림 형식을 직접 다루지 않는다.
- wrapper가 도구별 출력을 정규화해 최종 JSON 객체로 반환한다.
- `event-stream` 지원은 v2 이후 확장 항목으로 남긴다.

#### FR-7. 실행 결과 수집

시스템은 아래 결과를 반환해야 한다.

- stdout
- stderr
- exitCode
- parsed output if available

#### FR-8. 도구별 adapter 분리

각 도구별 명령 생성 로직은 독립 adapter로 분리되어야 한다.

#### FR-9. 병렬 실행 대응 가능 구조

초기 구현에서 병렬 실행 자체를 꼭 제공하지 않더라도, 실행 단위가 독립적이라 이후 병렬 scheduler를 붙일 수 있어야 한다.

### 6. 비기능 요구사항

#### NFR-1. 예측 가능성

같은 입력 파일과 같은 옵션이면 가능한 한 동일한 실행 계약을 제공해야 한다.

#### NFR-2. 추적 가능성

최소한 아래 디버깅 정보가 남아야 한다.

- 어떤 도구를 사용했는지
- 어떤 cwd에서 실행했는지
- 어떤 입력 파일이 사용됐는지
- 어떤 최종 프롬프트가 생성됐는지
- 어떤 stdout/stderr가 반환됐는지

로그는 작업 단위(run/task) JSON 아티팩트로 저장하는 것을 기본 정책으로 한다.

#### NFR-3. 확장 가능성

향후 추가 CLI 도구가 생겨도 adapter만 추가하면 붙일 수 있어야 한다.

#### NFR-4. 안전성

병렬 실행 또는 반복 실행 시 작업 디렉터리 충돌을 피할 수 있어야 한다.

### 7. 제안 데이터 모델

```ts
export type ToolKind = 'codex' | 'gemini';

export interface PromptFiles {
  personaFile?: string;
  taskFile: string;
  contextFiles?: string[];
  extraInstructions?: string[];
}

export interface RunRequest {
  tool: ToolKind;
  cwd: string;
  promptFiles: PromptFiles;
  model?: string;
  extraArgs?: string[];
  timeoutMs?: number;
  runId?: string;
}

export interface RunArtifacts {
  runId: string;
  compositePrompt: string;
  stdout: string;
  stderr: string;
  exitCode: number;
  parsedOutput?: unknown;
  logFilePath?: string;
}
```

### 8. 제안 모듈 구조

v1에서는 parser를 별도 모듈로 분리하지 않고, runner 내부의 얇은 `normalizeFinalJson()` 유틸로 처리한다.
이 단계에서는 복잡한 파싱 계층보다, *최종 JSON 추출과 최소 검증*만 있으면 충분하다.

```ts
/core
  prompt-builder.ts
  run-types.ts
/adapters
  codex-adapter.ts
  gemini-adapter.ts
/runtime
  exec-runner.ts
  final-json.ts
  workspace-isolation.ts
/index.ts
```

### 9. 제안 처리 흐름

1. `RunRequest` 수신
2. 입력 파일 존재 여부 검증
3. 파일 읽기
4. 합성 프롬프트 생성
5. tool adapter 선택
6. 실행 명령/인자 생성
7. cwd에서 CLI 실행
8. stdout/stderr 수집
9. final-json 기준으로 파싱 및 정규화
10. `RunArtifacts` 반환

### 10. 표준 프롬프트 합성 포맷 초안

```text
[Persona]
...
[/Persona]

[Task]
...
[/Task]

[Context File: path/to/file]
...
[/Context File]

[Extra Instructions]
Return valid JSON only.
[/Extra Instructions]
```

### 11. 도구별 adapter 계약

#### Codex adapter

역할:
- `codex exec` 기반 명령 생성
- JSONL 스트림과 최종 메시지 처리 기준 정의
- 모델 지정 옵션 매핑

예상 책임:
- `codex exec`
- `-C` cwd 적용
- `-m` 또는 동등한 model override 적용
- final-json 정규화를 위한 내부 출력 수집 방식 결정
- stdin 기반 prompt 전달

#### Gemini adapter

역할:
- `gemini` headless 실행 명령 생성
- output format 옵션 매핑
- 모델 지정 옵션 매핑

예상 책임:
- `-p` 또는 stdin 기반 입력 처리
- `-m` 또는 `--model` 적용
- `--output-format` 적용
- v1에서는 `include-directories` 공통화 없이 동작

### 12. final-json 정규화 정책

v1은 `final-json` 만 표준 지원한다.

별도 parser 계층은 두지 않고, runner 내부의 얇은 정규화 단계에서 아래만 수행한다.

- stdout에서 최종 JSON 블록 추출
- `JSON.parse` 수행
- 최소 schema 검증
- 공통 결과 객체로 감싸기

즉, 여기서 필요한 것은 범용 parser라기보다 *final-json 정규화 유틸*이다.

예상 반환 스키마:

```ts
interface FinalJsonResult {
  tool: ToolKind;
  success: boolean;
  response: unknown;
  rawText?: string;
  usage?: unknown;
}
```

`event-stream` 은 향후 디버깅/실시간 UI 요구가 생기면 별도 확장 스펙으로 추가한다.

### 13. 오류 처리 정책 초안

아래 오류를 구분한다.

- 입력 파일 없음
- CLI 바이너리 없음
- CLI 실행 실패
- 타임아웃
- stdout 파싱 실패
- 출력 형식 불일치

예상 오류 타입:

```ts
class InputFileError extends Error {}
class ToolNotFoundError extends Error {}
class ToolExecutionError extends Error {}
class OutputParseError extends Error {}
class TimeoutError extends Error {}
```

### 14. 병렬 실행 고려사항

병렬 실행 시 아래 전략을 기본 원칙으로 둔다.

- 각 실행은 별도 working directory 또는 worktree 사용
- runId 기준 임시 디렉터리 생성 가능
- stdout/stderr는 runId별 저장 가능
- 산출 파일 경로 충돌 방지

초기 구현은 단일 실행 API부터 시작하고, 이후 아래 형태로 확장 가능해야 한다.

```ts
async function runMany(requests: RunRequest[]): Promise<RunArtifacts[]>;
```

### 15. 확정 사항

이번 검토에서 아래처럼 결정한다.

- v1 구현 범위의 도구는 `codex`, `gemini` 로 한정한다.
- Claude Code는 비교 분석 결과만 유지하고, adapter 구현은 후속 버전으로 미룬다.
- 입력은 `persona/task/context files` 를 읽어 합성 프롬프트로 만든 뒤 stdin으로 전달한다.
- 출력 표준은 `final-json` 으로 고정한다.
- parser는 별도 모듈로 분리하지 않고, runner 내부의 얇은 final-json 정규화 유틸로 처리한다.
- 로그는 작업 단위(run/task) JSON 파일로 저장한다.
- 도구별 고급 옵션은 공통 인터페이스에 최소한만 노출하고, 예외 상황은 `extraArgs` 로 처리한다.
- `additionalDirectories` 는 v1 공통 인터페이스에 넣지 않는다.
- 이미지 입력은 v1 범위에서 제외한다.
- 세션 재개 기능은 v1 범위에서 제외한다.
- v1은 단일 실행 컨셉 증명에 집중하고, 병렬 실행은 후속 확장으로 둔다.
- 구현 언어는 TypeScript를 사용한다.
- 테스트는 fixture 기반 테스트와 실제 CLI 연동 테스트까지 포함한다.

### 16. 권장 구현 순서

1. 타입 정의
2. prompt-builder 구현
3. codex adapter 구현
4. gemini adapter 구현
5. 단일 실행 runner 구현
6. final-json 정규화 유틸 구현
7. fixture 기반 테스트 작성
8. 실제 CLI 연동 테스트 작성
9. 병렬 실행 확장 검토

### 17. 남은 검토 체크리스트

현재 기준으로 *v1 핵심 결정사항은 모두 확정*되었다.

후속 검토 항목만 남긴다.

- [ ] 실제 CLI 출력 샘플을 기준으로 final-json 정규화 규칙을 보정할지 검토
- [ ] 병렬 실행 확장 시 worktree 전략과 임시 디렉터리 전략 중 기본값 선택
- [ ] Claude adapter를 후속 버전에 어떤 조건에서 다시 포함할지 검토

### 18. 현재 권장 결론

현재 확정된 v1 방향은 아래와 같다.

- 공통 입력은 `파일 경로 집합`으로 받는다.
- 내부에서는 `합성 프롬프트`로 변환한다.
- 실행은 `tool adapter + cwd` 구조로 분리한다.
- v1 도구 범위는 `codex`, `gemini` 로 한정한다.
- 결과는 `final-json` 으로 정규화하고, 로그는 작업 단위 JSON 파일로 남긴다.
- final-json 처리는 별도 parser 계층이 아니라 runner 내부 정규화 유틸로 처리한다.
- 도구별 고급 옵션은 최소 노출 원칙을 유지하고, 필요 시 `extraArgs` 로 우회한다.
- `additionalDirectories`, 이미지 입력, 세션 재개는 v1 범위에서 제외한다.
- v1은 단일 실행 컨셉 증명과 실제 CLI 연동 테스트까지를 목표로 한다.
- 병렬성은 후속 단계에서 `독립 작업 디렉터리` 전략으로 확장한다.

이 spec은 현재까지 합의된 v1 구현 기준 문서다.
