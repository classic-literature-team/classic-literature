import '@/styles/home.css'
import '@/styles/logs.css'

import { useNavigate } from 'react-router-dom'

import { type AgentLog, useAgentLogs } from '@/hooks/useAgentLogs'

/** ISO 문자열을 ko-KR 로케일의 읽기 좋은 날짜+시간으로 변환 */
function formatCreatedAt(iso: string): string {
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) return iso
  return date.toLocaleString('ko-KR', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function LogCard({ log }: { log: AgentLog }) {
  return (
    <article className="log-card">
      <h3 className="log-question">{log.question}</h3>
      <p className="log-answer">{log.answer}</p>
      <div className="log-meta">
        <time className="log-date" dateTime={log.created_at}>
          {formatCreatedAt(log.created_at)}
        </time>
        <span className="log-likes" aria-label={`좋아요 ${log.like_count}개`}>
          ♥ {log.like_count}
        </span>
      </div>
    </article>
  )
}

export function LogsPage() {
  const navigate = useNavigate()
  const { data, isLoading, isError } = useAgentLogs()

  return (
    <div className="home-root">
      <div className="logs-page">
        <button
          type="button"
          className="chat-back"
          onClick={() => navigate('/')}
        >
          ← 홈으로
        </button>

        <div className="logs-head">
          <h2>AI 대화 로그</h2>
          <p>이용자들이 AI에게 묻고 받은 대화 기록을 모아 보여드립니다.</p>
        </div>

        {isLoading && <div className="logs-state">불러오는 중…</div>}

        {isError && (
          <div className="logs-state logs-error">
            대화 로그를 불러오지 못했습니다. 잠시 후 다시 시도해주세요.
          </div>
        )}

        {!isLoading && !isError && data && data.length === 0 && (
          <div className="logs-state">아직 저장된 대화가 없습니다.</div>
        )}

        {!isLoading && !isError && data && data.length > 0 && (
          <div className="logs-grid">
            {data.map((log) => (
              <LogCard key={log.id} log={log} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
