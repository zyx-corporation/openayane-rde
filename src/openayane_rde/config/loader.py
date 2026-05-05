"""Load and normalize ``openayane.toml``."""

from __future__ import annotations

import tomllib
from pathlib import Path

from openayane_rde.config.schema import OpenAyaneConfig


def load_openayane_config(path: Path | str) -> OpenAyaneConfig:
    """Parse TOML from ``path`` and validate as :class:`OpenAyaneConfig`.

    An empty file is treated as an empty document (all defaults).
    """
    p = Path(path)
    raw = p.read_text(encoding="utf-8").strip()
    if not raw:
        data: dict[str, object] = {}
    else:
        try:
            data = tomllib.loads(raw)
        except tomllib.TOMLDecodeError as exc:
            msg = f"Invalid TOML in {p}: {exc}"
            raise ValueError(msg) from exc
    return OpenAyaneConfig.model_validate(data)


def normalize_config_paths(config: OpenAyaneConfig, config_file: Path | str) -> OpenAyaneConfig:
    """Return a copy with path-like fields resolved to absolute strings.

    Relative paths are resolved against the parent directory of ``config_file``.
    """
    base = Path(config_file).resolve().parent

    def res(s: str) -> str:
        pp = Path(s)
        out = pp if pp.is_absolute() else base / pp
        return str(out.resolve())

    return config.model_copy(
        update={
            "audit": config.audit.model_copy(update={"path": res(config.audit.path)}),
            "relation_store": config.relation_store.model_copy(
                update={"path": res(config.relation_store.path)}
            ),
            "runtime": config.runtime.model_copy(
                update={"workspace_root": res(config.runtime.workspace_root)}
            ),
            "institution": config.institution.model_copy(
                update={
                    "rules_path": res(config.institution.rules_path),
                    "authority_path": res(config.institution.authority_path),
                }
            ),
        }
    )
