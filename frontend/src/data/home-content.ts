export type TabId =
  'intro' | 'biblio' | 'parti' | 'arran' | 'expre' | 'graph' | 'genre' | 'yangs'

export interface TabMeta {
  id: TabId
  label: string
  icon: string
  yangs?: boolean
}

/** 패널을 전환하는 탭 (같은 페이지 내 콘텐츠 교체) */
export const tabs: TabMeta[] = [
  { id: 'intro', label: 'DB소개', icon: '📋' },
  { id: 'biblio', label: '서지적요소', icon: '📖' },
  { id: 'parti', label: '참여적요소', icon: '💬' },
  { id: 'arran', label: '배열적요소', icon: '🧩' },
  { id: 'expre', label: '표현적요소', icon: '🎨' },
  { id: 'graph', label: '지식그래프', icon: '🕸' },
  { id: 'genre', label: '장르별 목록', icon: '📚' },
  { id: 'yangs', label: '양소유의 연애상담소', icon: '💌', yangs: true },
]

export interface LinkTab {
  label: string
  icon: string
  to: string
  variant: 'chat' | 'keyword'
}

/** 다른 페이지로 이동하는 탭 */
export const linkTabs: LinkTab[] = [
  { label: 'AI 질문', icon: '🤖', to: '/chat', variant: 'chat' },
  { label: '키워드 검색', icon: '🔍', to: '/search', variant: 'keyword' },
]

export interface Notice {
  text: string
  date: string
}

export const notices: Notice[] = [
  { text: 'DB 2차 구축 데이터 업로드 완료', date: '2024.12.01' },
  { text: '양소유의 연애상담소 콘텐츠 추가', date: '2024.11.15' },
  { text: '서지적요소 클래스 속성 업데이트', date: '2024.10.28' },
  { text: '시스템 점검 안내 (완료)', date: '2024.10.10' },
]

export interface WorkChip {
  ko: string
  hanja: string
  unavailable?: boolean
}

export const worksEarly: WorkChip[] = [
  { ko: '온달전', hanja: '溫達傳' },
  { ko: '최치원', hanja: '崔致遠' },
  { ko: '김현감호', hanja: '金現感虎' },
  { ko: '이석단전', hanja: '李石端傳' },
  { ko: '안생', hanja: '安生' },
  { ko: '이생규장전', hanja: '李生窺墻傳' },
  { ko: '만복사저포기', hanja: '萬福寺樗蒲記' },
  { ko: '하생기우전', hanja: '何生奇遇傳' },
  { ko: '채생', hanja: '蔡生' },
  { ko: '월단단', hanja: '月團團' },
  { ko: '왕랑반혼전', hanja: '王郞返魂傳' },
  { ko: '남염부주지', hanja: '南炎浮洲志' },
  { ko: '용궁부연록', hanja: '龍宮赴宴錄' },
  { ko: '최생우진기', hanja: '崔生遇眞記' },
  { ko: '수향기', hanja: '水鄕記' },
  { ko: '설공찬전', hanja: '薛公瓚傳', unavailable: true },
  { ko: '조신', hanja: '調信' },
  { ko: '취유부벽정기', hanja: '醉遊浮碧亭記' },
  { ko: '노힐부득 달달박박', hanja: '努肹夫得 怛怛朴朴' },
  { ko: '공방전', hanja: '孔方傳' },
  { ko: '저생전', hanja: '楮生傳' },
  { ko: '국생전', hanja: '麴生傳' },
  { ko: '국선생전', hanja: '麴先生傳' },
  { ko: '청강사자현부전', hanja: '靑江使者玄夫傳' },
  { ko: '정시자전', hanja: '丁侍者傳' },
  { ko: '서재야회록', hanja: '書齋夜會錄' },
  { ko: '빙조자전', hanja: '氷操子傳' },
  { ko: '관처사묘지명', hanja: '管處士墓誌銘' },
  { ko: '화사', hanja: '花史' },
  { ko: '안빙몽유록', hanja: '安憑夢遊錄' },
  { ko: '원생몽유록', hanja: '元生夢遊錄' },
  { ko: '대관재기몽', hanja: '大觀齋記夢' },
  { ko: '오륜전전', hanja: '五倫全傳' },
]

export const worksMid: WorkChip[] = [
  { ko: '등생전', hanja: '鄧生傳' },
  { ko: '수표기우기', hanja: '水標奇遇記' },
  { ko: '숙진전', hanja: '淑眞傳' },
  { ko: '연랑전', hanja: '蓮娘傳' },
  { ko: '오로봉기', hanja: '五老峰記' },
  { ko: '왕시봉전', hanja: '王時鳳傳' },
  { ko: '이학사전', hanja: '李學士傳' },
  { ko: '왕시붕기우기', hanja: '王時鵬奇遇記' },
  { ko: '오후강전', hanja: '五虎將傳' },
  { ko: '일석화', hanja: '一夕話' },
  { ko: '숙향전', hanja: '淑香傳' },
  { ko: '광한루기', hanja: '廣寒樓記' },
  { ko: '고성기우기', hanja: '古城奇遇記' },
  { ko: '구운몽', hanja: '九雲夢' },
  { ko: '김전전', hanja: '金錢傳' },
  { ko: '낙동야언', hanja: '洛東野言' },
  { ko: '동선기', hanja: '洞仙記' },
  { ko: '난학몽', hanja: '鸞鶴夢' },
  { ko: '봉래신설', hanja: '蓬萊新說' },
  { ko: '왕경룡전', hanja: '王慶龍傳' },
  { ko: '유생전', hanja: '劉生傳' },
  { ko: '육미당기', hanja: '六美堂記' },
  { ko: '이화실전', hanja: '李花實傳' },
  { ko: '일락정기', hanja: '一樂亭記' },
  { ko: '편옥기우기', hanja: '片玉奇遇記' },
  { ko: '홍백화전', hanja: '紅白花傳' },
  { ko: '효열지', hanja: '孝烈誌' },
]

export interface Genre {
  ko: string
  hanja: string
  color: string
}

export const genres: Genre[] = [
  { ko: '가문류소설', hanja: '假文類小說', color: '#e67e22' },
  { ko: '가문소설', hanja: '家門小說', color: '#27ae60' },
  { ko: '몽유록', hanja: '夢遊錄', color: '#2980b9' },
  { ko: '실기소설', hanja: '實記小說', color: '#8e44ad' },
  { ko: '야담계소설', hanja: '野談系小說', color: '#c0392b' },
  { ko: '여협소설', hanja: '女俠小說', color: '#16a085' },
  { ko: '연의소설', hanja: '演義小說', color: '#d35400' },
  { ko: '우화소설', hanja: '寓話小說', color: '#2c3e50' },
  { ko: '이계소설', hanja: '異界小說', color: '#7f8c8d' },
  { ko: '재자가인소설', hanja: '才子佳人小說', color: '#e74c3c' },
  { ko: '전기소설', hanja: '傳奇小說', color: '#3498db' },
  { ko: '풍자골계소설', hanja: '諷刺滑稽小說', color: '#f39c12' },
  { ko: '희곡', hanja: '戲曲', color: '#9b59b6' },
]
