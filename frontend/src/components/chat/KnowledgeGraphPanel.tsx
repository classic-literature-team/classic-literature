import '@xyflow/react/dist/style.css'

import dagre from '@dagrejs/dagre'
import {
  Background,
  Controls,
  type Edge,
  type Node,
  Position,
  ReactFlow,
} from '@xyflow/react'
import { useEffect, useMemo, useState } from 'react'

import type { AnswerTrace, TraceRecordGroup } from '@/hooks/useChat'

interface KnowledgeGraphPanelProps {
  trace: AnswerTrace
  open: boolean
  onClose: () => void
}

/** 노드에 붙는 부가 데이터(인스펙터용). React Flow Node.data에 담긴다. */
interface KgNodeData extends Record<string, unknown> {
  label: string
  node_class: string
  groupLabel: string
  /** 레코드 노드면 원본 행 데이터, 클래스 노드면 undefined. */
  row?: Record<string, string>
}

/** 레코드 노드 라벨로 쓸 대표 이름 컬럼(우선순위 순). */
const NAME_COLUMNS = [
  'title_name_kor',
  'work_kor',
  'name_kor',
  'name',
  'ch_name_kor',
] as const

/** node_class별 색상 팔레트(하늘색 톤 위주, 클래스 구분 가능하게). */
const CLASS_COLORS: Record<string, string> = {
  Book: '#4ba3d8',
  AbstractWork: '#e06088',
  WorksCompilation: '#a07040',
  Character: '#4a90c8',
  Scene: '#c94070',
  Participant: '#8a60c0',
  Number: '#4aae5a',
  Episode: '#4aae5a',
  Review: '#8a60c0',
  BackgroundE: '#40a0a0',
}

/** 팔레트에 없는 클래스는 안정적으로 하늘색~보조 톤에서 색을 배정한다. */
const FALLBACK_COLORS = [
  '#4ba3d8',
  '#2d8bc4',
  '#7dbfe8',
  '#8a60c0',
  '#40a0a0',
  '#a07040',
  '#c94070',
  '#4aae5a',
]

/** 레코드 행에서 대표 이름을 고른다. 없으면 id, 그것도 없으면 fallback. */
function pickLabel(row: Record<string, string>, fallback: string): string {
  for (const col of NAME_COLUMNS) {
    const value = row[col]
    if (value != null && value !== '') return value
  }
  const id = row.id
  if (id != null && id !== '') return id
  return fallback
}

interface BuiltNode {
  id: string
  data: KgNodeData
}

/** dagre에 넘길 노드 크기(실제 노드 160 + padding/border 여유를 감안한 상수). */
const NODE_W = 172
const NODE_H = 44

/**
 * dagre로 노드 좌표(position)만 계산해 채워 넣는다.
 *
 * 노드/엣지의 "구성"(id·data·색·label)은 호출부가 이미 만든 그대로 유지하고,
 * 여기서는 오직 좌표만 계층 레이아웃으로 대체한다. 방향은 LR(좌→우).
 *
 * dagre는 노드 "중심" 좌표를 주고 React Flow는 "좌상단" 좌표를 쓰므로
 * position = { x - width/2, y - height/2 }로 보정한다. dagre가 좌표를
 * 못 준 노드(고립 노드 등)는 순서대로 세로 폴백 배치한다.
 */
function layoutWithDagre(
  nodes: Node<KgNodeData>[],
  edges: Edge[],
): Node<KgNodeData>[] {
  const g = new dagre.graphlib.Graph()
  g.setDefaultEdgeLabel(() => ({}))
  g.setGraph({
    rankdir: 'LR',
    nodesep: 30,
    ranksep: 90,
    marginx: 20,
    marginy: 20,
  })

  nodes.forEach((node) => {
    g.setNode(node.id, { width: NODE_W, height: NODE_H })
  })
  edges.forEach((edge) => {
    g.setEdge(edge.source, edge.target)
  })

  dagre.layout(g)

  let fallbackIdx = 0
  return nodes.map((node) => {
    const laidOut = g.node(node.id) as { x?: number; y?: number } | undefined
    let position: { x: number; y: number }
    if (
      laidOut &&
      typeof laidOut.x === 'number' &&
      typeof laidOut.y === 'number'
    ) {
      // dagre 중심 좌표 → React Flow 좌상단 좌표 보정.
      position = { x: laidOut.x - NODE_W / 2, y: laidOut.y - NODE_H / 2 }
    } else {
      // 폴백: 좌표를 못 받은 노드는 순서대로 세로 배치.
      position = { x: 0, y: fallbackIdx * (NODE_H + 20) }
      fallbackIdx += 1
    }
    return {
      ...node,
      position,
      sourcePosition: Position.Right,
      targetPosition: Position.Left,
    }
  })
}

/**
 * 지식그래프 노드/엣지를 만든다.
 *
 * - trace.edges가 있고 비어 있지 않으면 백엔드가 준 실제 노드/연결로 그리는
 *   "정확 모드"(buildExactGraph)를 쓴다.
 * - 그 외(edge 미제공)에는 기존 A 근사 로직(buildApproxGraph)으로 fallback한다.
 */
function buildGraph(trace: AnswerTrace): {
  nodes: Node<KgNodeData>[]
  edges: Edge[]
} {
  if (trace.edges && trace.edges.length > 0) {
    return buildExactGraph(trace)
  }
  return buildApproxGraph(trace)
}

/** node_class별 색상 팔레트를 상태를 가진 색 배정 함수로 만든다. */
function makeColorFor(): (nodeClass: string) => string {
  const classColor = new Map<string, string>()
  let fallbackIdx = 0
  return (nodeClass: string): string => {
    if (CLASS_COLORS[nodeClass]) return CLASS_COLORS[nodeClass]
    const existing = classColor.get(nodeClass)
    if (existing) return existing
    const color = FALLBACK_COLORS[fallbackIdx % FALLBACK_COLORS.length]
    fallbackIdx += 1
    classColor.set(nodeClass, color)
    return color
  }
}

/**
 * 정확 모드: 백엔드 trace.nodes/trace.edges를 그대로 React Flow로 옮긴다.
 *
 * 노드 라벨은 name > label > id 순. records에 같은 id의 행이 있으면
 * 인스펙터에서 컬럼-값을 보여주도록 data.row에 담는다.
 *
 * 레이아웃: 노드/엣지 구성만 여기서 만들고, 좌표는 layoutWithDagre로
 * LR 계층 배치한다.
 */
function buildExactGraph(trace: AnswerTrace): {
  nodes: Node<KgNodeData>[]
  edges: Edge[]
} {
  const traceNodes = trace.nodes ?? []
  const traceEdges = trace.edges ?? []

  // id → 원본 레코드 행(있으면). records를 id로 인덱싱해 인스펙터에 활용.
  const rowById = new Map<string, Record<string, string>>()
  trace.records.forEach((group) => {
    group.rows.forEach((row) => {
      const id = row.id
      if (id != null && id !== '') rowById.set(id, row)
    })
  })

  const colorFor = makeColorFor()

  // 노드 메타를 id로 모은다. edges가 참조하지만 nodes에 없는 id는 최소 노드로 보충.
  interface NodeMeta {
    id: string
    node_class: string
    label: string
    name: string
  }
  const metaById = new Map<string, NodeMeta>()
  traceNodes.forEach((n) => {
    metaById.set(n.id, {
      id: n.id,
      node_class: n.node_class,
      label: n.label,
      name: n.name,
    })
  })
  const ensureMeta = (id: string) => {
    if (!metaById.has(id)) {
      metaById.set(id, { id, node_class: '', label: id, name: '' })
    }
  }
  traceEdges.forEach((e) => {
    ensureMeta(e.source)
    ensureMeta(e.target)
  })

  const ids = [...metaById.keys()]

  // 노드 구성(좌표 제외). 좌표는 뒤에서 dagre로 채운다.
  const rawNodes: Node<KgNodeData>[] = []
  ids.forEach((id) => {
    const meta = metaById.get(id)
    if (!meta) return
    const label = meta.name || meta.label || meta.id
    rawNodes.push({
      id,
      position: { x: 0, y: 0 },
      data: {
        label,
        node_class: meta.node_class,
        groupLabel: meta.label,
        row: rowById.get(id),
      },
      style: nodeStyle(colorFor(meta.node_class)),
    })
  })

  // 엣지: trace.edges 그대로. 라벨은 korean 우선, 없으면 relation. id는 유니크하게.
  const rfEdges: Edge[] = traceEdges.map((e) => ({
    ...makeEdge(e.source, e.target, e.korean || e.relation),
    id: `${e.source}->${e.target}:${e.relation}`,
  }))

  return { nodes: layoutWithDagre(rawNodes, rfEdges), edges: rfEdges }
}

/**
 * trace 데이터만으로 근사 지식그래프의 노드/엣지를 만든다(edge 미제공 시 fallback).
 *
 * 노드 규칙:
 *  - records의 각 그룹의 각 row를 노드 1개로 만든다.
 *  - rows가 빈 그룹(shown=0)은 그룹 자체를 노드 1개로.
 *  - classes에 있으나 records에 없는 클래스도 노드 1개로(레코드 없음).
 *
 * 층 배치: trace.path 순서를 층 순서로 보고, 각 클래스 label이 path에서
 * 등장하는 인덱스로 층을 정한다(매칭 안 되면 맨 뒤 층). 엣지 구성은 이
 * 층 순서를 따르되, 최종 좌표는 layoutWithDagre로 LR 계층 배치한다.
 *
 * 엣지: 인접 층 사이를 relations 라벨로 잇는 대표 근사(fan-out / 같은 인덱스).
 */
function buildApproxGraph(trace: AnswerTrace): {
  nodes: Node<KgNodeData>[]
  edges: Edge[]
} {
  const { path, classes, relations, records } = trace

  // path에서 label의 층 인덱스를 구한다(매칭 없으면 맨 뒤).
  const backLayer = Math.max(path.length, 1)
  const layerOf = (label: string): number => {
    const idx = path.indexOf(label)
    return idx === -1 ? backLayer : idx
  }

  // node_class → 색상. 팔레트에 없으면 fallback을 순서대로 배정.
  const colorFor = makeColorFor()

  // records에 존재하는 클래스 label 집합(중복 노드 방지용).
  const recordLabels = new Set(records.map((g) => g.label))

  // 층별로 노드를 모은다.
  const layers = new Map<number, BuiltNode[]>()
  const pushNode = (layer: number, node: BuiltNode) => {
    const list = layers.get(layer)
    if (list) list.push(node)
    else layers.set(layer, [node])
  }

  const addGroup = (group: TraceRecordGroup) => {
    const layer = layerOf(group.label)
    if (group.rows.length === 0) {
      // 빈 그룹: 클래스 자체를 노드 1개로.
      pushNode(layer, {
        id: `g:${group.key}`,
        data: {
          label: group.label,
          node_class: group.node_class,
          groupLabel: group.label,
        },
      })
      return
    }
    group.rows.forEach((row, i) => {
      const rid = row.id != null && row.id !== '' ? row.id : String(i)
      pushNode(layer, {
        id: `r:${group.key}:${rid}`,
        data: {
          label: pickLabel(row, group.label),
          node_class: group.node_class,
          groupLabel: group.label,
          row,
        },
      })
    })
  }

  records.forEach(addGroup)

  // records에 그룹이 없는 클래스도 노드로 추가.
  classes.forEach((cls) => {
    if (recordLabels.has(cls.label)) return
    pushNode(layerOf(cls.label), {
      id: `c:${cls.key}`,
      data: {
        label: cls.label,
        node_class: cls.node_class,
        groupLabel: cls.label,
      },
    })
  })

  // 노드 구성(좌표 제외). 층 순서는 엣지 생성에만 쓰고, 좌표는 dagre가 채운다.
  const rawNodes: Node<KgNodeData>[] = []
  const sortedLayers = [...layers.keys()].sort((a, b) => a - b)
  const layerNodeIds = new Map<number, string[]>()

  sortedLayers.forEach((layer) => {
    const list = layers.get(layer) ?? []
    layerNodeIds.set(
      layer,
      list.map((n) => n.id),
    )
    list.forEach((n) => {
      rawNodes.push({
        id: n.id,
        position: { x: 0, y: 0 },
        data: n.data,
        style: nodeStyle(colorFor(n.data.node_class)),
      })
    })
  })

  // 엣지: 인접 층 사이 대표 연결. relations를 순서대로 라벨로 대응.
  const rfEdges: Edge[] = []
  for (let li = 0; li < sortedLayers.length - 1; li += 1) {
    const fromIds = layerNodeIds.get(sortedLayers[li]) ?? []
    const toIds = layerNodeIds.get(sortedLayers[li + 1]) ?? []
    if (fromIds.length === 0 || toIds.length === 0) continue

    const rel = relations[li]
    const relLabel = rel ? rel.korean || rel.name : undefined

    if (fromIds.length === 1) {
      // 이전 층 1개 → 다음 층 전부 fan-out.
      const src = fromIds[0]
      toIds.forEach((tgt) => rfEdges.push(makeEdge(src, tgt, relLabel)))
    } else {
      // 같은 인덱스끼리 잇고, 남는 다음 층 노드는 이전 층 첫 노드에서 잇는다.
      toIds.forEach((tgt, i) => {
        const src = i < fromIds.length ? fromIds[i] : fromIds[0]
        rfEdges.push(makeEdge(src, tgt, relLabel))
      })
    }
  }

  return { nodes: layoutWithDagre(rawNodes, rfEdges), edges: rfEdges }
}

function makeEdge(source: string, target: string, label?: string): Edge {
  return {
    id: `${source}->${target}`,
    source,
    target,
    label,
    animated: true,
    style: { stroke: '#b8daf5' },
    labelStyle: { fontSize: 10, fill: '#2a4560' },
  }
}

function nodeStyle(color: string): React.CSSProperties {
  return {
    background: color,
    color: '#fff',
    border: '1px solid #fff',
    borderRadius: 10,
    padding: '6px 10px',
    fontSize: 11,
    fontWeight: 500,
    width: 160,
    textAlign: 'center',
  }
}

/**
 * AI 답변 근거를 React Flow 지식그래프로 보여주는 비모달 플로팅 패널.
 * 딤/오버레이 없이 화면 위에 떠 있어 바깥 화면을 계속 조작할 수 있다.
 * open=false면 아무것도 렌더하지 않는다.
 */
export function KnowledgeGraphPanel({
  trace,
  open,
  onClose,
}: KnowledgeGraphPanelProps) {
  const [selected, setSelected] = useState<string | null>(null)

  const { nodes, edges } = useMemo(() => buildGraph(trace), [trace])

  // Esc로 닫기(선택 기능). 비모달이므로 포커스 트랩/딤은 두지 않는다.
  useEffect(() => {
    if (!open) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open, onClose])

  if (!open) return null

  const selectedNode = nodes.find((n) => n.id === selected)
  const selectedData = selectedNode?.data

  return (
    <aside className="kg-panel" aria-label="지식 그래프">
      <div className="kg-panel-head">
        <h4>지식 그래프</h4>
        <button
          type="button"
          className="kg-close"
          aria-label="지식 그래프 닫기"
          onClick={onClose}
        >
          ✕
        </button>
      </div>

      <div className="kg-panel-body">
        <div className="kg-flow">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            fitView
            onNodeClick={(_, node) => setSelected(node.id)}
          >
            <Background />
            <Controls />
          </ReactFlow>
        </div>

        <div className="kg-inspector">
          {!selectedData && (
            <p className="kg-inspector-hint">노드를 선택하세요</p>
          )}
          {selectedData && (
            <>
              <div className="kg-inspector-head">
                <strong>{selectedData.label}</strong>
                <small>{selectedData.node_class}</small>
              </div>
              {selectedData.row ? (
                <dl className="kg-fields">
                  {Object.entries(selectedData.row)
                    .filter(([, value]) => value != null && value !== '')
                    .map(([key, value]) => (
                      <div className="kg-field" key={key}>
                        <dt>{key}</dt>
                        <dd>{value}</dd>
                      </div>
                    ))}
                </dl>
              ) : (
                <p className="kg-inspector-hint">레코드 없음</p>
              )}
            </>
          )}
        </div>
      </div>
    </aside>
  )
}
