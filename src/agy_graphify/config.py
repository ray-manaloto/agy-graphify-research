"""Graphify configuration manager handling ~/.graphify/config.json."""

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .logger import logger


SUPPORTED_COLIBRI_MODELS = [
    "glm-5.2",
    "inkling",
    "kimi-k3",
    "deepseek-v4-flash",
    "olmoe-7b",
]


@dataclass
class ColibriConfig:
    """Settings for the local Colibri LLM inference engine."""

    server_url: str = "http://127.0.0.1:8080/v1"
    model_name: str = "deepseek-v4-flash"
    model_path: str = ""
    binary_path: str = ""
    server_script: str = ""
    context_length: int = 8192
    max_queue: int = 8
    auto_launch: bool = True


@dataclass
class GraphifyConfig:
    """Global Graphify system configuration."""

    active_llm_assistant: str = "colibri"
    colibri: ColibriConfig = field(default_factory=ColibriConfig)
    global_memory_dir: str = "~/.graphify/global_memory"

    @classmethod
    def get_config_path(cls) -> Path:
        """Return the default configuration path ~/.graphify/config.json."""
        return Path.home() / ".graphify" / "config.json"

    @classmethod
    def load(cls, config_path: Path | None = None) -> "GraphifyConfig":
        """Load configuration from disk or create default."""
        path = config_path or cls.get_config_path()
        if not path.is_file():
            cfg = cls()
            cfg.save(path)
            return cfg

        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            colibri_dict = raw.get("colibri", {})
            colibri_cfg = ColibriConfig(**colibri_dict) if colibri_dict else ColibriConfig()

            return cls(
                active_llm_assistant=raw.get("active_llm_assistant", "colibri"),
                colibri=colibri_cfg,
                global_memory_dir=raw.get("global_memory_dir", "~/.graphify/global_memory"),
            )
        except Exception as err:
            logger.warning(f"Failed to load config from {path}: {err}. Returning defaults.")
            return cls()

    def save(self, config_path: Path | None = None) -> Path:
        """Persist configuration to disk."""
        path = config_path or self.get_config_path()
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            data = asdict(self)
            path.write_text(json.dumps(data, indent=2), encoding="utf-8")
            logger.info(f"Graphify configuration saved to {path}")
        except Exception as err:
            logger.warning(f"Could not save config to {path}: {err}")
        return path
