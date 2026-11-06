"""Lightweight checks for repository metadata and integration layout."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INTEGRATION = ROOT / "custom_components" / "airos_xs2_http"


def test_manifest_matches_integration_domain():
    manifest = json.loads((INTEGRATION / "manifest.json").read_text())
    assert manifest["domain"] == INTEGRATION.name
    assert manifest["version"]
    for key in ("name", "documentation", "issue_tracker", "codeowners", "iot_class"):
        assert key in manifest


def test_marketplace_metadata():
    hacs = json.loads((ROOT / "hacs.json").read_text())
    assert hacs["name"]
    # Marketplace renders the repository README itself; render_readme was
    # a legacy HACS setting and is intentionally no longer required.
    assert "render_readme" not in hacs


def test_config_flow_translation_exists():
    translations = json.loads((INTEGRATION / "translations" / "en.json").read_text())
    assert "config" in translations
    assert "user" in translations["config"]["step"]
