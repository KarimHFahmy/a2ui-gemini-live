"""Configuration loading.

`.env.example` tells developers to copy it to `.env`, so something has to
actually read that file — and it has to read it from wherever the process was
started, without ever shadowing what the deployment injects.
"""

from __future__ import annotations

import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from app.config import Settings

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND = REPO_ROOT / "backend"

PROBE = textwrap.dedent(
    """
    import sys
    sys.path.insert(0, {backend!r})
    from app.config import get_settings
    s = get_settings()
    print(s.project, s.voice_name, bool(s.dotenv_path), sep="|")
    """
)


def _probe(tmp_path: Path, cwd: Path, env: dict[str, str] | None = None) -> list[str]:
    """Runs a fresh interpreter so module-level `.env` loading is exercised."""
    script = tmp_path / "probe.py"
    script.write_text(PROBE.format(backend=str(BACKEND)))

    result = subprocess.run(
        [sys.executable, str(script)],
        cwd=cwd,
        capture_output=True,
        text=True,
        env={"PATH": "/usr/bin:/bin", "HOME": str(tmp_path), **(env or {})},
        check=True,
    )
    return result.stdout.strip().split("|")


@pytest.fixture
def dotenv(tmp_path: Path):
    """Writes a repo-root `.env` and removes it afterwards."""
    path = REPO_ROOT / ".env"
    if path.exists():
        pytest.skip("a real .env is present; not clobbering it")

    path.write_text(
        "GOOGLE_CLOUD_PROJECT=from-dotenv\nLIVE_VOICE_NAME=Charon\n", encoding="utf-8"
    )
    try:
        yield path
    finally:
        path.unlink(missing_ok=True)


def test_dotenv_is_found_from_the_repository_root(dotenv, tmp_path):
    project, voice, found = _probe(tmp_path, REPO_ROOT)

    assert found == "True"
    assert project == "from-dotenv"
    assert voice == "Charon"


def test_dotenv_is_found_from_the_backend_directory(dotenv, tmp_path):
    """`make dev-backend` starts uvicorn from `backend/`.

    A plain `load_dotenv()` reads `./.env` and would miss the file entirely
    here, which is the whole reason `find_dotenv` walks up.
    """
    project, _, found = _probe(tmp_path, BACKEND)

    assert found == "True"
    assert project == "from-dotenv"


def test_the_real_environment_wins_over_dotenv(dotenv, tmp_path):
    """A stray `.env` must never shadow what Cloud Run injects."""
    project, _, _ = _probe(
        tmp_path, REPO_ROOT, env={"GOOGLE_CLOUD_PROJECT": "from-real-env"}
    )

    assert project == "from-real-env"


def test_a_missing_dotenv_is_not_an_error(tmp_path):
    """The container has no `.env`; startup must not depend on one."""
    project, _, found = _probe(tmp_path, tmp_path)

    assert found == "False"
    assert project == ""


class TestValidation:
    def test_vertex_needs_a_project(self):
        settings = Settings(use_vertex_ai=True, project="", location="us-central1")
        assert any("GOOGLE_CLOUD_PROJECT" in problem for problem in settings.validate())

    def test_the_api_key_path_needs_a_key(self):
        settings = Settings(use_vertex_ai=False, api_key="")
        assert any("GOOGLE_API_KEY" in problem for problem in settings.validate())

    def test_a_complete_vertex_configuration_is_clean(self):
        settings = Settings(use_vertex_ai=True, project="demo", location="us-central1")
        assert settings.validate() == []


class TestAdkEnvironment:
    def test_vertex_settings_reach_adk(self, monkeypatch):
        """ADK builds its own client from these, not from constructor arguments."""
        for name in (
            "GOOGLE_GENAI_USE_VERTEXAI",
            "GOOGLE_CLOUD_PROJECT",
            "GOOGLE_CLOUD_LOCATION",
        ):
            monkeypatch.delenv(name, raising=False)

        Settings(use_vertex_ai=True, project="demo", location="europe-west4").apply_to_environment()

        import os

        assert os.environ["GOOGLE_GENAI_USE_VERTEXAI"] == "1"
        assert os.environ["GOOGLE_CLOUD_PROJECT"] == "demo"
        assert os.environ["GOOGLE_CLOUD_LOCATION"] == "europe-west4"

    def test_the_api_key_path_disables_vertex(self, monkeypatch):
        monkeypatch.delenv("GOOGLE_GENAI_USE_VERTEXAI", raising=False)
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

        Settings(use_vertex_ai=False, api_key="test-key").apply_to_environment()

        import os

        assert os.environ["GOOGLE_GENAI_USE_VERTEXAI"] == "0"
        assert os.environ["GOOGLE_API_KEY"] == "test-key"
