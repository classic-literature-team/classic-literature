import { useMutation } from '@tanstack/react-query'
import { useState } from 'react'

import { ApiError, apiFetch } from '@/utils/api'

interface ChatResponse {
  reply: string
}

async function sendChat(message: string): Promise<string> {
  const data = await apiFetch<ChatResponse>('/chat', {
    method: 'POST',
    body: JSON.stringify({ message }),
  })
  return data.reply
}

/** LLM 대화 전송 mutation (비스트리밍). 백엔드 /api/chat 연동. */
export function useChat() {
  return useMutation({
    mutationFn: sendChat,
  })
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '/api'

/** 조회에 등장한 클래스(노드) 하나. */
export interface TraceClass {
  key: string
  node_class: string
  label: string
}

/** 등장한 관계명 하나(한국어 병기). */
export interface TraceRelation {
  name: string
  korean: string
}

/** 클래스별 레코드 미리보기 표 데이터. */
export interface TraceRecordGroup {
  key: string
  node_class: string
  label: string
  total: number
  shown: number
  columns: string[]
  rows: Record<string, string>[]
}

/** SSE `trace` 이벤트 본문이자 프론트 상태의 근거 객체. */
export interface AnswerTrace {
  path: string[]
  classes: TraceClass[]
  relations: TraceRelation[]
  evidence: string[]
  records: TraceRecordGroup[]
}

interface StreamCallbacks {
  /** 토큰 조각이 도착할 때마다 호출된다. */
  onDelta: (delta: string) => void
  /** 답변 근거(trace) 이벤트가 도착하면 호출된다. (선택) */
  onTrace?: (trace: AnswerTrace) => void
}

/**
 * SSE로 받은 값이 AnswerTrace 스키마(다섯 필드가 모두 배열)인지 최소 검증한다.
 * 스키마가 예상과 다르면 false를 반환해 해당 trace 이벤트를 무시한다(Req 5.2).
 */
function isAnswerTrace(value: unknown): value is AnswerTrace {
  if (typeof value !== 'object' || value === null) return false
  const t = value as Record<string, unknown>
  return (
    Array.isArray(t.path) &&
    Array.isArray(t.classes) &&
    Array.isArray(t.relations) &&
    Array.isArray(t.evidence) &&
    Array.isArray(t.records)
  )
}

/**
 * 백엔드 /api/chat/stream(SSE)에 붙어 답변을 조각 단위로 받는다.
 *
 * fetch 응답 본문을 ReadableStream으로 읽어 "data: {...}\n\n" 형태의
 * SSE 이벤트를 파싱한다. delta가 오면 onDelta로 넘기고, done이면 종료,
 * error가 오면 예외를 던진다.
 */
async function streamChat(
  message: string,
  { onDelta, onTrace }: StreamCallbacks,
  signal?: AbortSignal,
): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/chat/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message }),
    signal,
  })

  if (!response.ok || !response.body) {
    const text = await response.text().catch(() => '')
    throw new ApiError(response.status, text || response.statusText)
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  for (;;) {
    const { value, done } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })

    // SSE 이벤트는 빈 줄(\n\n)로 구분된다.
    let sep: number
    while ((sep = buffer.indexOf('\n\n')) !== -1) {
      const rawEvent = buffer.slice(0, sep)
      buffer = buffer.slice(sep + 2)

      const line = rawEvent
        .split('\n')
        .find((l) => l.startsWith('data:'))
      if (!line) continue

      const payload = JSON.parse(line.slice('data:'.length).trim()) as {
        delta?: string
        done?: boolean
        error?: string
        trace?: unknown
      }

      if (payload.error) throw new Error(payload.error)
      if (payload.done) return
      if (payload.delta) onDelta(payload.delta)

      // trace 이벤트는 답변 본문 처리와 독립적으로 다룬다. 스키마가 예상과
      // 다르면 무시하고, trace 처리 실패가 delta/done/error에 영향을 주지
      // 않도록 예외를 삼킨다(Req 5.2, 5.3).
      if (payload.trace !== undefined && onTrace) {
        try {
          if (isAnswerTrace(payload.trace)) onTrace(payload.trace)
        } catch {
          // trace 콜백 실패는 답변 스트림 처리에 영향을 주지 않는다.
        }
      }
    }
  }
}

interface UseChatStreamState {
  send: (message: string, callbacks: StreamCallbacks) => Promise<void>
  isStreaming: boolean
}

/** SSE 스트리밍 대화 훅. 토큰이 오는 대로 onDelta로 흘려준다. */
export function useChatStream(): UseChatStreamState {
  const [isStreaming, setIsStreaming] = useState(false)

  async function send(message: string, callbacks: StreamCallbacks) {
    setIsStreaming(true)
    try {
      await streamChat(message, callbacks)
    } finally {
      setIsStreaming(false)
    }
  }

  return { send, isStreaming }
}
