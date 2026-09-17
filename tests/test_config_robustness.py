"""Tests for config loading robustness (corrupt/wrong-typed profile values)."""

from dwm_cli.config import settings


def test_load_config_coerces_bad_types(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(settings, "CURRENT_PROFILE_FILE", tmp_path / ".current")

    settings._create_default_profile()
    settings.save_config(
        {"opacity": "oops", "scale": 3, "font_size": "x", "font": 12345},
        "default",
    )

    config = settings.load_config("default")
    assert config["opacity"] == 0.5  # invalid -> default
    assert config["scale"] == 3.0  # valid -> float
    assert config["font_size"] == 36  # invalid -> default
    assert config["font"] == "12345"  # non-string -> coerced, no crash