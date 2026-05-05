"""Tests for ``openayane.toml`` configuration loading (Phase 5 P5-2)."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from openayane_rde.config import load_openayane_config, normalize_config_paths


def test_load_empty_file_uses_defaults(tmp_path: Path) -> None:
    p = tmp_path / "openayane.toml"
    p.write_text("", encoding="utf-8")
    cfg = load_openayane_config(p)
    assert cfg.profile.name == "local-dev"
    assert cfg.runtime.allow_subprocess_execution is False
    assert cfg.audit.append is True
    assert cfg.relation_store.backend == "json"


def test_load_partial_merges_defaults(tmp_path: Path) -> None:
    p = tmp_path / "openayane.toml"
    p.write_text(
        '[profile]\nname = "ci"\n',
        encoding="utf-8",
    )
    cfg = load_openayane_config(p)
    assert cfg.profile.name == "ci"
    assert cfg.profile.mode == "internal-pilot"
    assert cfg.policy.halt_on_critical_risk is True


def test_invalid_backend_rejected(tmp_path: Path) -> None:
    p = tmp_path / "openayane.toml"
    p.write_text(
        '[relation_store]\nbackend = "postgres"\n',
        encoding="utf-8",
    )
    with pytest.raises(ValidationError):
        load_openayane_config(p)


def test_invalid_max_output_bytes_rejected(tmp_path: Path) -> None:
    p = tmp_path / "openayane.toml"
    p.write_text(
        "[runtime]\nmax_output_bytes = 0\n",
        encoding="utf-8",
    )
    with pytest.raises(ValidationError):
        load_openayane_config(p)


def test_invalid_toml_syntax(tmp_path: Path) -> None:
    p = tmp_path / "openayane.toml"
    p.write_text("not toml {{{\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Invalid TOML"):
        load_openayane_config(p)


def test_extra_top_level_key_rejected(tmp_path: Path) -> None:
    p = tmp_path / "openayane.toml"
    p.write_text(
        "[unknown]\nx = 1\n",
        encoding="utf-8",
    )
    with pytest.raises(ValidationError):
        load_openayane_config(p)


def test_normalize_paths_relative_to_config_file(tmp_path: Path) -> None:
    sub = tmp_path / "proj"
    sub.mkdir()
    p = sub / "openayane.toml"
    p.write_text(
        '[audit]\npath = "logs/a.jsonl"\n'
        '[runtime]\nworkspace_root = "ws"\n'
        '[institution]\nrules_path = "r.json"\nauthority_path = "a.json"\n',
        encoding="utf-8",
    )
    cfg = load_openayane_config(p)
    norm = normalize_config_paths(cfg, p)
    assert Path(norm.audit.path).is_absolute()
    assert Path(norm.audit.path) == (sub / "logs" / "a.jsonl").resolve()
    assert Path(norm.runtime.workspace_root) == (sub / "ws").resolve()
    assert Path(norm.institution.rules_path) == (sub / "r.json").resolve()


def test_normalize_preserves_absolute_paths(tmp_path: Path) -> None:
    abs_audit = tmp_path / "abs.jsonl"
    abs_audit.write_text("", encoding="utf-8")
    p = tmp_path / "openayane.toml"
    p.write_text(f'[audit]\npath = "{abs_audit.as_posix()}"\n', encoding="utf-8")
    cfg = load_openayane_config(p)
    norm = normalize_config_paths(cfg, p)
    assert Path(norm.audit.path) == abs_audit.resolve()
