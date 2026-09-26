import { cleanup, fireEvent, render, screen, within } from '@testing-library/react'
import fc from 'fast-check'
import { describe, expect, it } from 'vitest'

import type {
  AnswerTrace,
  TraceClass,
  TraceRecordGroup,
  TraceRelation,
} from '@/hooks/useChat'

import { AnswerTracePanel } from './AnswerTracePanel'

// ---------------------------------------------------------------------------
// 테스트 헬퍼: AnswerTrace 구조에 맞춘 최소 fixture 빌더
// ---------------------------------------------------------------------------

const EMPTY_TRACE: AnswerTrace = {
  path: [],
  classes: [],
  relations: [],
  evidence: [],
  records: [],
}

function makeRecordGroup(overrides: Partial<TraceRecordGroup> = {}): TraceRecordGroup {
  const columns = overrides.columns ?? ['id', 'title_name_kor']
  const rows = overrides.rows ?? [
    { id: 'book_001', title_name_kor: '구운몽' },
    { id: 'book_002', title_name_kor: '사씨남정기' },
  ]
  return {
    key: overrides.key ?? 'book',
    node_class: overrides.node_class ?? 'Book',
    label: overrides.label ?? '이본',
    total: overrides.total ?? 142,
    shown: overrides.shown ?? rows.length,
    columns,
    rows,
  }
}

// ===========================================================================
// 8.3 단위 테스트 — 렌더/토글/탭/건수 표기
// Requirements: 6.2, 7.1, 8.3
// ===========================================================================

describe('AnswerTracePanel — 단위 (8.3)', () => {
  it('trace가 비어 있으면 아무것도 렌더하지 않는다 (버튼 부재) — Req 6.2', () => {
    const { container } = render(<AnswerTracePanel trace={EMPTY_TRACE} />)
    expect(container).toBeEmptyDOMElement()
    expect(
      screen.queryByRole('button', { name: /왜 이런 답이 나왔지/ }),
    ).not.toBeInTheDocument()
  })

  it('trace에 내용이 있으면 why-button을 렌더한다 — Req 7.1', () => {
    const trace: AnswerTrace = {
      ...EMPTY_TRACE,
      classes: [{ key: 'book', node_class: 'Book', label: '이본' }],
    }
    render(<AnswerTracePanel trace={trace} />)
    expect(
      screen.getByRole('button', { name: /왜 이런 답이 나왔지/ }),
    ).toBeInTheDocument()
  })

  it('토글 클릭 시 aria-expanded가 false→true로 바뀌고 패널에 open 클래스가 붙는다 — Req 7.1', () => {
    const trace: AnswerTrace = {
      ...EMPTY_TRACE,
      classes: [{ key: 'book', node_class: 'Book', label: '이본' }],
    }
    render(<AnswerTracePanel trace={trace} />)

    const button = screen.getByRole('button', { name: /왜 이런 답이 나왔지/ })
    expect(button).toHaveAttribute('aria-expanded', 'false')

    const panelId = button.getAttribute('aria-controls')!
    const panel = document.getElementById(panelId)!
    expect(panel).not.toHaveClass('open')

    fireEvent.click(button)

    expect(button).toHaveAttribute('aria-expanded', 'true')
    expect(panel).toHaveClass('open')
  })

  it('탭이 여러 개면 클릭으로 전환되어 활성 탭 표가 바뀐다 — Req 8.3', () => {
    const trace: AnswerTrace = {
      ...EMPTY_TRACE,
      records: [
        makeRecordGroup({
          key: 'book',
          label: '이본',
          columns: ['id', 'title_name_kor'],
          rows: [{ id: 'book_001', title_name_kor: '구운몽' }],
          total: 142,
        }),
        makeRecordGroup({
          key: 'review',
          label: '외평',
          columns: ['id', 'comment_kor'],
          rows: [{ id: 'rev_001', comment_kor: '평론입니다' }],
          total: 46,
        }),
      ],
    }
    render(<AnswerTracePanel trace={trace} />)
    fireEvent.click(screen.getByRole('button', { name: /왜 이런 답이 나왔지/ }))

    // 초기: 첫 탭(이본) 활성, 첫 탭 데이터가 보인다.
    const bookTab = screen.getByRole('tab', { name: '이본' })
    const reviewTab = screen.getByRole('tab', { name: '외평' })
    expect(bookTab).toHaveAttribute('aria-selected', 'true')
    expect(reviewTab).toHaveAttribute('aria-selected', 'false')
    expect(screen.getByText('구운몽')).toBeInTheDocument()
    expect(screen.queryByText('평론입니다')).not.toBeInTheDocument()

    // 두 번째 탭(외평)으로 전환 → 표가 바뀐다.
    fireEvent.click(reviewTab)
    expect(reviewTab).toHaveAttribute('aria-selected', 'true')
    expect(bookTab).toHaveAttribute('aria-selected', 'false')
    expect(screen.getByText('평론입니다')).toBeInTheDocument()
    expect(screen.queryByText('구운몽')).not.toBeInTheDocument()
  })

  it('"전체 N건 중 M건 미리보기" 텍스트가 total/shown과 일치한다 — Req 8.3', () => {
    const trace: AnswerTrace = {
      ...EMPTY_TRACE,
      records: [
        makeRecordGroup({
          key: 'book',
          label: '이본',
          rows: [
            { id: 'book_001', title_name_kor: '구운몽' },
            { id: 'book_002', title_name_kor: '사씨남정기' },
            { id: 'book_003', title_name_kor: '홍길동전' },
          ],
          shown: 3,
          total: 142,
        }),
      ],
    }
    render(<AnswerTracePanel trace={trace} />)
    fireEvent.click(screen.getByRole('button', { name: /왜 이런 답이 나왔지/ }))

    expect(screen.getByText('전체 142건 중 3건 미리보기')).toBeInTheDocument()
  })
})

// ===========================================================================
// fast-check arbitrary — 유효한 AnswerTrace 생성기
// ===========================================================================

/** 한국어/한자/영문/특수문자를 섞은 짧은 비어있지 않은 문자열. */
const textArb = fc
  .string({ minLength: 1, maxLength: 8 })
  .map((s) => s.replace(/\s+/g, '_'))
  .filter((s) => s.trim().length > 0)

const classArb: fc.Arbitrary<TraceClass> = fc.record({
  key: textArb,
  node_class: textArb,
  label: textArb,
})

const relationArb: fc.Arbitrary<TraceRelation> = fc.record({
  name: textArb,
  korean: textArb,
})

/** 컬럼 목록(중복 제거)과 그에 맞는 rows를 함께 만드는 record group 생성기. */
const recordGroupArb: fc.Arbitrary<TraceRecordGroup> = fc
  .record({
    key: textArb,
    node_class: textArb,
    label: textArb,
    columns: fc.uniqueArray(textArb, { minLength: 1, maxLength: 4 }),
    rowValues: fc.array(
      fc.array(fc.string({ minLength: 0, maxLength: 10 }), {
        minLength: 1,
        maxLength: 4,
      }),
      { minLength: 0, maxLength: 4 },
    ),
    totalExtra: fc.nat({ max: 1000 }),
  })
  .map(({ key, node_class, label, columns, rowValues, totalExtra }) => {
    const rows: Record<string, string>[] = rowValues.map((values, r) => {
      const row: Record<string, string> = { id: `${key}_${r}` }
      columns.forEach((col, c) => {
        if (col !== 'id') row[col] = values[c % values.length] ?? ''
      })
      return row
    })
    const cols = columns.includes('id') ? columns : ['id', ...columns]
    return {
      key,
      node_class,
      label,
      columns: cols,
      rows,
      shown: rows.length,
      total: rows.length + totalExtra,
    }
  })

/** 최소 한 필드는 비어있지 않은(=렌더되는) AnswerTrace 생성기. */
const nonEmptyTraceArb: fc.Arbitrary<AnswerTrace> = fc
  .record({
    path: fc.array(textArb, { maxLength: 4 }),
    classes: fc.array(classArb, { maxLength: 4 }),
    relations: fc.array(relationArb, { maxLength: 4 }),
    evidence: fc.array(textArb, { maxLength: 4 }),
    // records key는 React key로 쓰이므로 그룹 간 유일해야 한다.
    records: fc
      .uniqueArray(recordGroupArb, {
        minLength: 0,
        maxLength: 4,
        selector: (g) => g.key,
      }),
  })
  .filter(
    (t) =>
      t.path.length +
        t.classes.length +
        t.relations.length +
        t.evidence.length +
        t.records.length >
      0,
  )

/** 비어있을 수도, 아닐 수도 있는 AnswerTrace 생성기(Property 12용). */
const anyTraceArb: fc.Arbitrary<AnswerTrace> = fc.oneof(
  fc.constant(EMPTY_TRACE),
  nonEmptyTraceArb,
)

const RUNS = { numRuns: 100 }

// ===========================================================================
// 8.4 property 테스트 — 칩/탭/건수/렌더 무결성
// Property: 12, 13, 14, 15, 16, 17
// ===========================================================================

describe('AnswerTracePanel — property (8.4)', () => {
  // Feature: answer-trace-panel, Property 12
  it('근거 버튼 존재 ⇔ trace 비어있지 않음', () => {
    fc.assert(
      fc.property(anyTraceArb, (trace) => {
        const { container } = render(<AnswerTracePanel trace={trace} />)
        const isEmpty =
          trace.path.length === 0 &&
          trace.classes.length === 0 &&
          trace.relations.length === 0 &&
          trace.evidence.length === 0 &&
          trace.records.length === 0
        const button = screen.queryByRole('button', {
          name: /왜 이런 답이 나왔지/,
        })
        if (isEmpty) {
          expect(container).toBeEmptyDOMElement()
          expect(button).toBeNull()
        } else {
          expect(button).not.toBeNull()
        }
        cleanup()
      }),
      RUNS,
    )
  })

  // Feature: answer-trace-panel, Property 13
  it('노드 칩이 label과 node_class 텍스트를 모두 포함한다', () => {
    fc.assert(
      fc.property(
        fc.array(classArb, { minLength: 1, maxLength: 4 }),
        (classes) => {
          const trace: AnswerTrace = { ...EMPTY_TRACE, classes }
          render(<AnswerTracePanel trace={trace} />)
          fireEvent.click(
            screen.getByRole('button', { name: /왜 이런 답이 나왔지/ }),
          )
          for (const cls of classes) {
            const chips = screen.getAllByText(cls.label, {
              selector: '.audit-chip',
            })
            // label을 담은 칩 중, node_class도 함께 담은 칩이 있어야 한다.
            const match = chips.some((chip) =>
              within(chip).queryByText(cls.node_class, {
                selector: 'small',
                exact: false,
              }),
            )
            expect(match || chipHoldsBoth(cls.label, cls.node_class)).toBe(true)
          }
          cleanup()
        },
      ),
      RUNS,
    )
  })

  // Feature: answer-trace-panel, Property 14
  it('관계 칩이 원문 name과 korean 텍스트를 모두 포함한다', () => {
    fc.assert(
      fc.property(
        fc.array(relationArb, { minLength: 1, maxLength: 4 }),
        (relations) => {
          const trace: AnswerTrace = { ...EMPTY_TRACE, relations }
          const { container } = render(<AnswerTracePanel trace={trace} />)
          fireEvent.click(
            screen.getByRole('button', { name: /왜 이런 답이 나왔지/ }),
          )
          const chips = Array.from(
            container.querySelectorAll('.audit-chip'),
          ) as HTMLElement[]
          for (const rel of relations) {
            const found = chips.some(
              (chip) =>
                chip.textContent?.includes(rel.name) &&
                within(chip).queryByText(rel.korean, { selector: 'small' }) !==
                  null,
            )
            expect(found).toBe(true)
          }
          cleanup()
        },
      ),
      RUNS,
    )
  })

  // Feature: answer-trace-panel, Property 15
  it('렌더된 탭 수가 records 길이와 같고 각 탭이 대응 클래스에 매핑된다', () => {
    fc.assert(
      fc.property(
        fc.uniqueArray(recordGroupArb, {
          minLength: 1,
          maxLength: 4,
          selector: (g) => g.key,
        }),
        (records) => {
          const trace: AnswerTrace = { ...EMPTY_TRACE, records }
          render(<AnswerTracePanel trace={trace} />)
          fireEvent.click(
            screen.getByRole('button', { name: /왜 이런 답이 나왔지/ }),
          )
          const tabs = screen.getAllByRole('tab')
          expect(tabs).toHaveLength(records.length)
          records.forEach((group, i) => {
            expect(tabs[i]).toHaveTextContent(group.label)
          })
          cleanup()
        },
      ),
      RUNS,
    )
  })

  // Feature: answer-trace-panel, Property 16
  it('활성 탭의 "전체 N건 중 M건"이 total/shown과 일치한다', () => {
    fc.assert(
      fc.property(
        fc.uniqueArray(recordGroupArb, {
          minLength: 1,
          maxLength: 4,
          selector: (g) => g.key,
        }),
        fc.nat(),
        (records, tabPick) => {
          const trace: AnswerTrace = { ...EMPTY_TRACE, records }
          render(<AnswerTracePanel trace={trace} />)
          fireEvent.click(
            screen.getByRole('button', { name: /왜 이런 답이 나왔지/ }),
          )
          const index = tabPick % records.length
          fireEvent.click(screen.getAllByRole('tab')[index])
          const group = records[index]
          expect(
            screen.getByText(
              `전체 ${group.total}건 중 ${group.shown}건 미리보기`,
            ),
          ).toBeInTheDocument()
          cleanup()
        },
      ),
      RUNS,
    )
  })

  // Feature: answer-trace-panel, Property 17
  it('마크다운/HTML 마커·한국어 원문이 든 셀 값이 텍스트 그대로 렌더된다', () => {
    // 마크다운/HTML/한국어를 섞은 셀 값 생성기
    const cellArb = fc.constantFrom(
      '<b>굵게</b>',
      '**강조**',
      '<script>alert(1)</script>',
      '[링크](http://x)',
      '구운몽 <九雲夢>',
      '값 & <tag> "따옴표"',
      '# 제목',
    )
    fc.assert(
      fc.property(
        fc.array(cellArb, { minLength: 1, maxLength: 4 }),
        (values) => {
          const rows: Record<string, string>[] = values.map((v, i) => ({
            id: `r_${i}`,
            content: v,
          }))
          const trace: AnswerTrace = {
            ...EMPTY_TRACE,
            records: [
              {
                key: 'k',
                node_class: 'K',
                label: '테스트',
                total: rows.length,
                shown: rows.length,
                columns: ['id', 'content'],
                rows,
              },
            ],
          }
          const { container } = render(<AnswerTracePanel trace={trace} />)
          fireEvent.click(
            screen.getByRole('button', { name: /왜 이런 답이 나왔지/ }),
          )
          for (const v of values) {
            // 텍스트 노드로 정확히 존재해야 한다(요소로 해석되지 않음).
            const cell = screen.getAllByText(v, { selector: 'td' })
            expect(cell.length).toBeGreaterThan(0)
          }
          // 셀 값 안의 마커가 실제 요소로 해석되지 않았는지 확인.
          expect(container.querySelector('td script')).toBeNull()
          expect(container.querySelector('td b')).toBeNull()
          cleanup()
        },
      ),
      RUNS,
    )
  })
})

/** label과 node_class를 모두 담은 audit-chip이 존재하는지 DOM 전체에서 확인. */
function chipHoldsBoth(label: string, nodeClass: string): boolean {
  const chips = Array.from(
    document.querySelectorAll('.audit-chip'),
  ) as HTMLElement[]
  return chips.some(
    (chip) =>
      chip.textContent?.includes(label) &&
      within(chip).queryByText(nodeClass, { selector: 'small' }) !== null,
  )
}

// ===========================================================================
// 8.5 접근성 property 테스트 — aria 상태
// Property: 18, 19
// ===========================================================================

describe('AnswerTracePanel — 접근성 property (8.5)', () => {
  // Feature: answer-trace-panel, Property 18
  it('토글 상태 전환 시퀀스에서 aria-expanded가 패널 open 상태와 항상 일치하고 aria-controls가 패널 id를 가리킨다', () => {
    fc.assert(
      fc.property(
        nonEmptyTraceArb,
        // 토글 클릭 횟수(0~6회)
        fc.integer({ min: 0, max: 6 }),
        (trace, clickCount) => {
          render(<AnswerTracePanel trace={trace} />)
          const button = screen.getByRole('button', {
            name: /왜 이런 답이 나왔지/,
          })
          const panelId = button.getAttribute('aria-controls')
          expect(panelId).toBeTruthy()
          const panel = document.getElementById(panelId!)
          expect(panel).not.toBeNull()

          let expectedOpen = false
          const assertConsistent = () => {
            expect(button.getAttribute('aria-expanded')).toBe(
              String(expectedOpen),
            )
            expect(panel!.classList.contains('open')).toBe(expectedOpen)
          }
          assertConsistent()
          for (let i = 0; i < clickCount; i++) {
            fireEvent.click(button)
            expectedOpen = !expectedOpen
            assertConsistent()
          }
          cleanup()
        },
      ),
      RUNS,
    )
  })

  // Feature: answer-trace-panel, Property 19
  it('탭 선택을 바꿔가며 선택된 탭만 aria-selected=true, 나머지는 false(배타성)', () => {
    fc.assert(
      fc.property(
        fc.uniqueArray(recordGroupArb, {
          minLength: 2,
          maxLength: 5,
          selector: (g) => g.key,
        }),
        fc.array(fc.nat(), { minLength: 1, maxLength: 6 }),
        (records, picks) => {
          const trace: AnswerTrace = { ...EMPTY_TRACE, records }
          render(<AnswerTracePanel trace={trace} />)
          fireEvent.click(
            screen.getByRole('button', { name: /왜 이런 답이 나왔지/ }),
          )

          const assertExclusive = (selectedIndex: number) => {
            const tabs = screen.getAllByRole('tab')
            tabs.forEach((tab, i) => {
              expect(tab.getAttribute('aria-selected')).toBe(
                String(i === selectedIndex),
              )
            })
          }
          // 초기 선택은 첫 탭.
          assertExclusive(0)
          for (const pick of picks) {
            const index = pick % records.length
            fireEvent.click(screen.getAllByRole('tab')[index])
            assertExclusive(index)
          }
          cleanup()
        },
      ),
      RUNS,
    )
  })
})
