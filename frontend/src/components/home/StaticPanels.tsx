/** 정적 콘텐츠 탭 패널들 (소개/서지/참여/배열/표현) */

export function IntroPanel() {
  return (
    <>
      <div className="section-head">
        <h2>DB소개</h2>
        <span className="eng">Overview</span>
      </div>
      <div className="card-row">
        <div className="card">
          <h4>개요</h4>
          <p>
            온톨로지(Ontology) 기반 시맨틱 데이터 모델. 한국한문소설 및 유관
            비평 자료의 구성 요소를 체계적으로 구조화한 그래프 데이터베이스.
          </p>
        </div>
        <div className="card">
          <h4>구조</h4>
          <p>
            외부 정보(서지적·참여적 요소)와 내부 정보(배열적·표현적 요소)로
            대별. 총 20건 클래스, 42건 관계 표현, 약 190여 건 속성으로 구성.
          </p>
        </div>
      </div>
      <div className="card-row">
        <div className="card">
          <h4>목적</h4>
          <p>
            파편화·독점화·편중화를 타개하고, 작품의 구성 요소·자료적 특징·유관
            비평을 능동적으로 활용할 수 있는 학술 환경 조성.
          </p>
        </div>
        <div className="card">
          <h4>활용</h4>
          <p>
            학술 연구, 디지털 인문학 교육, 한국 고전 문학의 체계적 보존 및
            대중적 접근성 향상을 위한 기반 인프라.
          </p>
        </div>
      </div>
      <div className="more-btn-wrap">
        <button type="button" className="more-btn">
          더보기 →
        </button>
      </div>
    </>
  )
}

export function BiblioPanel() {
  return (
    <>
      <div className="section-head">
        <h2>서지적요소</h2>
        <span className="eng">Bibliographic</span>
      </div>
      <p className="section-desc">
        문헌의 서지 정보 및 자료를 제작·유통한 사람과 관련한 정보
      </p>
      <div className="card-row">
        <div className="card card-grouped-brown card-clickable">
          <h4>
            이본 <em>Manuscript</em>
          </h4>
          <p>기준본에 대한 서지 사항으로 제목·소장처·형태·연대 등의 정보</p>
        </div>
        <div className="card card-grouped-brown card-clickable">
          <h4>
            작품집 <em>Works Compilation</em>
          </h4>
          <p>작품집에 대한 서지 사항으로 제목·수록 작품 등의 정보</p>
        </div>
      </div>
      <div className="card-row">
        <div className="card card-grouped-brown card-clickable">
          <h4>
            인물 <em>Participant</em>
          </h4>
          <p>작품을 직접 창작했거나 복본의 제작 및 편집·향유를 담당한 사람</p>
        </div>
        <div className="card card-other card-clickable">
          <h4>
            작품(기타 요소) <em>Abstract Work</em>
          </h4>
          <p>
            비실재적 개념 작품 정보. 작품명·이칭·평비본여부·한글본여부·회목여부.
          </p>
        </div>
      </div>
    </>
  )
}

export function PartiPanel() {
  return (
    <>
      <div className="section-head">
        <h2>참여적요소</h2>
        <span className="eng">Participatory</span>
      </div>
      <p className="section-desc">
        이본 및 유관 자료 등에서 확인되는 향유 양상들
      </p>
      <div className="card-row">
        <div className="card card-grouped-brown card-clickable">
          <h4>
            비점 <em>SideDot</em>
          </h4>
          <p>작품 본문 근처에 권(圈)·점(點)·선(線) 등의 형태로 표시한 반응</p>
        </div>
        <div className="card card-grouped-purple card-clickable">
          <h4>
            외평 <em>Review</em>
          </h4>
          <p>이본에서 발견되는 감상·해석·논평 성격의 서발·독법·범례·부기사항</p>
        </div>
      </div>
      <div className="card-row">
        <div className="card card-grouped-blue card-clickable">
          <h4>
            연관 작품 <em>Related Work</em>
          </h4>
          <p>소설의 향유·창작·전파등과 관련해 문인들이 남긴 시문</p>
        </div>
      </div>
    </>
  )
}

export function ExprePanel() {
  return (
    <>
      <div className="section-head">
        <h2>표현적요소</h2>
        <span className="eng">Expressive</span>
      </div>
      <p className="section-desc">본문의 제시 방식과 표현 전략</p>
      <div className="card-row col-2">
        <div className="card card-grouped-indigo card-clickable">
          <h4>
            전고 <em>Allusion</em>
          </h4>
          <p>
            어전(語典)·사전(事典)으로 차용 맥락 분류. 문헌 유형은
            경(A)·사(B)·자(C)·집(D)·도(E)·불(F)·기타(G)로 대별.
          </p>
        </div>
        <div className="card card-grouped-coral card-clickable">
          <h4>
            소작품(개별 시문) <em>Embedded Work</em>
          </h4>
          <p>작품 안에 문체로서 독립화가 가능한 소작품. 운문-산문으로 대별</p>
        </div>
      </div>
      <div className="info-note">
        시점(1·3인칭)과 표기 언어(한문·국한문·이두·백화)는 독립 클래스가 아닌{' '}
        <strong>장면(Scene)</strong>의 속성으로 관리됩니다.
      </div>
    </>
  )
}
