import { renderHook } from '@testing-library/react'
import fc from 'fast-check'
import { afterEach, describe, expect, it, vi } from 'vitest'

import type { AnswerTrace } from './useChat'
import { useChatStream } from './useChat'

/**
 * SSE 파서 테스트 (작업 6.2 / 6.3, Req 5.1~5.4, Property 11).
 *
 * useChat.ts의 streamChat/파서 로직은 export되어 있지 않고 fetch에 의존하므로,
 * global.fetch를 목으로 대체해 ReadableStream(SSE 바이트)을 반환하는 방식으로만
 * 접근한다. (useChat.ts는 수정하지 않는다.)
 */

// ---------------------------------------------------------------------------
// 테스트 헬퍼: SSE 프레임을 만들고 ReadableStream을 반환하는 목 fetch 구성
// ---------------------------------------------------------------------------

type SseEvent =
  | { delta: string }
  | { done: true }
  | { error: string }
  | { trace: unknown }

/** 하나의 이벤트를 "data: {json}\n\n" 프레임 문자열로 만든다. */
function frame(event: SseEvent): string {
  return `data: ${JSON.stringify(event)}\n\n`
}

/**
 * SSE 이벤트 목록을 바이트로 인코딩해 ReadableStream으로 흘리는 목 fetch를
 * global.fetch에 설치한다. chunkSize로 프레임 경계를 넘나드는 청크 분할도
 * 시뮬레이션할 수 있다(파서의 버퍼링 견고성 확인).
 */
function installFetchMock(events: SseEvent[], opts: { chunkSize?: number } = {}) {
  const encoder = new TextEncoder()
  const bytes = encoder.encode(events.map(frame).join(''))
  const chunkSize = opts.chunkSize ?? bytes.length

  const body = new ReadableStream<Uint8Array>({
    start(controller) {
      for (let offset = 0; offset < bytes.length; offset += chunkSize) {
        controller.enqueue(bytes.slice(offset, offset + chunkSize))
      }
      // 이벤트가 하나도 없어도(빈 스트림) 정상적으로 닫는다.
      controller.close()
    },
  })

  const response = {
    ok: true,
    status: 200,
    statusText: 'OK',
    body,
    text: async () => '',
  } as unknown as Response

  const fetchMock = vi.fn(async () => response)
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

/** useChatStream().send를 목 스트림에 대해 실행하고 관측 결과를 수집한다. */
async function runStream(events: SseEvent[], opts: { chunkSize?: number } = {}) {
  installFetchMock(events, opts)

  const deltas: string[] = []
  const traces: AnswerTrace[] = []
  // useChatStream은 useState를 쓰는 React 훅이므로 컴포넌트 컨텍스트 안에서
  // 획득해야 한다. renderHook으로 send 함수를 꺼내 파서 로직만 실행한다.
  const { result } = renderHook(() => useChatStream())
  const { send } = result.current

  let error: unknown = null
  try {
    await send('질문', {
      onDelta: (d) => deltas.push(d),
      onTrace: (t) => traces.push(t),
    })
  } catch (err) {
    error = err
  }

  return { deltas, traces, error, joined: deltas.join('') }
}

/** 스키마에 맞는 최소 유효 AnswerTrace 객체. */
const validTrace: AnswerTrace = {
  path: ['작품', '이본'],
  classes: [{ key: 'book', node_class: 'Book', label: '이본' }],
  relations: [{ name: 'spreadsInto', korean: '이본으로 확산된다' }],
  evidence: ['이본(Book) 142건 중 30건 확인'],
  records: [
    {
      key: 'book',
      node_class: 'Book',
      label: '이본',
      total: 142,
      shown: 1,
      columns: ['id', 'title_name_kor'],
      rows: [{ id: 'book_001', title_name_kor: '구운몽' }],
    },
  ],
}

afterEach(() => {
  vi.unstubAllGlobals()
  vi.restoreAllMocks()
})

// ---------------------------------------------------------------------------
// 작업 6.3: 파서 단위 테스트 (Req 5.1, 5.2, 5.4)
// ---------------------------------------------------------------------------

describe('useChatStream SSE 파서 단위 테스트 (6.3)', () => {
  it('trace 이벤트를 올바른 AnswerTrace 객체로 onTrace 호출한다 (Req 5.1)', async () => {
    const { traces, error } = await runStream([
      { delta: '안녕' },
      { trace: validTrace },
      { done: true },
    ])

    expect(error).toBeNull()
    expect(traces).toHaveLength(1)
    expect(traces[0]).toEqual(validTrace)
  })

  it('스키마 불일치 trace(필드 누락)면 onTrace를 호출하지 않는다 (Req 5.2)', async () => {
    const { traces, error } = await runStream([
      { delta: '안녕' },
      { trace: { path: 'x' } }, // 배열이어야 할 필드가 문자열 + 나머지 누락
      { done: true },
    ])

    expect(error).toBeNull()
    expect(traces).toHaveLength(0)
  })

  it('일부 필드만 있는 trace도 스키마 불일치로 무시한다 (Req 5.2)', async () => {
    const { traces } = await runStream([
      { trace: { path: [], classes: [], relations: [], evidence: [] } }, // records 누락
      { done: true },
    ])

    expect(traces).toHaveLength(0)
  })

  it('delta들을 순서대로 누적하고 done에서 정상 종료한다 (Req 5.4)', async () => {
    const { deltas, joined, error } = await runStream([
      { delta: '한국' },
      { delta: '고전' },
      { delta: '소설' },
      { done: true },
    ])

    expect(error).toBeNull()
    expect(deltas).toEqual(['한국', '고전', '소설'])
    expect(joined).toBe('한국고전소설')
  })

  it('error 이벤트면 send가 reject한다 (Req 5.4)', async () => {
    const { error, joined } = await runStream([
      { delta: '부분 답변' },
      { error: '에이전트 실행 오류' },
    ])

    expect(error).toBeInstanceOf(Error)
    expect((error as Error).message).toBe('에이전트 실행 오류')
    // error 이전의 delta는 정상 누적된다.
    expect(joined).toBe('부분 답변')
  })

  it('프레임 경계를 가로지르는 청크 분할에도 delta/trace를 정확히 파싱한다 (Req 5.4)', async () => {
    const { deltas, traces, joined, error } = await runStream(
      [{ delta: '조각1' }, { trace: validTrace }, { delta: '조각2' }, { done: true }],
      { chunkSize: 3 },
    )

    expect(error).toBeNull()
    expect(joined).toBe('조각1조각2')
    expect(deltas).toEqual(['조각1', '조각2'])
    expect(traces).toEqual([validTrace])
  })
})

// ---------------------------------------------------------------------------
// 작업 6.2: 파서 견고성 property 테스트 (Property 11, Req 5.3)
// ---------------------------------------------------------------------------

describe('useChatStream 파서 견고성 property 테스트 (6.2)', () => {
  // Feature: answer-trace-panel, Property 11
  it('trace 이벤트를 섞어도 최종 답변 텍스트·종료 방식이 trace 없을 때와 동일하다', async () => {
    // 스키마가 어긋난 trace 페이로드 후보들(파서가 무시해야 함).
    const invalidTraceArb = fc.oneof(
      fc.constant({ path: 'not-array' }),
      fc.constant({ path: [], classes: [], relations: [], evidence: [] }), // records 누락
      fc.constant({ foo: 'bar' }),
      fc.constant(null),
      fc.constant(42),
      fc.record({ path: fc.array(fc.string()) }), // 일부 필드만
    )

    await fc.assert(
      fc.asyncProperty(
        // 임의의 delta 문자열 시퀀스
        fc.array(fc.string(), { maxLength: 12 }),
        // 스트림을 error로 끝낼지 여부와 error 메시지
        fc.option(fc.string(), { nil: null }),
        // trace 이벤트를 어디에 얼마나 끼워 넣을지 결정하는 시드들
        fc.array(fc.boolean(), { maxLength: 12 }),
        async (rawDeltas, errorMsg, traceFlags) => {
          // JSON.stringify가 깨지지 않도록 delta에 빈 문자열은 제외하지 않되,
          // 파서는 falsy delta('')를 onDelta로 넘기지 않으므로 기준 계산도 동일 규칙 적용.
          const deltas = rawDeltas

          // "trace 없는" 기준 스트림
          const baseEvents: SseEvent[] = deltas.map((d) => ({ delta: d }))

          // "trace 섞은" 스트림: 각 delta 앞뒤로 유효/무효 trace를 섞는다.
          const mixedEvents: SseEvent[] = []
          for (let i = 0; i < deltas.length; i++) {
            if (traceFlags[i]) {
              // 유효/무효 trace를 번갈아 삽입
              mixedEvents.push(
                i % 2 === 0
                  ? { trace: validTrace }
                  : { trace: await sampleInvalid(invalidTraceArb) },
              )
            }
            mixedEvents.push({ delta: deltas[i] })
          }
          // 맨 끝에도 하나 더 섞어본다.
          mixedEvents.push({ trace: validTrace })

          // 종료 이벤트(done 또는 error)를 양쪽에 동일하게 붙인다.
          const terminator: SseEvent =
            errorMsg === null ? { done: true } : { error: errorMsg }
          baseEvents.push(terminator)
          mixedEvents.push(terminator)

          const base = await runStream(baseEvents)
          const mixed = await runStream(mixedEvents)

          // 핵심 불변식: trace를 섞은 스트림의 최종 답변 텍스트와 종료 결과가
          // trace 없는 기준 스트림과 동일해야 한다(Property 11). 실제 파서 동작을
          // 기준(base)으로 삼아 비교하므로, 파서의 세부 규칙(예: falsy error 처리)에
          // 의존하지 않고 "trace 무관성"만 검증한다.
          expect(mixed.joined).toBe(base.joined)
          expect(mixed.deltas).toEqual(base.deltas)

          // 종료 방식(정상 종료 여부·에러 메시지)이 base와 mixed에서 동일해야 한다.
          if (base.error === null) {
            expect(mixed.error).toBeNull()
          } else {
            expect(mixed.error).toBeInstanceOf(Error)
            expect((mixed.error as Error).message).toBe((base.error as Error).message)
          }
        },
      ),
      { numRuns: 100 },
    )
  })
})

/** fast-check arbitrary에서 값 하나를 동기적으로 뽑는다(무효 trace 후보 선택용). */
async function sampleInvalid(arb: fc.Arbitrary<unknown>): Promise<unknown> {
  return fc.sample(arb, 1)[0]
}
