## floodit

这是一个由python + pygame写成的填色游戏.
游戏原型为: Chrome store [Flood-It!](https://chrome.google.com/webstore/detail/flood-it/hidcjhphimkfnacedjcnajpmlaegnddp)

## 玩法

* 该游戏的目标是在允许的步数内使一种颜色填满整个棋盘格.
* 从棋盘格左上角开始, 点击右侧的各个色块进行填充.
* 当您改变当前区域的颜色时, 具有相同颜色的相邻方块也都会改变颜色.
* 当棋盘格中只有一种颜色时游戏结束.
* 所使用步数越少, 得分越高.

## 安装

* 依赖
    * [python](http://python.org/getit/)
    * [SDL](http://www.libsdl.org/)
    * [pygame](http://pygame.org/download.shtml)

## 运行

在shell/cmd中运行`python floodit.py`

## Licence

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