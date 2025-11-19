r"""Write example altitude/speed/autopilot files next to the dashboard.

Run this when the dashboard warns that the text files are missing. It
creates three small files with sensible defaults so the Streamlit app
displays values immediately.

Usage (PowerShell):
    cd "C:/Users/seeke/OneDrive/Desktop/voice command based aircraft"
    python populate_example_files.py
"""
from __future__ import annotations
import os
from pathlib import Path


def write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def main() -> None:
    base = Path(__file__).resolve().parent
    files = {
        "altitude.txt": "15000",
        "speed.txt": "450",
        "autopilot.txt": "OFF",
    }

    created = []
    for name, value in files.items():
        p = base / name
        write(p, value)
        created.append((p, value))

    print("Wrote example files:")
    for p, v in created:
        print(f" - {p} -> {v}")


if __name__ == "__main__":
    main()
