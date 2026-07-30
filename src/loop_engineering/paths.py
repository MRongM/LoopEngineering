from pathlib import PurePosixPath


def normalized_relative(value: str) -> PurePosixPath:
    path = PurePosixPath(value.replace("\\", "/"))
    has_drive = bool(path.parts and path.parts[0].endswith(":"))
    unresolved = any(character in value for character in "*?[]{}$%~")
    if (
        path.is_absolute()
        or has_drive
        or ".." in path.parts
        or not path.parts
        or unresolved
    ):
        raise ValueError(f"unsafe relative path: {value}")
    return path


def normalized_allowed_boundary(value: str) -> PurePosixPath:
    normalized = value.replace("\\", "/")
    if normalized in {".", "./"}:
        return PurePosixPath(".")
    return normalized_relative(normalized.rstrip("/"))


def is_allowed_path(value: str, allowed_paths: list[str]) -> bool:
    try:
        candidate = normalized_relative(value)
    except ValueError:
        return False
    for allowed in allowed_paths:
        boundary = normalized_allowed_boundary(allowed)
        if boundary == PurePosixPath("."):
            return True
        if candidate == boundary or candidate.is_relative_to(boundary):
            return True
    return False
