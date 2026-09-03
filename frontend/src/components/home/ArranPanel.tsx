/** 배열적요소 탭 패널 */
export function ArranPanel() {
  return (
    <>
      <div className="section-head">
        <h2>배열적요소</h2>
        <span className="eng">Content</span>
      </div>
      <p className="section-desc">
        작품 문맥의 구조적 골격을 형성하는 핵심 요소들
      </p>

      <div className="card-row">
        <div className="card card-grouped-teal card-clickable">
          <h4>
            장면 <em>Scene</em>
          </h4>
          <p>특정 장소에서 발생하는 최소 단위로서의 사건</p>
        </div>
        <div className="card card-grouped-blue card-clickable">
          <h4>
            등장인물 <em>Character</em>
          </h4>
          <p>작품·이본별 등장인물의 명칭·이칭과 구성 요소</p>
        </div>
      </div>

      <div className="card-row">
        <div className="card card-grouped-blue card-clickable">
          <h4>
            신분 <em>Caste</em>
          </h4>
          <p>작품 속에 등장하는 캐릭터의 신분과 지위</p>
        </div>
        <div className="card card-grouped-blue card-clickable">
          <h4>
            요소 <em>Char. Elements</em>
          </h4>
          <p>성별·존재계·실존성·유형을 조합한 인물 정보</p>
        </div>
      </div>

      <div className="card-row">
        <div className="card card-grouped-green card-clickable">
          <h4>
            개별 목차 <em>Episode</em>
          </h4>
          <p>회목·역사서 체제 등의 기술 체계 (개별 정보)</p>
        </div>
        <div className="card card-grouped-green card-clickable">
          <h4>
            대표 목차 <em>Number</em>
          </h4>
          <p>회목·역사서 체제 등의 기술 체계 (포괄 정보)</p>
        </div>
      </div>

      <div className="card-row">
        <div className="card card-grouped-yellow card-clickable">
          <h4>
            시대적 배경 <em>Background_E</em>
          </h4>
          <p>작품의 무대가 되는 시대적[왕조] 정보</p>
        </div>
        <div className="card card-grouped-yellow card-clickable">
          <h4>
            공간적 배경 <em>Background_L</em>
          </h4>
          <p>작품의 무대가 되는 차원적·지역적 권역</p>
        </div>
      </div>

      <div className="card-row">
        <div className="card card-grouped-yellow card-clickable">
          <h4>
            장소적 배경 <em>Background_W</em>
          </h4>
          <p>작품의 무대가 되는 경험적·실재적 권역</p>
        </div>
        <div className="card card-grouped-orange card-clickable">
          <h4>
            논평 <em>Comment</em>
          </h4>
          <p>작품 곳곳에 존재하는 여러 층위의 비평</p>
        </div>
      </div>

      <div className="card-row">
        <div className="card card-grouped-orange card-clickable">
          <h4>
            평비 <em>Remark</em>
          </h4>
          <p>넓은 의미의 평비본소설에서 발견되는 평비자의 비평</p>
        </div>
      </div>
    </>
  )
}
