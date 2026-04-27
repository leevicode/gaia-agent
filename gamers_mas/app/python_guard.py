import sys

REQUIRED_MAJOR = 3
REQUIRED_MINOR = 12


def enforce_python_312() -> None:
    current = sys.version_info[:2]
    required = (REQUIRED_MAJOR, REQUIRED_MINOR)
    if current != required:
        raise RuntimeError(
            "This project requires Python 3.12.x only. "
            f"Current interpreter: {sys.version.split()[0]}"
        )
