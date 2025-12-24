#!/usr/bin/env python3
import random
from collections import deque


class Minesweeper:
    def __init__(self, rows, cols, mine_count):
        if rows <= 0 or cols <= 0:
            raise ValueError("rows and cols must be positive")
        if mine_count <= 0 or mine_count >= rows * cols:
            raise ValueError("mine_count must be between 1 and rows*cols - 1")
        self.rows = rows
        self.cols = cols
        self.mine_count = mine_count
        self.mines = set()
        self.revealed = set()
        self.flags = set()
        self.neighbor_counts = {}
        self._place_mines()
        self._compute_neighbor_counts()

    def _place_mines(self):
        choices = random.sample(range(self.rows * self.cols), self.mine_count)
        for idx in choices:
            row = idx // self.cols
            col = idx % self.cols
            self.mines.add((row, col))

    def _compute_neighbor_counts(self):
        for row in range(self.rows):
            for col in range(self.cols):
                if (row, col) in self.mines:
                    continue
                count = sum((nr, nc) in self.mines for nr, nc in self.neighbors(row, col))
                self.neighbor_counts[(row, col)] = count

    def neighbors(self, row, col):
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                nr = row + dr
                nc = col + dc
                if 0 <= nr < self.rows and 0 <= nc < self.cols:
                    yield nr, nc

    def reveal(self, row, col):
        if (row, col) in self.flags or (row, col) in self.revealed:
            return True
        if (row, col) in self.mines:
            self.revealed.add((row, col))
            return False
        queue = deque([(row, col)])
        while queue:
            cr, cc = queue.popleft()
            if (cr, cc) in self.revealed or (cr, cc) in self.flags:
                continue
            self.revealed.add((cr, cc))
            if self.neighbor_counts.get((cr, cc), 0) == 0:
                for nr, nc in self.neighbors(cr, cc):
                    if (nr, nc) not in self.revealed and (nr, nc) not in self.flags:
                        queue.append((nr, nc))
        return True

    def toggle_flag(self, row, col):
        if (row, col) in self.revealed:
            return
        if (row, col) in self.flags:
            self.flags.remove((row, col))
        else:
            self.flags.add((row, col))

    def is_won(self):
        return len(self.revealed) == self.rows * self.cols - self.mine_count

    def display(self, show_mines=False):
        header = "   " + " ".join(f"{c:2d}" for c in range(self.cols))
        lines = [header]
        for r in range(self.rows):
            row_cells = []
            for c in range(self.cols):
                cell = (r, c)
                if show_mines and cell in self.mines:
                    symbol = "*"
                elif cell in self.revealed:
                    count = self.neighbor_counts.get(cell, 0)
                    symbol = str(count) if count > 0 else " "
                elif cell in self.flags:
                    symbol = "F"
                else:
                    symbol = "."
                row_cells.append(f"{symbol:2s}")
            lines.append(f"{r:2d} " + "".join(row_cells))
        return "\n".join(lines)


def parse_dimensions(text, default):
    if not text.strip():
        return default
    parts = text.strip().split()
    if len(parts) != 3:
        raise ValueError("请输入三项：行 列 雷数")
    rows, cols, mines = (int(part) for part in parts)
    return rows, cols, mines


def main():
    print("欢迎来到扫雷！输入坐标格式: r 行 列 (揭开), f 行 列 (插旗), q 退出")
    try:
        rows, cols, mines = parse_dimensions(
            input("请输入 行 列 雷数 (默认 9 9 10): "),
            (9, 9, 10),
        )
    except ValueError as exc:
        print(f"输入错误: {exc}")
        return

    try:
        game = Minesweeper(rows, cols, mines)
    except ValueError as exc:
        print(f"参数错误: {exc}")
        return

    while True:
        print("\n" + game.display())
        command = input("你的操作: ").strip().lower()
        if not command:
            continue
        if command == "q":
            print("已退出游戏。")
            break
        parts = command.split()
        if len(parts) != 3:
            print("请输入格式: r 行 列 或 f 行 列")
            continue
        action, row_text, col_text = parts
        if action not in {"r", "f"}:
            print("未知操作，请输入 r 或 f。")
            continue
        try:
            row = int(row_text)
            col = int(col_text)
        except ValueError:
            print("行列必须是数字。")
            continue
        if not (0 <= row < game.rows and 0 <= col < game.cols):
            print("坐标超出范围。")
            continue

        if action == "f":
            game.toggle_flag(row, col)
        else:
            safe = game.reveal(row, col)
            if not safe:
                print("\n" + game.display(show_mines=True))
                print("踩到雷了，游戏结束！")
                break
            if game.is_won():
                print("\n" + game.display(show_mines=True))
                print("恭喜通关！")
                break


if __name__ == "__main__":
    main()
