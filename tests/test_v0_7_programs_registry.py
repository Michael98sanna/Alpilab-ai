"""V0.7: Programs UI uses existing executable tools only (no fake tools)."""

from __future__ import annotations

from app.tools.registry import default_tool_registry


def test_existing_executable_tools_unchanged() -> None:
    ids = {t.tool_id for t in default_tool_registry.list_executable()}
    assert "windows.3utools.open" in ids
    assert "windows.alpilab_check.open" in ids
    assert "alpilab_check.search_products" in ids
    assert "alpilab_check.get_product" in ids
    assert "demo.safe_test" in ids


def test_thermal_and_microscope_executable_tools_are_registered() -> None:
    ids = {t.tool_id for t in default_tool_registry.list_executable()}
    assert "windows.thermal_camera.open" in ids
    assert "windows.microscope.open" in ids
    assert "windows.zxw.open" not in ids
    assert "windows.borneo.open" not in ids


def test_soft_catalog_still_lists_lab_software_names() -> None:
    names = {t.name for t in default_tool_registry.list_tools()}
    assert "3uTools" in names
    assert "Alpilab Check" in names
    assert "Termocamera" in names
    assert "Microscopio" in names
