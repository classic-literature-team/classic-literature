import { useId, useState } from 'react'

import type { AnswerTrace } from '@/hooks/useChat'

interface AnswerTracePanelProps {
  trace: AnswerTrace
}

/** trace가 실질적으로 비어 있는지(다섯 배열이 전부 비었는지) 판단한다. */
function isEmptyTrace(trace: AnswerTrace): boolean {
  return (
    trace.path.length === 0 &&
    trace.classes.length === 0 &&
    trace.relations.length === 0 &&
    trace.evidence.length === 0 &&
    trace.records.length === 0
  )
}

/**
 * 어시스턴트 답변 아래에 "왜 이런 답이 나왔지?" 토글과 근거 패널을 렌더한다.
 * trace가 없거나 내용이 비어 있으면 아무것도 렌더하지 않는다(Req 6.2).
 * 시안 answer-audit 디자인을 따르되 Cypher 항목은 제외한다(Req 7.4).
 */
export function AnswerTracePanel({ trace }: AnswerTracePanelProps) {
  const [open, setOpen] = useState(false)
  const [activeTab, setActiveTab] = useState(0)
  const panelId = useId()

  // Req 6.2: 근거가 없으면 버튼/패널을 렌더하지 않는다.
  if (!trace || isEmptyTrace(trace)) return null

  const { path, classes, relations, evidence, records } = trace
  const activeGroup = records[Math.min(activeTab, records.length - 1)]

  return (
    <div className="answer-actions">
      {/* Req 7.1, 9.1, 9.2: 토글 버튼(시맨틱 button + aria-expanded/controls) */}
      <button
        type="button"
        className="why-button"
        aria-expanded={open}
        aria-controls={panelId}
        onClick={() => setOpen((prev) => !prev)}
      >
        왜 이런 답이 나왔지?
        <span className="why-chevron" aria-hidden="true">
          ▾
        </span>
      </button>

      {/* Req 7.2: 토글 상태에 따라 펼쳐지는 패널 */}
      <div id={panelId} className={`answer-audit${open ? ' open' : ''}`}>
        <div className="audit-overflow">
          <div className="audit-panel">
            {/* 패널 헤더 (Cypher 항목 없음) */}
            <div className="audit-head">
              <div>
                <p className="audit-kicker">Answer trace</p>
                <h4>답변 생성 경로</h4>
              </div>
            </div>

            {/* 1. 탐색 경로 (Req 7.3) */}
            {path.length > 0 && (
              <div className="trace-paths">
                <div className="trace-path">
                  {path.map((step, i) => (
                    <span className="trace-step" key={`${step}-${i}`}>
                      {step}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* 2. 조회한 노드 — label + node_class 병기 (Req 7.5) */}
            {classes.length > 0 && (
              <div className="audit-chips">
                {classes.map((cls) => (
                  <span className="audit-chip" key={cls.key}>
                    {cls.label}
                    <small>{cls.node_class}</small>
                  </span>
                ))}
              </div>
            )}

            {/* 3. 연결 관계 — 원문 name + korean 병기 (Req 7.6) */}
            {relations.length > 0 && (
              <div className="audit-chips">
                {relations.map((rel) => (
                  <span className="audit-chip" key={rel.name}>
                    {rel.name}
                    <small>{rel.korean}</small>
                  </span>
                ))}
              </div>
            )}

            {/* 4. 답변 근거 요약 (Req 7.3) */}
            {evidence.length > 0 && (
              <ul className="evidence-list">
                {evidence.map((line, i) => (
                  <li key={`${line}-${i}`}>{line}</li>
                ))}
              </ul>
            )}

            {/* 5. 관련 노드 테이블 — 클래스별 탭 (Req 8.1~8.4) */}
            {records.length > 0 && activeGroup && (
              <div className="audit-tables">
                <div className="audit-table-head">
                  <div className="audit-table-tabs" role="tablist">
                    {records.map((group, i) => {
                      const selected = i === activeTab
                      return (
                        <button
                          type="button"
                          key={group.key}
                          role="tab"
                          aria-selected={selected}
                          className={`audit-table-tab${selected ? ' active' : ''}`}
                          onClick={() => setActiveTab(i)}
                        >
                          {group.label}
                        </button>
                      )
                    })}
                  </div>
                  {/* Req 8.3: "전체 N건 중 M건 미리보기" */}
                  <span className="audit-table-meta">
                    전체 {activeGroup.total}건 중 {activeGroup.shown}건 미리보기
                  </span>
                </div>

                <div className="audit-table-view active" role="tabpanel">
                  <div className="audit-record-scroll">
                    <table className="audit-record-table">
                      <thead>
                        <tr>
                          {activeGroup.columns.map((col) => (
                            <th key={col}>{col}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {activeGroup.rows.map((row, i) => (
                          <tr key={row.id ?? i}>
                            {activeGroup.columns.map((col) => (
                              // Req 8.4, 10.3: 텍스트로만 렌더(마크다운/HTML 미해석)
                              <td key={col}>{row[col] ?? ''}</td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
