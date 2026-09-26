// AI 질문 화면(ChatPage) 가이드 패널 데이터. 시안 ai-chat-2의 한국어 원문 보존.

export type CategoryId =
  | 'bibliographic'
  | 'participatory'
  | 'arrangement'
  | 'expressive'

export interface CategoryNode {
  /** 노드 라벨(한국어 원문) */
  label: string
  /** 노드 설명(한국어 원문) */
  description: string
}

export interface Category {
  id: CategoryId
  label: string
  nodes: CategoryNode[]
}

/** 카테고리 4종과 각 노드 목록 */
export const guideCategories: Category[] = [
  {
    id: 'bibliographic',
    label: '서지적요소',
    nodes: [
      {
        label: '이본',
        description:
          '기준본에 대한 서지 사항으로 제목·소장처·형태·연대 등의 정보를 다룬다.',
      },
      {
        label: '작품집',
        description:
          '작품집에 대한 서지 사항으로 제목·수록 작품 등의 정보를 다룬다.',
      },
      {
        label: '인물',
        description:
          '작품을 직접 창작했거나 복본의 제작 및 편집·향유를 담당한 사람을 다룬다.',
      },
      {
        label: '작품',
        description: '비실재적 개념으로 작품의 전반적 구성 정보를 다룬다.',
      },
    ],
  },
  {
    id: 'participatory',
    label: '참여적요소',
    nodes: [
      {
        label: '비점',
        description:
          '작품 본문 근처에 圈·點·線 등의 형태로 표시한 반응들을 다룬다.',
      },
      {
        label: '외평',
        description:
          '이본에서 발견되는 감상·해석·논평 성격의 서·발·필사기 등을 다룬다.',
      },
      {
        label: '연관 작품',
        description:
          '소설의 향유·창작·전파 등과 관련해 문인들이 남긴 시문 등을 다룬다.',
      },
    ],
  },
  {
    id: 'arrangement',
    label: '배열적요소',
    nodes: [
      {
        label: '장면',
        description:
          '특정 장소에서 발생하는 최소 단위로서의 사건으로 작품의 원문·번역, 시점·언어 등을 다룬다.',
      },
      {
        label: '등장인물',
        description: '캐릭터의 명칭과 캐릭터가 등장하는 작품을 다룬다.',
      },
      {
        label: '신분',
        description: '작품 속에 등장하는 캐릭터의 신분과 지위를 다룬다.',
      },
      {
        label: '요소',
        description: '작품 속에 등장하는 캐릭터의 구성적 정보를 다룬다.',
      },
      {
        label: '개별목차',
        description:
          '작품의 창작자가 자의적으로 내용을 분절한 회목·역사서 체제 등의 기술 체계를 말한다. (총목)',
      },
      {
        label: '대표목차',
        description:
          '작품의 창작자가 자의적으로 내용을 분절한 회목·역사서 체제 등의 기술 체계를 말한다. (세목)',
      },
      {
        label: '시대',
        description: '작품의 무대가 되는 시대적[왕조] 정보를 다룬다.',
      },
      {
        label: '공간',
        description: '작품의 무대가 되는 차원적·지역적 권역을 다룬다.',
      },
      {
        label: '장소',
        description: '작품의 무대가 되는 경험적·실재적 권역을 다룬다.',
      },
      {
        label: '논평',
        description: '작품 곳곳에 존재하는 여러 층위의 비평을 다룬다.',
      },
      {
        label: '평비',
        description: '넓은 의미의 평비본소설에서 발견되는 평비자의 비평을 다룬다.',
      },
    ],
  },
  {
    id: 'expressive',
    label: '표현적요소',
    nodes: [
      {
        label: '전고',
        description: '각종 개체에 녹아 있는 전고 및 관용적 표현들을 다룬다.',
      },
      {
        label: '소작품',
        description: '작품 안에 문체로서 독립화가 가능한 소작품을 다룬다.',
      },
    ],
  },
]

/** 예시 질문 6종(한국어 원문) */
export const exampleQuestions: string[] = [
  '나말여초-조선전기 한문소설 작품들과 이본 현황을 모두 알려줘.',
  '「이석단전」에 등장인물들의 사회적 지위와 속성들을 모두 알려줘.',
  '「구운몽」‧「홍백화전」‧「옥루몽」‧「창선감의록」‧「청백운」과 같은 재자가인소설류 서발문을 모두 알려줘.',
  '환생‧재생‧선화 등을 겪는 인물과 그 변동 맥락을 모두 알려줘.',
  '평비 및 주석을 보유한 한문소설 목록과 이본을 모두 알려줘.',
  '장회를 보유한 한문소설의 목록과 해당 세부 목차를 모두 알려줘.',
]

/** 첫 진입 시 표시되는 양소유 페르소나 인사말 */
export const personaGreeting =
  '세인들의 시시한 질문 따위 내 부채질 한 번이면 해결될 터이니, 가소로운 고민이라도 사양 말고 털어놓아 보아라.'

/** 인사말 하단 안내(탐색 가능 범위) */
export const greetingSourceNote =
  '탐색 가능 범위 · 작품 / 이본 / 장면 / 등장인물 / 외평 / 평비 / 전고'
