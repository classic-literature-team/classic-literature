import '@/styles/home.css'
import '@/styles/chat.css'

import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { useChat } from '@/hooks/useChat'
import { ApiError } from '@/utils/api'

interface Message {
  role: 'user' | 'assistant'
  content: string
}

const EXAMPLES = [
  '「운영전」에 대한 당시 사람들의 반응들을 알려줘',
  '남성 등장인물이 여성으로 변장하는 작품들을 알려줘',
  '구운몽의 주요 등장인물을 설명해줘',
]

export function ChatPage() {
  const navigate = useNavigate()
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [errorMsg, setErrorMsg] = useState<string | null>(null)
  const chat = useChat()
  const windowRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    windowRef.current?.scrollTo({
      top: windowRef.current.scrollHeight,
      behavior: 'smooth',
    })
  }, [messages, chat.isPending])

  function submit(text: string) {
    const trimmed = text.trim()
    if (!trimmed || chat.isPending) return

    setErrorMsg(null)
    setMessages((prev) => [...prev, { role: 'user', content: trimmed }])
    setInput('')

    chat.mutate(trimmed, {
      onSuccess: (reply) => {
        setMessages((prev) => [...prev, { role: 'assistant', content: reply }])
      },
      onError: (err) => {
        if (err instanceof ApiError && err.status === 503) {
          setErrorMsg(
            'AI 응답 기능이 아직 설정되지 않았습니다. (서버에 OPENAI_API_KEY 필요)',
          )
        } else {
          const msg = err instanceof Error ? err.message : '알 수 없는 오류'
          setErrorMsg(`요청 중 오류가 발생했습니다: ${msg}`)
        }
      },
    })
  }

  return (
    <div className="home-root">
      <div className="chat-page">
        <button
          type="button"
          className="chat-back"
          onClick={() => navigate('/')}
        >
          ← 홈으로
        </button>

        <div className="chat-head">
          <h2>AI 질문</h2>
          <p>고전소설에 대해 자유롭게 대화하세요.</p>
        </div>

        <div className="chat-window" ref={windowRef}>
          {messages.length === 0 && !chat.isPending && (
            <div className="chat-empty">
              무엇이든 물어보세요.
              <div className="examples">
                {EXAMPLES.map((ex) => (
                  <button
                    key={ex}
                    type="button"
                    className="chat-example"
                    onClick={() => submit(ex)}
                  >
                    {ex}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((m, i) => (
            <div key={i} className={`chat-msg ${m.role}`}>
              <div className="chat-avatar">
                {m.role === 'user' ? '나' : '楊'}
              </div>
              <div className="chat-bubble">{m.content}</div>
            </div>
          ))}

          {chat.isPending && (
            <div className="chat-typing">답변을 생각하는 중…</div>
          )}

          {errorMsg && <div className="chat-error">{errorMsg}</div>}
        </div>

        <form
          className="chat-form"
          onSubmit={(e) => {
            e.preventDefault()
            submit(input)
          }}
        >
          <input
            className="chat-input"
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="고전소설에 대해 자유롭게 대화하세요"
            aria-label="질문 입력"
          />
          <button
            className="chat-send"
            type="submit"
            disabled={chat.isPending || !input.trim()}
          >
            질문
          </button>
        </form>
      </div>
    </div>
  )
}
