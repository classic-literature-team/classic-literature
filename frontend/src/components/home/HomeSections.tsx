import { useNavigate } from 'react-router-dom'

import { linkTabs, notices, type TabId, tabs } from '@/data/home-content'

/** Hero 헤더 (로그인 링크는 방침상 제외) */
export function Hero() {
  return (
    <header className="hero">
      <div className="util-nav">
        <button type="button" className="util-link">
          오류신고
        </button>
        <button type="button" className="util-link">
          Q&amp;A
        </button>
        <button type="button" className="util-link">
          Language
        </button>
      </div>
      <h1 className="hero-title">
        한국고전소설<span className="accent">DB</span>
      </h1>
      <p className="hero-sub">
        한국고전소설의 작품과 관련 문헌에 담긴 모든 지식을 연결합니다.
      </p>
      <p className="hero-sub-small">
        Korean novels in literary sinitic Database
      </p>
      <div className="hero-line" />
    </header>
  )
}

/** 탭 네비게이션. 패널 탭은 콘텐츠 전환, 링크 탭(AI 질문/키워드 검색)은 페이지 이동 */
export function MainNav({
  active,
  onSelect,
}: {
  active: TabId
  onSelect: (id: TabId) => void
}) {
  const navigate = useNavigate()

  return (
    <nav className="main-nav">
      <div className="nav-inner">
        {tabs.map((t) => (
          <button
            key={t.id}
            type="button"
            className={`nav-link${active === t.id ? ' active' : ''}`}
            aria-current={active === t.id ? 'page' : undefined}
            onClick={() => onSelect(t.id)}
          >
            {t.icon}{' '}
            {t.yangs ? <span className="nav-yangs">{t.label}</span> : t.label}
          </button>
        ))}

        {linkTabs.map((t) => (
          <button
            key={t.to}
            type="button"
            className={`nav-link nav-link--${t.variant}`}
            onClick={() => navigate(t.to)}
          >
            {t.icon} {t.label}
          </button>
        ))}
      </div>
    </nav>
  )
}

/** 통계 스트립 */
export function StatsStrip() {
  return (
    <section className="stats-strip">
      <div className="stat-cell">
        <div className="num">
          18,000<span className="unit">건</span>
        </div>
        <div className="label">노드(Node)</div>
      </div>
      <div className="stat-cell">
        <div className="num">
          57,000<span className="unit">건</span>
        </div>
        <div className="label">관계(Edge)</div>
      </div>
      <div className="stat-cell">
        <div className="num">
          20/42<span className="unit">건</span>
        </div>
        <div className="label">클래스(Class)/관계유형(Relation)</div>
      </div>
      <div className="stat-cell">
        <div className="num">
          1,500/400<span className="unit">건</span>
        </div>
        <div className="label">이본/작품 수</div>
      </div>
    </section>
  )
}

/** 우측 사이드바 (공지사항) */
export function Sidebar() {
  return (
    <aside className="sidebar-right">
      <div className="sidebar-widget">
        <div className="widget-header">공지사항</div>
        <div className="widget-body">
          <ul className="notice-list">
            {notices.map((n) => (
              <li key={n.text}>
                {n.text}
                <span className="date">{n.date}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </aside>
  )
}
