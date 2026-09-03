import '@/styles/home.css'
import '@/styles/chat.css'

import { useNavigate } from 'react-router-dom'

export function KeywordSearchPage() {
  const navigate = useNavigate()

  return (
    <div className="home-root">
      <div className="placeholder-page">
        <h2>키워드 검색</h2>
        <p>키워드 검색 기능은 준비 중입니다.</p>
        <button
          type="button"
          className="placeholder-back"
          onClick={() => navigate('/')}
        >
          ← 홈으로
        </button>
      </div>
    </div>
  )
}
