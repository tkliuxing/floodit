# floodit

A coloring game implemented with Python and Pygame.
The concept is based on the Chrome extension [Flood-It!](https://chrome.google.com/webstore/detail/flood-it/hidcjhphimkfnacedjcnajpmlaegnddp).

一个由 Python + Pygame 开发的填色游戏。
游戏原型参考自 Chrome Store 扩展程序 [Flood-It!](https://chrome.google.com/webstore/detail/flood-it/hidcjhphimkfnacedjcnajpmlaegnddp)。

---

## Gameplay / 玩法

### English
* **Goal**: Fill the entire grid with a single color within the step limit.
* **Controls**:
    * The game starts from the top-left area of the grid. Your area is drawn with a white outline, so you can always see what you own and how it grows.
    * Click the color buttons on the right to change the current region's color. Hovering a color previews exactly which tiles it would absorb, and how many.
    * **Color Propagation**: When a region changes color, all adjacent tiles of the same color will change color simultaneously (with a smooth animation effect).
* **Keyboard shortcuts**:
    * `1`–`6` — pick the matching color
    * `R` or `F2` — start a new game
    * `L` — switch the interface language
    * `F11` — toggle fullscreen
    * `Esc` or `Q` — quit
* **Window**: The window is resizable — drag any edge and the whole board scales to fit while keeping its aspect ratio.
* **Language**: The interface follows your system locale. Set `FLOODIT_LANG=en` or `FLOODIT_LANG=zh` to override it.
* **Rules**:
    * **Win Condition**: The game is won when all tiles in the grid are the same color.
    * **Loss Condition**: The game is lost if you exceed the maximum number of steps.
    * **Scoring**: A higher score is achieved by using fewer steps.
    * **Misclicks are free**: Clicking the color your region already has changes nothing, so it costs no step.

### 中文
* **目标**：在规定的步数限制内，使棋盘格上的所有方块变成同一种颜色。
* **操作**：
    * 游戏从棋盘格的左上角区域开始。你的领地带白色描边，随时能看清自己占了哪些格、又长大了多少。
    * 点击界面右侧对应的颜色块，将当前连接区域的颜色替换为目标颜色。鼠标悬停在色块上会预览这一步能吃掉哪些格子、共几格。
    * **颜色传播**：颜色变化具有“扩散”效果：当改变当前区域颜色时，与其相邻且颜色相同的方块也会同步改变颜色。
* **键盘快捷键**：
    * `1`–`6` —— 选择对应颜色
    * `R` 或 `F2` —— 开始新游戏
    * `L` —— 切换界面语言
    * `F11` —— 切换全屏
    * `Esc` 或 `Q` —— 退出
* **窗口**：窗口可自由缩放——拖动任意边缘，整个棋盘会等比缩放适配，不会变形。
* **语言**：界面语言默认跟随系统区域设置，可用 `FLOODIT_LANG=en` 或 `FLOODIT_LANG=zh` 覆盖。
* **规则**：
    * **胜负判定**：当整个棋盘格仅剩一种颜色时，游戏胜利；如果在达到指定步数前未完成，则游戏失败。
    * **得分机制**：使用的总步数越少，得分越高。
    * **误点不罚**：点击当前领地已有的颜色不会改变棋盘，因此不消耗步数。

---

## Installation / 安装

* **Dependencies / 依赖**
    * [Python](http://python.org/getit/)
    * [SDL](http://www.libsdl.org/)
    * [pygame](http://pygame.org/download.shtml)

## Running / 运行

Run the following command in your terminal:
在终端/命令行中运行：
```bash
python main.py
```

## License / 许可

Released under the MIT License. Copyright (c) 2012 Ronald Bai.
The full text lives in [LICENSE](LICENSE).

本项目基于 MIT 许可证发布，版权归 Ronald Bai 所有，完整条款见 [LICENSE](LICENSE)。
