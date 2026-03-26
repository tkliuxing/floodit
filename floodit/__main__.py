import sys
from pathlib import Path

# 直接执行 (python floodit/__main__.py 或 uv run floodit) 时
# __package__ 为 None，需手动将项目根目录加入 sys.path
if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    __package__ = "floodit"  # noqa: A001

import pygame as pg

from .floodit import Floodit


def main():
    pg.init()
    fi = Floodit()
    fi.show()
    fi.mainloop()


if __name__ == "__main__":
    main()
