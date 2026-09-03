import { useState } from 'react'

import {
  genres,
  type WorkChip,
  worksEarly,
  worksMid,
} from '@/data/home-content'

function Chips({ works, variant }: { works: WorkChip[]; variant: string }) {
  return (
    <div className={`work-chips chips-${variant}`}>
      {works.map((w) =>
        w.unavailable ? (
          <span key={w.ko} className="work-chip work-chip--unavailable">
            {w.ko}
            <span>{w.hanja}</span>
          </span>
        ) : (
          <button key={w.ko} type="button" className="work-chip">
            {w.ko}
            <span>{w.hanja}</span>
          </button>
        ),
      )}
    </div>
  )
}

/** 지식그래프 탭 패널 */
export function GraphPanel() {
  return (
    <>
      <div className="section-head">
        <h2>작품별 지식그래프</h2>
        <span className="eng">Knowledge Graph</span>
      </div>
      <p className="section-desc">
        지식그래프 생성이 완료된 작품들만 제공합니다.
      </p>

      <h3 className="graph-period period-early">나말여초~조선 전기</h3>
      <Chips works={worksEarly} variant="early" />

      <h3 className="graph-period period-mid">조선중기 이후</h3>
      <Chips works={worksMid} variant="mid" />

      <p className="section-note">※ 완료된 작품들을 우선적으로 탑재</p>
    </>
  )
}

/** 장르별 목록 탭 패널 (아코디언) */
export function GenrePanel() {
  const [openGenre, setOpenGenre] = useState<string | null>(null)

  return (
    <>
      <div className="section-head">
        <h2>장르별 목록</h2>
        <span className="eng">Genre List</span>
      </div>
      <p className="section-desc">
        한국한문소설의 장르 분류 체계. 장르를 클릭하면 해당 작품 목록이
        펼쳐집니다.
      </p>
      <div className="genre-accordion">
        {genres.map((g) => {
          const open = openGenre === g.ko
          return (
            <div key={g.ko} className={`genre-row${open ? ' open' : ''}`}>
              <button
                type="button"
                className="genre-header"
                style={{ width: '100%', background: 'none', border: 'none' }}
                aria-expanded={open}
                onClick={() => setOpenGenre(open ? null : g.ko)}
              >
                <span className="genre-bar" style={{ background: g.color }} />
                <span className="genre-name">
                  {g.ko}
                  <span className="genre-chi">{g.hanja}</span>
                </span>
                <span className="genre-arrow">▸</span>
              </button>
              <div className="genre-body">
                <p className="genre-placeholder">작품 데이터 준비 중</p>
              </div>
            </div>
          )
        })}
      </div>
    </>
  )
}
