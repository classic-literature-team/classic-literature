import '@xyflow/react/dist/style.css'
import '@/styles/home.css'
import '@/styles/graph.css'

import {
  Background,
  Controls,
  type Edge,
  type Node,
  ReactFlow,
} from '@xyflow/react'
import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { type GraphNode, useGraph, useNodeSearch } from '@/hooks/useGraph'

// 노드 클래스별 색상
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

function colorFor(nodeClass: string): string {
  return CLASS_COLORS[nodeClass] ?? '#7a8fa0'
}

export function GraphPage() {
  const navigate = useNavigate()
  const [term, setTerm] = useState('')
  const [query, setQuery] = useState('')
  const [centerId, setCenterId] = useState<string | null>(null)

  const search = useNodeSearch(query)
  const graph = useGraph(centerId)

  // 그래프 데이터를 React Flow 노드/엣지로 변환 (중심=가운데, 이웃=원형 배치)
  const { nodes, edges } = useMemo(() => {
    if (!graph.data) return { nodes: [], edges: [] }

    const neighbors = graph.data.nodes.filter((n) => n.id !== centerId)
    const cx = 400
    const cy = 300
    const radius = 260

    const rfNodes: Node[] = graph.data.nodes.map((n) => {
      if (n.id === centerId) {
        return {
          id: n.id,
          position: { x: cx, y: cy },
          data: { label: n.label },
          style: nodeStyle(n, true),
        }
      }
      const idx = neighbors.findIndex((x) => x.id === n.id)
      const angle = (idx / Math.max(neighbors.length, 1)) * 2 * Math.PI
      return {
        id: n.id,
        position: {
          x: cx + radius * Math.cos(angle),
          y: cy + radius * Math.sin(angle),
        },
        data: { label: n.label },
        style: nodeStyle(n, false),
      }
    })

    const rfEdges: Edge[] = graph.data.edges.map((e) => ({
      id: e.id,
      source: e.source,
      target: e.target,
      label: e.relation ?? undefined,
      animated: true,
      style: { stroke: '#b8daf5' },
      labelStyle: { fontSize: 10, fill: '#2a4560' },
    }))

    return { nodes: rfNodes, edges: rfEdges }
  }, [graph.data, centerId])

  function nodeStyle(n: GraphNode, isCenter: boolean): React.CSSProperties {
    return {
      background: colorFor(n.node_class),
      color: '#fff',
      border: isCenter ? '3px solid #1a4a7a' : '1px solid #fff',
      borderRadius: 10,
      padding: '6px 10px',
      fontSize: isCenter ? 13 : 11,
      fontWeight: isCenter ? 700 : 500,
      width: 150,
      textAlign: 'center',
    }
  }

  return (
    <div className="home-root">
      <div className="graph-page">
        <button
          type="button"
          className="chat-back"
          onClick={() => navigate('/')}
        >
          ← 홈으로
        </button>

        <div className="graph-head">
          <h2>지식그래프</h2>
          <p>작품·인물·이본의 관계를 탐색하세요.</p>
        </div>

        <form
          className="graph-search"
          onSubmit={(e) => {
            e.preventDefault()
            setQuery(term)
          }}
        >
          <input
            className="chat-input"
            value={term}
            onChange={(ev) => setTerm(ev.target.value)}
            placeholder="작품·인물 이름으로 검색 (예: 운영전, 최치원)"
          />
          <button className="chat-send" type="submit">
            검색
          </button>
        </form>

        {search.data && search.data.length > 0 && (
          <div className="graph-results">
            {search.data.map((n) => (
              <button
                key={n.id}
                type="button"
                className="graph-result-chip"
                style={{ borderLeftColor: colorFor(n.node_class) }}
                onClick={() => setCenterId(n.id)}
              >
                {n.label}
                <span className="graph-class">{n.node_class}</span>
              </button>
            ))}
          </div>
        )}

        <div className="graph-canvas">
          {!centerId && (
            <div className="graph-empty">
              위에서 노드를 검색하고 선택하면 관계 그래프가 표시됩니다.
            </div>
          )}
          {centerId && graph.isLoading && (
            <div className="graph-empty">불러오는 중…</div>
          )}
          {centerId && graph.data && (
            <ReactFlow
              nodes={nodes}
              edges={edges}
              fitView
              onNodeClick={(_, node) => setCenterId(node.id)}
            >
              <Background />
              <Controls />
            </ReactFlow>
          )}
        </div>
      </div>
    </div>
  )
}
