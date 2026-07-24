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
    * The game starts from the top-left area of the grid.
    * Click the color buttons on the right to change the current region's color.
    * **Color Propagation**: When a region changes color, all adjacent tiles of the same color will change color simultaneously (with a smooth animation effect).
* **Keyboard shortcuts**:
    * `1`–`6` — pick the matching color
    * `R` or `F2` — start a new game
    * `L` — switch the interface language
    * `Esc` or `Q` — quit
* **Language**: The interface follows your system locale. Set `FLOODIT_LANG=en` or `FLOODIT_LANG=zh` to override it.
* **Rules**:
    * **Win Condition**: The game is won when all tiles in the grid are the same color.
    * **Loss Condition**: The game is lost if you exceed the maximum number of steps.
    * **Scoring**: A higher score is achieved by using fewer steps.
    * **Constraint**: Clicking the color currently occupying the region still consumes one step.

### 中文
* **目标**：在规定的步数限制内，使棋盘格上的所有方块变成同一种颜色。
* **操作**：
    * 游戏从棋盘格的左上角区域开始。
    * 点击界面右侧对应的颜色块，将当前连接区域的颜色替换为目标颜色。
    * **颜色传播**：颜色变化具有“扩散”效果：当改变当前区域颜色时，与其相邻且颜色相同的方块也会同步改变颜色。
* **键盘快捷键**：
    * `1`–`6` —— 选择对应颜色
    * `R` 或 `F2` —— 开始新游戏
    * `L` —— 切换界面语言
    * `Esc` 或 `Q` —— 退出
* **语言**：界面语言默认跟随系统区域设置，可用 `FLOODIT_LANG=en` 或 `FLOODIT_LANG=zh` 覆盖。
* **规则**：
    * **胜负判定**：当整个棋盘格仅剩一种颜色时，游戏胜利；如果在达到指定步数前未完成，则游戏失败。
    * **得分机制**：使用的总步数越少，得分越高。
    * **惩罚机制**：点击当前区域已有的颜色仍会消耗一步。

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

> Copyright (c) 2012 Ronald Bai <<ouyanghongyu@gmail.com>>
> 
> Permission is hereby granted, free of charge, to any person obtaining a copy
> of this software and associated documentation files (the "Software"), to deal
> in the Software without restriction, including without limitation the rights
> to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
> copies of the Software, and to permit persons to whom the Software is
> furnished to do so, subject to the following conditions:
> 
> The above copyright notice and this permission notice shall be included in
> all copies or substantial portions of the Software.
> 
> THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
> IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
> FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
> AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
> LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
> OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
> THE SOFTWARE.
