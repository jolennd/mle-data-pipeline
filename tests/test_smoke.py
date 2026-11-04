import importlib


def test_package_imports():
    """Proves the package is importable and pytest finds src/ (the pythonpath setting)."""
    importlib.import_module("data_pipeline.config")
