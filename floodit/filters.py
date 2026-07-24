"""棋盘的颜色融合滤镜。

做法是对**已经画好的棋盘区域**做后处理，而不是改变格子的画法：
先把该区域降采样到"每格 cell_px 像素"，再用双线性插值放大回原尺寸。
降采样丢掉的正是格子内部的平坦区域，插值放回来时相邻格之间就出现
了渐变带，于是硬边界变成了融合过渡。

因为是后处理，它对铺开动画、填充波纹、屏幕震动一视同仁，
无需在各个动画里分别处理。

cell_px 是唯一的旋钮：
    cell_px == 格子边长  ->  完全不融合（等价于关闭）
    cell_px 越小         ->  过渡带越宽，融合越强
    cell_px == 1         ->  每格只剩一个采样点，整块画面糊成色云
过渡带宽度约等于 格子边长 / cell_px 像素。
"""

import pygame as pg

# 每格保留的采样像素数。实测过几档强度（15x15 棋盘、格子 20px）：
#
#   cell_px   过渡带宽   糊掉的像素
#         8      2.5px        12.1%
#         4        5px        24.9%
#         2       10px        47.9%
#         1       20px        82.7%
#
# "糊掉的像素"指已经不属于任何一种调色板颜色、玩家无法判定归属的比例。
# 融合过强会伤可玩性——认不出连通区域的形状和边界，正是这个游戏要做的判断，
# 所以取最轻的一档：边界柔和了，格子仍然清清楚楚。
CELL_PX = 8


def transition_width(block_side: int, cell_px: int) -> float:
    """过渡带的大致宽度（像素），用来直观描述某个强度。"""
    if not cell_px or cell_px >= block_side:
        return 0.0
    return block_side / cell_px


def blend_rect(surface: pg.Surface, rect: pg.Rect, grid: tuple, cell_px: int):
    """就地把 surface 上 rect 区域的格子边界融合掉。

    surface: 目标画面
    rect: 棋盘区域
    grid: (列数, 行数)
    cell_px: 每格保留几个采样像素；None 或 >= 格子边长时不做任何事
    """
    if not cell_px:
        return
    cols, rows = grid
    small = (max(1, cols * cell_px), max(1, rows * cell_px))
    if small[0] >= rect.width and small[1] >= rect.height:
        # 采样密度已经不低于原图，融合没有意义
        return

    board = surface.subsurface(rect).copy()
    # 先降采样再放大，两步都用双线性，才会得到平滑渐变而不是马赛克
    shrunk = pg.transform.smoothscale(board, small)
    surface.blit(pg.transform.smoothscale(shrunk, rect.size), rect.topleft)
