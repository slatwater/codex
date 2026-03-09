"""
贪吃蛇游戏 - Snake Game
适用系统: Windows (需要 windows-curses) / Linux / macOS
安装依赖: pip install windows-curses  (仅 Windows 需要)
运行方式: python snake.py
操作说明: 方向键控制移动，Q 键退出
"""

import curses
import random
import time

# 游戏配置
BOARD_HEIGHT = 20
BOARD_WIDTH = 40
INITIAL_SPEED = 0.15  # 每帧间隔（秒）
SPEED_UP = 0.005      # 每吃一个食物加速


def draw_border(win):
    """绘制边框"""
    win.border(
        curses.ACS_VLINE, curses.ACS_VLINE,
        curses.ACS_HLINE, curses.ACS_HLINE,
        curses.ACS_ULCORNER, curses.ACS_URCORNER,
        curses.ACS_LLCORNER, curses.ACS_LRCORNER,
    )


def draw_info(stdscr, score, best_score):
    """在边框外绘制得分信息"""
    stdscr.addstr(0, 2, f" 贪吃蛇 Snake ", curses.A_BOLD | curses.color_pair(3))
    stdscr.addstr(0, BOARD_WIDTH - 22, f" 得分: {score:4d}  最高: {best_score:4d} ")


def place_food(snake):
    """在蛇身以外的位置随机放置食物"""
    while True:
        y = random.randint(1, BOARD_HEIGHT - 2)
        x = random.randint(1, BOARD_WIDTH - 2)
        if (y, x) not in snake:
            return (y, x)


def game_over_screen(stdscr, score, best_score):
    """显示游戏结束画面，返回 True 表示重新开始，False 表示退出"""
    stdscr.clear()
    h, w = stdscr.getmaxyx()
    cy = h // 2

    msgs = [
        ("游戏结束  GAME OVER", curses.A_BOLD | curses.color_pair(2)),
        (f"本局得分: {score}", curses.A_NORMAL),
        (f"历史最高: {best_score}", curses.A_NORMAL),
        ("", curses.A_NORMAL),
        ("按 R 重新开始  |  按 Q 退出", curses.color_pair(3)),
    ]
    for i, (msg, attr) in enumerate(msgs):
        x = max(0, (w - len(msg)) // 2)
        stdscr.addstr(cy - 2 + i, x, msg, attr)

    stdscr.refresh()
    stdscr.nodelay(False)
    while True:
        key = stdscr.getch()
        if key in (ord('r'), ord('R')):
            return True
        if key in (ord('q'), ord('Q'), 27):
            return False


def run_game(stdscr):
    """单局游戏主循环"""
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(100)

    # 颜色初始化
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_GREEN, -1)   # 蛇身
    curses.init_pair(2, curses.COLOR_RED, -1)     # 游戏结束 / 食物
    curses.init_pair(3, curses.COLOR_YELLOW, -1)  # 标题 / 提示

    best_score = 0

    while True:
        # --- 初始化单局状态 ---
        mid_y = BOARD_HEIGHT // 2
        mid_x = BOARD_WIDTH // 2
        snake = [(mid_y, mid_x), (mid_y, mid_x - 1), (mid_y, mid_x - 2)]
        direction = curses.KEY_RIGHT
        food = place_food(snake)
        score = 0
        speed = INITIAL_SPEED
        last_time = time.time()

        while True:
            # 处理按键（非阻塞）
            key = stdscr.getch()
            if key in (curses.KEY_UP, curses.KEY_DOWN,
                       curses.KEY_LEFT, curses.KEY_RIGHT):
                # 禁止 180° 掉头
                opposites = {
                    curses.KEY_UP: curses.KEY_DOWN,
                    curses.KEY_DOWN: curses.KEY_UP,
                    curses.KEY_LEFT: curses.KEY_RIGHT,
                    curses.KEY_RIGHT: curses.KEY_LEFT,
                }
                if key != opposites[direction]:
                    direction = key
            elif key in (ord('q'), ord('Q'), 27):
                return best_score  # 直接退出

            now = time.time()
            if now - last_time < speed:
                continue
            last_time = now

            # 计算新蛇头
            head_y, head_x = snake[0]
            if direction == curses.KEY_UP:
                head_y -= 1
            elif direction == curses.KEY_DOWN:
                head_y += 1
            elif direction == curses.KEY_LEFT:
                head_x -= 1
            elif direction == curses.KEY_RIGHT:
                head_x += 1

            new_head = (head_y, head_x)

            # 碰撞检测：墙壁
            if (head_y <= 0 or head_y >= BOARD_HEIGHT - 1 or
                    head_x <= 0 or head_x >= BOARD_WIDTH - 1):
                break

            # 碰撞检测：自身
            if new_head in snake:
                break

            snake.insert(0, new_head)

            # 吃到食物
            if new_head == food:
                score += 10
                best_score = max(best_score, score)
                food = place_food(snake)
                speed = max(0.04, speed - SPEED_UP)
            else:
                snake.pop()

            # --- 绘制 ---
            stdscr.erase()
            draw_border(stdscr)
            draw_info(stdscr, score, best_score)

            # 绘制食物
            fy, fx = food
            stdscr.addstr(fy, fx, "●", curses.color_pair(2) | curses.A_BOLD)

            # 绘制蛇
            for i, (sy, sx) in enumerate(snake):
                ch = "◆" if i == 0 else "■"
                stdscr.addstr(sy, sx, ch, curses.color_pair(1) | curses.A_BOLD)

            # 底部提示
            stdscr.addstr(
                BOARD_HEIGHT, 1,
                " 方向键: 移动  |  Q: 退出 ",
                curses.color_pair(3),
            )
            stdscr.refresh()

        # --- 单局结束 ---
        best_score = max(best_score, score)
        restart = game_over_screen(stdscr, score, best_score)
        if not restart:
            break

    return best_score


def main():
    try:
        curses.wrapper(run_game)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
