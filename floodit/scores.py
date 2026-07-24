"""最佳成绩（通关最少步数）的读写，按难度分别记录。

存到用户数据目录下的一个 JSON 文件。一切 IO 都是尽力而为：任何异常都不该
打断游戏——读失败当作没有记录，写失败静默忽略，脏数据一律丢弃。
"""

import json
import os
import sys
from pathlib import Path

APP_NAME = "floodit"
FILENAME = "scores.json"


def default_dir() -> Path:
    """按平台返回存放数据的目录。"""
    if sys.platform.startswith("win"):
        base = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
    elif sys.platform == "darwin":
        base = str(Path.home() / "Library" / "Application Support")
    else:
        base = os.environ.get("XDG_DATA_HOME") or str(Path.home() / ".local" / "share")
    return Path(base) / APP_NAME


def default_path() -> Path:
    return default_dir() / FILENAME


class BestScores:
    """按难度记录通关最少步数，读写自动落盘。"""

    def __init__(self, path=None):
        self.path = Path(path) if path is not None else default_path()
        self._best = self._load()

    def _load(self) -> dict:
        try:
            with open(self.path, encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, ValueError):
            return {}
        # 只接受 {难度键: 正整数} 形状，其余一律丢弃，防止脏文件把游戏带崩。
        # bool 是 int 的子类，要显式排除，否则 true 会被当成步数 1。
        best = {}
        if isinstance(data, dict):
            for key, value in data.items():
                if (
                    isinstance(key, str)
                    and isinstance(value, int)
                    and not isinstance(value, bool)
                    and value > 0
                ):
                    best[key] = value
        return best

    def best_for(self, key: str):
        """该难度的最少通关步数；没有记录返回 None。"""
        return self._best.get(key)

    def record(self, key: str, steps: int) -> bool:
        """登记一次通关。刷新（或首次创下）记录返回 True，否则 False。"""
        if steps <= 0:
            return False
        current = self._best.get(key)
        if current is not None and steps >= current:
            return False
        self._best[key] = steps
        self._save()
        return True

    def _save(self):
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self._best, f)
        except OSError:
            pass
