import { useState } from 'react'

import { yangsQAs } from '@/data/yangs'

function YangsCard({ qa }: { qa: (typeof yangsQAs)[number] }) {
  const [open, setOpen] = useState(false)

  return (
    <div className="yangs-card">
      <div className="yangs-card-q">
        <span className="yangs-num">{qa.num}</span>
        <span>{qa.question}</span>
      </div>
      <div className="yangs-card-a">
        <div className="yangs-card-avatar">楊</div>
        <div className="yangs-card-body">
          <p>{qa.answer}</p>
          <div className="yangs-scenes">
            <button
              type="button"
              className={`yangs-scene-toggle${open ? ' open' : ''}`}
              aria-expanded={open}
              onClick={() => setOpen((v) => !v)}
            >
              {open ? '📖 관련 장면 닫기' : '📖 관련 장면 보기'}
            </button>
            {open && (
              <div className="yangs-scene-list" style={{ display: 'flex' }}>
                {qa.scenes.map((s) => (
                  <button
                    key={s.label}
                    type="button"
                    className="yangs-scene-chip"
                  >
                    {s.label}
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

/** 양소유의 연애상담소 탭 패널 */
export function YangsPanel() {
  return (
    <>
      <div className="section-head">
        <h2>양소유의 연애상담소</h2>
        <span className="eng">Love Counseling</span>
      </div>
      <div className="counselor-intro">
        <div className="counselor-badge">楊</div>
        <div className="counselor-text">
          <strong>상담사: 양소유</strong>
          <p className="counselor-desc">
            여덟 선녀와의 인연을 모두 성취한 천하제일 풍류남아.
          </p>
        </div>
        <button type="button" className="counselor-chat-link">
          양소유와 더 대화하러 가기 →
        </button>
      </div>

      <div className="yangs-cards">
        {yangsQAs.map((qa) => (
          <YangsCard key={qa.num} qa={qa} />
        ))}
      </div>
    </>
  )
}
