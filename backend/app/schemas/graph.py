from pydantic import BaseModel


class GraphNode(BaseModel):
    """그래프의 노드 하나."""

    id: str
    label: str
    node_class: str


class GraphEdge(BaseModel):
    """그래프의 엣지(관계) 하나."""

    id: str
    source: str
    target: str
    relation: str | None = None


class GraphData(BaseModel):
    """React Flow가 렌더링할 노드/엣지 묶음."""

    nodes: list[GraphNode]
    edges: list[GraphEdge]
