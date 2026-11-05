import os


def require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise ValueError(f"{name} is not set")
    return value


def source_base_url() -> str:
    return require_env("SOURCE_BASE_URL").rstrip("/")


def source_file_pattern() -> str:
    return require_env("SOURCE_FILE_PATTERN")


def partitions() -> list[str]:
    return [p.strip() for p in require_env("PARTITIONS").split(",") if p.strip()]


def staging_dir() -> str:
    return require_env("STAGING_DIR")


def processed_dir() -> str:
    return require_env("PROCESSED_DIR")
