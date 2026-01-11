from __future__ import annotations

from .schemas import CoreOutput, LewdElementsOutput, ScenesOutput, ThunderOutput


def validate_core_consistency(core: CoreOutput) -> list[str]:
    errors: list[str] = []

    if not core.characters:
        errors.append("characters 为空")
        return errors

    names = {c.name for c in core.characters}

    for idx, rel in enumerate(core.relationships):
        if rel.from_ not in names:
            errors.append(f"relationships[{idx}].from 不在角色表: {rel.from_}")
        if rel.to not in names:
            errors.append(f"relationships[{idx}].to 不在角色表: {rel.to}")

    return errors


def validate_scenes_consistency(scenes: ScenesOutput, allowed_names: set[str]) -> list[str]:
    errors: list[str] = []

    def check_participants(items, ctx: str) -> None:
        for i, s in enumerate(items):
            if not s.participants:
                errors.append(f"{ctx}[{i}].participants 为空")
                continue
            for p in s.participants:
                if p not in allowed_names:
                    errors.append(f"{ctx}[{i}] 参与者不在角色表: {p}")

    check_participants(scenes.first_sex_scenes, "first_sex_scenes")
    check_participants(scenes.sex_scenes.scenes, "sex_scenes.scenes")

    if scenes.sex_scenes.total_count < len(scenes.sex_scenes.scenes):
        errors.append("sex_scenes.total_count 小于 scenes 数量")

    return errors


def validate_thunder_consistency(thunder: ThunderOutput, allowed_names: set[str]) -> list[str]:
    errors: list[str] = []

    for idx, tz in enumerate(thunder.thunderzones):
        if not tz.involved_characters:
            errors.append(f"thunderzones[{idx}].involved_characters 为空")
            continue
        for p in tz.involved_characters:
            if p not in allowed_names:
                errors.append(f"thunderzones[{idx}] 角色不在角色表: {p}")

    return errors


def validate_lewd_elements_consistency(lewd: LewdElementsOutput, allowed_names: set[str]) -> list[str]:
    errors: list[str] = []

    seen_types: set[str] = set()
    for idx, item in enumerate(lewd.lewd_elements):
        t = item.type
        if t in seen_types:
            errors.append(f"lewd_elements[{idx}].type 重复: {t}")
        else:
            seen_types.add(t)

        for p in item.involved_characters:
            if p not in allowed_names:
                errors.append(f"lewd_elements[{idx}] 角色不在角色表: {p}")

    return errors

