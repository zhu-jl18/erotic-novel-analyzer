from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class NovelInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    world_setting: str = Field(min_length=1)
    world_tags: list[str] = Field(default_factory=list)
    chapter_count: int = Field(ge=0)
    is_completed: bool
    completion_note: str = ""


class MetaOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    novel_info: NovelInfo
    summary: str = Field(min_length=1)


class Character(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    gender: Literal["male", "female"]
    identity: str = Field(min_length=1)
    personality: str = Field(min_length=1)
    sexual_preferences: str = Field(min_length=1)

    lewdness_score: int | None = Field(default=None, ge=1, le=100)
    lewdness_analysis: str | None = None

    @model_validator(mode="after")
    def _female_requires_lewdness(self) -> "Character":
        if self.gender == "female":
            if self.lewdness_score is None:
                raise ValueError("female character missing lewdness_score")
            if not (self.lewdness_analysis or "").strip():
                raise ValueError("female character missing lewdness_analysis")
        return self


class Relationship(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    from_: str = Field(alias="from", min_length=1)
    to: str = Field(min_length=1)
    type: str = Field(min_length=1)
    start_way: str = Field(min_length=1)
    description: str = Field(min_length=1)


class CoreOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    characters: list[Character] = Field(default_factory=list)
    relationships: list[Relationship] = Field(default_factory=list)


class SceneEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    participants: list[str] = Field(default_factory=list)
    chapter: str = Field(min_length=1)
    location: str = Field(min_length=1)
    description: str = Field(min_length=1)


class SexScenes(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total_count: int = Field(ge=0)
    scenes: list[SceneEntry] = Field(default_factory=list)


class EvolutionEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    chapter: str = Field(min_length=1)
    stage: str = Field(min_length=1)
    description: str = Field(min_length=1)


class ScenesOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    first_sex_scenes: list[SceneEntry] = Field(default_factory=list)
    sex_scenes: SexScenes
    evolution: list[EvolutionEntry] = Field(default_factory=list)


class ThunderzoneEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: str = Field(min_length=1)
    severity: Literal["高", "中", "低"]
    description: str = Field(min_length=1)
    involved_characters: list[str] = Field(default_factory=list)
    chapter_location: str = ""
    relationship_context: str = ""


class ThunderOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    thunderzones: list[ThunderzoneEntry] = Field(default_factory=list)
    thunderzone_summary: str = Field(min_length=1)
