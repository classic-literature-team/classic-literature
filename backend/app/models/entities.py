"""한국고전소설DB 엔티티 모델.

각 엔티티 시트가 관계형 테이블이 되고, Edge 테이블이 엔티티 간의
다형적(polymorphic) 연결을 저장하는 그래프 구조.
따라서 Edge.source_id / target_id 에는 의도적으로 일반 외래키를 걸지 않는다.
"""

from __future__ import annotations

from sqlalchemy import Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class EntityMixin:
    """엔티티 시트들이 공유하는 공통 컬럼."""

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    name: Mapped[str | None] = mapped_column(Text, nullable=True)


class Book(EntityMixin, Base):
    __tablename__ = "book"

    designation: Mapped[str | None] = mapped_column(Text)
    cover_name_chi: Mapped[str | None] = mapped_column(Text)
    cover_name_kor: Mapped[str | None] = mapped_column(Text)
    title_name_chi: Mapped[str | None] = mapped_column(Text)
    title_name_kor: Mapped[str | None] = mapped_column(Text)
    division: Mapped[str | None] = mapped_column(String(16))
    institution_kor: Mapped[str | None] = mapped_column(Text)
    institution_chi: Mapped[str | None] = mapped_column(Text)
    setting_type: Mapped[str | None] = mapped_column(String(64))
    volume_type: Mapped[str | None] = mapped_column(String(16))
    etc: Mapped[str | None] = mapped_column(Text)
    pb_edition_status: Mapped[str | None] = mapped_column(String(16))
    contents_type: Mapped[str | None] = mapped_column(String(32))
    contents_information: Mapped[str | None] = mapped_column(Text)
    date_statement: Mapped[str | None] = mapped_column(Text)
    comments: Mapped[str | None] = mapped_column(Text)


class AbstractWork(EntityMixin, Base):
    __tablename__ = "abstract_work"

    designation: Mapped[str | None] = mapped_column(Text)
    title_name_chi: Mapped[str | None] = mapped_column(Text)
    title_name_kor: Mapped[str | None] = mapped_column(Text)
    title_name_alter: Mapped[str | None] = mapped_column(Text)
    pb_edition_status: Mapped[str | None] = mapped_column(String(16))
    hangul_edition_status: Mapped[str | None] = mapped_column(String(16))
    numbered_sections_status: Mapped[str | None] = mapped_column(String(16))
    contents_type: Mapped[str | None] = mapped_column(String(64))
    creation_period: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)


class WorksCompilation(EntityMixin, Base):
    __tablename__ = "works_compilation"

    type: Mapped[str | None] = mapped_column(String(32))
    designation: Mapped[str | None] = mapped_column(Text)
    cover_name_chi: Mapped[str | None] = mapped_column(Text)
    cover_name_kor: Mapped[str | None] = mapped_column(Text)
    title_name_chi: Mapped[str | None] = mapped_column(Text)
    title_name_kor: Mapped[str | None] = mapped_column(Text)
    division: Mapped[str | None] = mapped_column(String(16))
    institution_kor: Mapped[str | None] = mapped_column(Text)
    institution_chi: Mapped[str | None] = mapped_column(Text)
    setting_type: Mapped[str | None] = mapped_column(String(64))
    included_work: Mapped[str | None] = mapped_column(Text)
    etc: Mapped[str | None] = mapped_column(Text)
    published_year: Mapped[str | None] = mapped_column(Text)
    related_discussion: Mapped[str | None] = mapped_column(Text)


class Scene(EntityMixin, Base):
    __tablename__ = "scene"

    work_kor: Mapped[str | None] = mapped_column(Text)
    work_chi: Mapped[str | None] = mapped_column(Text)
    viewpoint: Mapped[str | None] = mapped_column(String(32))
    language: Mapped[str | None] = mapped_column(String(32))
    original_text: Mapped[str | None] = mapped_column(Text)
    translation: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    temporal_background: Mapped[str | None] = mapped_column(Text)
    spatial_background_1: Mapped[str | None] = mapped_column(Text)
    spatial_background_2: Mapped[str | None] = mapped_column(Text)
    place_background: Mapped[str | None] = mapped_column(Text)
    characters: Mapped[str | None] = mapped_column(Text)
    allusions: Mapped[str | None] = mapped_column(Text)
    spatial_background_link: Mapped[str | None] = mapped_column(Text)
    place_background_link: Mapped[str | None] = mapped_column(Text)
    character_link: Mapped[str | None] = mapped_column(Text)
    allusion_link: Mapped[str | None] = mapped_column(Text)
    embedded_work_status: Mapped[str | None] = mapped_column(String(16))


class EmbeddedWork(EntityMixin, Base):
    __tablename__ = "embedded_work"

    work_kor: Mapped[str | None] = mapped_column(Text)
    work_chi: Mapped[str | None] = mapped_column(Text)
    ew_title: Mapped[str | None] = mapped_column(Text)
    ew_type: Mapped[str | None] = mapped_column(String(64))
    ew_genre: Mapped[str | None] = mapped_column(String(64))
    language: Mapped[str | None] = mapped_column(String(32))
    original_text: Mapped[str | None] = mapped_column(Text)
    translation: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)


class Allusion(EntityMixin, Base):
    __tablename__ = "allusion"

    citation_type: Mapped[str | None] = mapped_column(String(64))
    title_chi: Mapped[str | None] = mapped_column(Text)
    title_kor: Mapped[str | None] = mapped_column(Text)
    work_chi: Mapped[str | None] = mapped_column(Text)
    work_kor: Mapped[str | None] = mapped_column(Text)
    allusion_type: Mapped[str | None] = mapped_column(String(64))
    explain: Mapped[str | None] = mapped_column(Text)
    original_text: Mapped[str | None] = mapped_column(Text)
    translation: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    source_work: Mapped[str | None] = mapped_column(Text)


class Remark(EntityMixin, Base):
    __tablename__ = "remark"

    type: Mapped[str | None] = mapped_column(String(64))
    reviewer: Mapped[str | None] = mapped_column(Text)
    work_kor: Mapped[str | None] = mapped_column(Text)
    work_chi: Mapped[str | None] = mapped_column(Text)
    target_book: Mapped[str | None] = mapped_column(Text)
    original_text: Mapped[str | None] = mapped_column(Text)
    translation: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)


class Comment(EntityMixin, Base):
    __tablename__ = "comment"

    c_type: Mapped[str | None] = mapped_column(String(64))
    work_kor: Mapped[str | None] = mapped_column(Text)
    work_chi: Mapped[str | None] = mapped_column(Text)
    target_book: Mapped[str | None] = mapped_column(Text)
    original_text: Mapped[str | None] = mapped_column(Text)
    translation: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)


class Review(EntityMixin, Base):
    __tablename__ = "review"

    work_kor: Mapped[str | None] = mapped_column(Text)
    work_chi: Mapped[str | None] = mapped_column(Text)
    target_book: Mapped[str | None] = mapped_column(Text)
    reviewer: Mapped[str | None] = mapped_column(Text)
    criticism_type: Mapped[str | None] = mapped_column(String(64))
    paratext_title: Mapped[str | None] = mapped_column(Text)
    language: Mapped[str | None] = mapped_column(String(32))
    original_text: Mapped[str | None] = mapped_column(Text)
    translation: Mapped[str | None] = mapped_column(Text)
    mentioned_work: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    location: Mapped[str | None] = mapped_column(Text)


class RelatedWork(EntityMixin, Base):
    __tablename__ = "related_work"

    work_kor: Mapped[str | None] = mapped_column(Text)
    work_chi: Mapped[str | None] = mapped_column(Text)
    writer: Mapped[str | None] = mapped_column(Text)
    record: Mapped[str | None] = mapped_column(Text)
    rw_title: Mapped[str | None] = mapped_column(Text)
    name_kor: Mapped[str | None] = mapped_column(Text)
    name_chi: Mapped[str | None] = mapped_column(Text)
    genre: Mapped[str | None] = mapped_column(String(64))
    language: Mapped[str | None] = mapped_column(String(32))
    original_text: Mapped[str | None] = mapped_column(Text)
    translation: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)


class Character(EntityMixin, Base):
    __tablename__ = "character"

    work_kor: Mapped[str | None] = mapped_column(Text)
    work_chi: Mapped[str | None] = mapped_column(Text)
    ch_name_kor: Mapped[str | None] = mapped_column(Text)
    ch_name_chi: Mapped[str | None] = mapped_column(Text)
    nickname: Mapped[str | None] = mapped_column(Text)
    primary_classification: Mapped[str | None] = mapped_column(Text)
    secondary_classification: Mapped[str | None] = mapped_column(Text)
    comments: Mapped[str | None] = mapped_column(Text)
    gender: Mapped[str | None] = mapped_column(String(32))
    existence: Mapped[str | None] = mapped_column(String(32))
    facticity: Mapped[str | None] = mapped_column(String(32))
    attribute_type: Mapped[str | None] = mapped_column(String(64))


class Caste(EntityMixin, Base):
    __tablename__ = "caste"

    f_classification: Mapped[str | None] = mapped_column(Text)
    s_classification: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)


class ChElements(EntityMixin, Base):
    __tablename__ = "ch_elements"

    gender: Mapped[str | None] = mapped_column(String(32))
    existence: Mapped[str | None] = mapped_column(String(32))
    facticity: Mapped[str | None] = mapped_column(String(32))
    type: Mapped[str | None] = mapped_column(String(64))
    notes: Mapped[str | None] = mapped_column(Text)


class BackgroundE(EntityMixin, Base):
    __tablename__ = "background_e"

    nation_eng: Mapped[str | None] = mapped_column(Text)
    nation_kor: Mapped[str | None] = mapped_column(Text)
    dynasty_chi: Mapped[str | None] = mapped_column(Text)
    dynasty_kor: Mapped[str | None] = mapped_column(Text)
    ruler_chi: Mapped[str | None] = mapped_column(Text)
    ruler_kor: Mapped[str | None] = mapped_column(Text)
    historicity: Mapped[str | None] = mapped_column(String(16))
    source_work: Mapped[str | None] = mapped_column(Text)


class BackgroundL(EntityMixin, Base):
    __tablename__ = "background_l"

    stage_type: Mapped[str | None] = mapped_column(String(64))
    nation_chi: Mapped[str | None] = mapped_column(Text)
    nation_kor: Mapped[str | None] = mapped_column(Text)
    nation_eng: Mapped[str | None] = mapped_column(Text)
    province_chi: Mapped[str | None] = mapped_column(Text)
    province_kor: Mapped[str | None] = mapped_column(Text)
    landmark_chi: Mapped[str | None] = mapped_column(Text)
    landmark_kor: Mapped[str | None] = mapped_column(Text)
    # 좌표가 숫자가 아니라 플레이스홀더일 수 있어 문자열로 둔다.
    latitude: Mapped[str | None] = mapped_column(String(64))
    longitude: Mapped[str | None] = mapped_column(String(64))
    notes: Mapped[str | None] = mapped_column(Text)


class BackgroundW(EntityMixin, Base):
    __tablename__ = "background_w"

    stage_type: Mapped[str | None] = mapped_column(String(64))
    whereabouts_chi: Mapped[str | None] = mapped_column(Text)
    whereabouts_kor: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)


class Number(EntityMixin, Base):
    __tablename__ = "number"

    n_title: Mapped[str | None] = mapped_column(Text)
    target_book: Mapped[str | None] = mapped_column(Text)
    con_type: Mapped[str | None] = mapped_column(String(64))
    con_information: Mapped[str | None] = mapped_column(Text)
    line_count: Mapped[str | None] = mapped_column(String(32))
    word_count: Mapped[str | None] = mapped_column(String(32))
    notes: Mapped[str | None] = mapped_column(Text)


class Episode(EntityMixin, Base):
    __tablename__ = "episode"

    t_title: Mapped[str | None] = mapped_column(Text)
    target_book: Mapped[str | None] = mapped_column(Text)
    line_count: Mapped[str | None] = mapped_column(String(32))
    word_count: Mapped[str | None] = mapped_column(String(32))
    episode: Mapped[str | None] = mapped_column(String(32))
    original_text: Mapped[str | None] = mapped_column(Text)
    translation: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)


class Participant(EntityMixin, Base):
    __tablename__ = "participant"

    role_type: Mapped[str | None] = mapped_column(String(64))
    unknown_status: Mapped[str | None] = mapped_column(String(64))
    name_chi: Mapped[str | None] = mapped_column(Text)
    name_kor: Mapped[str | None] = mapped_column(Text)
    nationality: Mapped[str | None] = mapped_column(Text)
    # 숫자와 '[未詳]' 같은 플레이스홀더가 섞여 있어 문자열로 둔다.
    birth_year: Mapped[str | None] = mapped_column(String(32))
    death_year: Mapped[str | None] = mapped_column(String(32))
    courtesy_name: Mapped[str | None] = mapped_column(Text)
    pen_name: Mapped[str | None] = mapped_column(Text)
    related_works: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)


class SideDot(EntityMixin, Base):
    __tablename__ = "side_dot"

    n_title: Mapped[str | None] = mapped_column(Text)
    target_book: Mapped[str | None] = mapped_column(Text)
    original_text: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)


class Edge(Base):
    """임의의 두 엔티티 레코드를 잇는 그래프 엣지."""

    __tablename__ = "edge"

    __table_args__ = (
        UniqueConstraint(
            "source_class",
            "source_id",
            "target_class",
            "target_id",
            "relation",
            name="uq_edge_connection",
        ),
        Index("ix_edge_source", "source_class", "source_id"),
        Index("ix_edge_target", "target_class", "target_id"),
        Index("ix_edge_relation", "relation"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_class: Mapped[str] = mapped_column(String(64), nullable=False)
    source_id: Mapped[str] = mapped_column(String(128), nullable=False)
    source_name: Mapped[str | None] = mapped_column(Text)
    target_class: Mapped[str] = mapped_column(String(64), nullable=False)
    target_id: Mapped[str] = mapped_column(String(128), nullable=False)
    target_name: Mapped[str | None] = mapped_column(Text)
    relation: Mapped[str | None] = mapped_column(String(64))
    etc1: Mapped[str | None] = mapped_column(Text)
    etc2: Mapped[str | None] = mapped_column(Text)
