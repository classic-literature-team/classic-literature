import { useQuery } from '@tanstack/react-query'

import { apiFetch } from '@/utils/api'

export interface GraphNode {
  id: string
  label: string
  node_class: string
}

export interface GraphEdge {
  id: string
  source: string
  target: string
  relation: string | null
}

export interface GraphData {
  nodes: GraphNode[]
  edges: GraphEdge[]
}

/** 노드 이름으로 시작 노드 후보 검색 */
export function useNodeSearch(query: string) {
  return useQuery({
    queryKey: ['graph', 'search', query],
    queryFn: () =>
      apiFetch<GraphNode[]>(`/graph/search?q=${encodeURIComponent(query)}`),
    enabled: query.trim().length > 0,
  })
}

/** 중심 노드 기준 1-hop 그래프 조회 */
export function useGraph(nodeId: string | null) {
  return useQuery({
    queryKey: ['graph', nodeId],
    queryFn: () =>
      apiFetch<GraphData>(`/graph?node_id=${encodeURIComponent(nodeId ?? '')}`),
    enabled: Boolean(nodeId),
  })
}
