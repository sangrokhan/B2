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

```ts
export type AiCodingTool = 'claude' | 'codex' | 'gemini';

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
  outputFormat: 'json' | 'stream-json';
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
