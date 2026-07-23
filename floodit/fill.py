def fill(ary: list, number: int, x: int = 0, y: int = 0, src: int = None):
    """
    将二维数组(ary)中从坐标(x, y)开始，相邻且与原始值(src)相同的格子
    替换为指定数字(number)。
    """
    if x < 0 or y < 0 or x >= len(ary[0]) or y >= len(ary):
        return
    if src is None:
        src = ary[y][x]
        if src == number:
            return
    if ary[y][x] != src:
        return
    ary[y][x] = number
    fill(ary, number, x + 1, y, src)
    fill(ary, number, x - 1, y, src)
    fill(ary, number, x, y + 1, src)
    fill(ary, number, x, y - 1, src)


def get_fill_sequence(ary: list, number: int, start_x: int = 0, start_y: int = 0):
    """
    使用 BFS 获取填充过程中的颜色变化序列（按层级分组）。
    返回: list of list of (x, y, new_color)
    """
    rows = len(ary)
    cols = len(ary[0])

    src = ary[start_y][start_x]
    if src == number:
        return []

    sequence = []
    current_layer = [(start_x, start_y)]
    visited = set([(start_x, start_y)])

    while current_layer:
        layer_data = []
        next_layer = []
        for x, y in current_layer:
            layer_data.append((x, y, number))

            for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < cols and 0 <= ny < rows:
                    if (nx, ny) not in visited and ary[ny][nx] == src:
                        visited.add((nx, ny))
                        next_layer.append((nx, ny))

        sequence.append(layer_data)
        current_layer = next_layer
    return sequence


def filldone(ary: list) -> bool:
    """判断二维数组是否已全部填充为同一个值。"""
    src = ary[0][0]
    return all(cell == src for row in ary for cell in row)


if __name__ == "__main__":
    # 命令行版 floodit 游戏
    import os
    import random

    def print_board(ary: list):
        for line in ary:
            print("".join(line))

    symbols = ["1", "2", "3", "4", "5", "6"]
    board = [[random.choice(symbols) for _ in range(7)] for _ in range(7)]

    os.system("clear")
    print_board(board)

    while not filldone(board):
        number = input("Select symbol: ")
        while number not in symbols:
            number = input("Select symbol: ")
        fill(board, number, x=0, y=0)
        os.system("clear")
        print_board(board)

    print("You win!")
