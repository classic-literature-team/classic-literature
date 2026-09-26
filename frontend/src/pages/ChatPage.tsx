import '@/styles/home.css'
import '@/styles/chat.css'

import { useEffect, useMemo, useRef, useState } from 'react'
import Markdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

import yangsoyuAvatar from '@/assets/images/yangsoyu.png'
import { AnswerTracePanel } from '@/components/chat/AnswerTracePanel'
import {
  type CategoryId,
  exampleQuestions,
  greetingSourceNote,
  guideCategories,
  personaGreeting,
} from '@/data/chat-guide'
import { type AnswerTrace,useChatStream } from '@/hooks/useChat'
import { ApiError } from '@/utils/api'

interface Message {
  role: 'user' | 'assistant'
  content: string
  /** 인사말 등 어시스턴트 메시지 하단 부가 안내 */
  source?: string
  /** 답변 생성 근거(탐색 경로/노드/관계/레코드). 있을 때만 근거 패널 렌더 */
  trace?: AnswerTrace
}

/** 카테고리별 SVG 아이콘 (시안 ai-chat-2 그대로) */
const CATEGORY_ICONS: Record<CategoryId, React.ReactNode> = {
  bibliographic: (
    <path
      d="M4 5.5c3.2-.8 5.8-.2 8 1.6v12c-2.2-1.8-4.8-2.4-8-1.6v-12ZM20 5.5c-3.2-.8-5.8-.2-8 1.6v12c2.2-1.8 4.8-2.4 8-1.6v-12Z"
      strokeWidth={1.8}
      strokeLinejoin="round"
    />
  ),
  participatory: (
    <>
      <path
        d="M5 6h9a3 3 0 0 1 3 3v3a3 3 0 0 1-3 3H9l-4 3v-3a3 3 0 0 1-3-3V9a3 3 0 0 1 3-3Z"
        strokeWidth={1.8}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M17 9h2a3 3 0 0 1 3 3v2a3 3 0 0 1-3 3v2l-3-2"
        strokeWidth={1.8}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </>
  ),
  arrangement: (
    <>
      <circle cx={6} cy={6} r={2.4} strokeWidth={1.8} />
      <circle cx={18} cy={7} r={2.4} strokeWidth={1.8} />
      <circle cx={12} cy={18} r={2.4} strokeWidth={1.8} />
      <path
        d="m8.2 7 7.5-.1M7.4 8l3.5 7.8M16.6 9l-3.4 6.8"
        strokeWidth={1.8}
        strokeLinecap="round"
      />
    </>
  ),
  expressive: (
    <>
      <path
        d="m5 17 8.8-8.8 3 3L8 20H5v-3Z"
        strokeWidth={1.8}
        strokeLinejoin="round"
      />
      <path
        d="m15.2 6.8 1.5-1.5a1.7 1.7 0 0 1 2.4 0 1.7 1.7 0 0 1 0 2.4l-1.5 1.5"
        strokeWidth={1.8}
        strokeLinecap="round"
      />
    </>
  ),
}

const GREETING_MESSAGE: Message = {
  role: 'assistant',
  content: personaGreeting,
  source: greetingSourceNote,
}

export function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([GREETING_MESSAGE])
  const [input, setInput] = useState('')
  const [errorMsg, setErrorMsg] = useState<string | null>(null)
  const [activeCategory, setActiveCategory] =
    useState<CategoryId>('bibliographic')
  const [activeNode, setActiveNode] = useState<string | null>(null)

  const chat = useChatStream()
  const windowRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    windowRef.current?.scrollTo({
      top: windowRef.current.scrollHeight,
      behavior: 'smooth',
    })
  }, [messages, chat.isStreaming])

  const currentCategory = useMemo(
    () => guideCategories.find((c) => c.id === activeCategory)!,
    [activeCategory],
  )
  const currentNode = useMemo(
    () => currentCategory.nodes.find((n) => n.label === activeNode) ?? null,
    [currentCategory, activeNode],
  )

  function resizeInput() {
    const el = inputRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = `${Math.min(el.scrollHeight, 130)}px`
  }

  async function submit(text: string) {
    const trimmed = text.trim()
    if (!trimmed || chat.isStreaming) return

    setErrorMsg(null)
    setMessages((prev) => [
      ...prev,
      { role: 'user', content: trimmed },
      { role: 'assistant', content: '' },
    ])
    setInput('')
    requestAnimationFrame(resizeInput)

    try {
      await chat.send(trimmed, {
        onDelta: (delta) => {
          setMessages((prev) => {
            const next = [...prev]
            const last = next[next.length - 1]
            if (last && last.role === 'assistant') {
              next[next.length - 1] = { ...last, content: last.content + delta }
            }
            return next
          })
        },
        // Req 6.1: trace는 delta 누적이 끝난 뒤(스트림 종료 직전) 도착하므로
        // 마지막 assistant 메시지에 근거 객체를 병합한다.
        onTrace: (trace) => {
          setMessages((prev) => {
            const next = [...prev]
            const last = next[next.length - 1]
            if (last && last.role === 'assistant') {
              next[next.length - 1] = { ...last, trace }
            }
            return next
          })
        },
      })
    } catch (err) {
      setMessages((prev) => {
        const next = [...prev]
        const last = next[next.length - 1]
        if (last && last.role === 'assistant' && last.content === '') next.pop()
        return next
      })
      if (err instanceof ApiError && err.status === 503) {
        setErrorMsg(
          'AI 응답 기능이 아직 설정되지 않았습니다. (서버에 OPENAI_API_KEY 필요)',
        )
      } else {
        const msg = err instanceof Error ? err.message : '알 수 없는 오류'
        setErrorMsg(`요청 중 오류가 발생했습니다: ${msg}`)
      }
    }
  }

  function newChat() {
    setMessages([GREETING_MESSAGE])
    setInput('')
    setErrorMsg(null)
    requestAnimationFrame(resizeInput)
    inputRef.current?.focus()
  }

  function selectCategory(id: CategoryId) {
    setActiveCategory(id)
    setActiveNode(null)
  }

  const waitingFirstToken =
    chat.isStreaming &&
    messages.length > 0 &&
    messages[messages.length - 1].role === 'assistant' &&
    messages[messages.length - 1].content === ''

  return (
    <div className="home-root">
      <main className="chat-workspace">
        {/* ── 좌: 대화 영역 ── */}
        <section className="chat-area" aria-labelledby="chat-title">
          <div className="chat-header">
            <div className="chat-title">
              <h1 id="chat-title">데이터로 묻고 답하는 한국고전소설</h1>
              <p>
                본 답변은 현재 구축된 데이터 모델을 바탕으로 탐색 경로를
                구성하여 제공합니다. 데이터 생성-점검이 완료된 자료에 한하여
                답변이 제한될 수 있는 점 양해 부탁드립니다.
              </p>
            </div>
            <button className="new-chat" type="button" onClick={newChat}>
              새 대화
            </button>
          </div>

          <div className="messages" ref={windowRef} role="log" aria-live="polite">
            {messages.map((m, i) => {
              if (
                m.role === 'assistant' &&
                m.content === '' &&
                i === messages.length - 1
              ) {
                return null
              }
              return (
                <div key={i} className={`message ${m.role}`}>
                  {m.role === 'assistant' && (
                    <span className="assistant-id">
                      <img
                        className="assistant-avatar"
                        src={yangsoyuAvatar}
                        alt=""
                      />
                      <span className="assistant-name">양소유</span>
                    </span>
                  )}
                  <div className="bubble">
                    {m.role === 'assistant' ? (
                      <Markdown remarkPlugins={[remarkGfm]}>
                        {m.content}
                      </Markdown>
                    ) : (
                      m.content
                    )}
                    {m.source && (
                      <div className="source-note">{m.source}</div>
                    )}
                    {/* Req 6.2: trace가 있을 때만 근거 패널 렌더(빈 trace는 컴포넌트가 자체 미렌더) */}
                    {m.role === 'assistant' && m.trace && (
                      <AnswerTracePanel trace={m.trace} />
                    )}
                  </div>
                </div>
              )
            })}

            {waitingFirstToken && (
              <div className="message assistant">
                <span className="assistant-id">
                  <img
                    className="assistant-avatar"
                    src={yangsoyuAvatar}
                    alt=""
                  />
                  <span className="assistant-name">양소유</span>
                </span>
                <div className="bubble">
                  <span className="typing" aria-label="답변 작성 중">
                    <span />
                    <span />
                    <span />
                  </span>
                </div>
              </div>
            )}

            {errorMsg && <div className="chat-error">{errorMsg}</div>}
          </div>

          <div className="composer-zone">
            <form
              className="composer"
              onSubmit={(e) => {
                e.preventDefault()
                submit(input)
              }}
            >
              <textarea
                ref={inputRef}
                rows={1}
                aria-label="AI 질문 입력"
                placeholder="본 데이터 모델의 개체와 관계에 기반해 질문하시면 더 정확한 답변을 받을 수 있습니다."
                value={input}
                onChange={(e) => {
                  setInput(e.target.value)
                  resizeInput()
                }}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault()
                    submit(input)
                  }
                }}
              />
              <button
                className="send"
                type="submit"
                aria-label="질문 보내기"
                title="질문 보내기"
                disabled={chat.isStreaming || !input.trim()}
              >
                <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
                  <path
                    d="M12 19V5M6.5 10.5 12 5l5.5 5.5"
                    strokeWidth={2.2}
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
              </button>
            </form>
            <div className="composer-meta">
              <span>Enter 전송 · Shift+Enter 줄바꿈</span>
            </div>
          </div>
        </section>

        {/* ── 우: 안내 패널 ── */}
        <aside className="guide-panel" aria-labelledby="guide-title">
          <p className="guide-kicker">Ask the database</p>
          <h2 id="guide-title">
            데이터 모델에 기반해
            <br />
            다양한 질문을 던져보세요
          </h2>
          <p className="guide-copy">
            단순한 키워드 검색을 넘어 작품을 구성하는 개체와 그 사이의 관계를
            따라 자료를 탐색합니다.
          </p>

          <div
            className="category-tabs"
            role="tablist"
            aria-label="데이터 요소 분류"
          >
            {guideCategories.map((c) => (
              <button
                key={c.id}
                className={`category-tab${activeCategory === c.id ? ' active' : ''}`}
                type="button"
                role="tab"
                aria-selected={activeCategory === c.id}
                data-category={c.id}
                onClick={() => selectCategory(c.id)}
              >
                <span className="category-icon" aria-hidden="true">
                  <svg viewBox="0 0 24 24" fill="none">
                    {CATEGORY_ICONS[c.id]}
                  </svg>
                </span>
                {c.label}
              </button>
            ))}
          </div>

          <div className="node-buttons">
            {currentCategory.nodes.map((n) => (
              <button
                key={n.label}
                className={`node-button${activeNode === n.label ? ' active' : ''}`}
                type="button"
                onClick={() => setActiveNode(n.label)}
              >
                {n.label}
              </button>
            ))}
          </div>

          <div
            className="node-description"
            data-category={activeCategory}
            aria-live="polite"
          >
            {currentNode ? (
              <>
                <strong>{currentNode.label}</strong>
                <p>{currentNode.description}</p>
              </>
            ) : (
              <p className="node-description-hint">
                노드를 선택하면 설명이 표시됩니다.
              </p>
            )}
          </div>

          <div className="example-head">
            <strong>예시 질문</strong>
            <span>선택하여 입력</span>
          </div>
          <div className="examples">
            {exampleQuestions.map((q) => (
              <button
                key={q}
                className="example"
                type="button"
                onClick={() => {
                  setInput(q)
                  requestAnimationFrame(resizeInput)
                  inputRef.current?.focus()
                }}
              >
                <span className="example-text">{q}</span>
              </button>
            ))}
          </div>
        </aside>
      </main>
    </div>
  )
}
