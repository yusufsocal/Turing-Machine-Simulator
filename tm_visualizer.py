#!/usr/bin/env python3
"""
Pygame visualizer for tm_simulator.py Turing machines.

Loads a machine file + input string, precomputes every step via
tm_simulator.step_machine(), then lets you play/pause/step/rewind
through the run while watching the tape animate.

Usage:
    python tm_visualizer.py <machine_file> <input_string> [--speed N]
"""
import argparse
import sys

import pygame

from tm_simulator import ParseError, parse_tm, step_machine

CELL_SIZE = 48
CELL_GAP = 6
TAPE_Y = 260
WINDOW_W, WINDOW_H = 960, 420

COLOR_BG = (24, 26, 32)
COLOR_CELL = (54, 58, 70)
COLOR_CELL_BLANK = (38, 40, 48)
COLOR_CELL_HEAD = (240, 196, 25)
COLOR_TEXT = (235, 235, 235)
COLOR_TEXT_HEAD = (24, 26, 32)
COLOR_STATE = (120, 200, 255)
COLOR_ACCEPT = (110, 220, 120)
COLOR_REJECT = (230, 90, 90)
COLOR_MUTED = (150, 152, 160)


def load_machine(path):
    with open(path) as f:
        text = f.read()
    return parse_tm(text)


def tape_cells(snapshot):
    """Yield (absolute_position, symbol, is_head) for every visited cell."""
    left, head_char, right = snapshot["left"], snapshot["head_char"], snapshot["right"]
    head_pos = snapshot["head_pos"]
    for i, sym in enumerate(left):
        yield head_pos - len(left) + i, sym, False
    yield head_pos, head_char, True
    for i, sym in enumerate(right):
        yield head_pos + 1 + i, sym, False


def draw_tape(screen, font, snapshot, blank):
    head_pos = snapshot["head_pos"]
    center_x = WINDOW_W // 2
    stride = CELL_SIZE + CELL_GAP

    for pos, sym, is_head in tape_cells(snapshot):
        x = center_x + (pos - head_pos) * stride - CELL_SIZE // 2
        rect = pygame.Rect(x, TAPE_Y - CELL_SIZE // 2, CELL_SIZE, CELL_SIZE)

        if is_head:
            color = COLOR_CELL_HEAD
        elif sym == blank:
            color = COLOR_CELL_BLANK
        else:
            color = COLOR_CELL
        pygame.draw.rect(screen, color, rect, border_radius=6)
        if is_head:
            pygame.draw.rect(screen, (255, 255, 255), rect, width=3, border_radius=6)

        if sym != blank or is_head:
            text_color = COLOR_TEXT_HEAD if is_head else COLOR_TEXT
            label = font.render(sym, True, text_color)
            screen.blit(label, label.get_rect(center=rect.center))

    tri_x, tri_y = center_x, TAPE_Y - CELL_SIZE // 2 - 14
    pygame.draw.polygon(
        screen, COLOR_CELL_HEAD,
        [(tri_x - 8, tri_y - 12), (tri_x + 8, tri_y - 12), (tri_x, tri_y)],
    )


def draw_hud(screen, font, big_font, snapshot, idx, total, input_str, playing, speed):
    state, status = snapshot["state"], snapshot["status"]

    screen.blit(big_font.render(f"state: {state}", True, COLOR_STATE), (24, 20))
    screen.blit(font.render(f"step {idx} / {total - 1}", True, COLOR_MUTED), (24, 60))
    screen.blit(font.render(f"input: {input_str}", True, COLOR_MUTED), (24, 84))

    if status == "accept":
        label = big_font.render("ACCEPT", True, COLOR_ACCEPT)
        screen.blit(label, (WINDOW_W - label.get_width() - 24, 20))
    elif status == "reject":
        label = big_font.render("REJECT", True, COLOR_REJECT)
        screen.blit(label, (WINDOW_W - label.get_width() - 24, 20))
        rej_state, rej_sym = snapshot["rejected_at"]
        detail = font.render(f"no transition for ({rej_state!r}, {rej_sym!r})", True, COLOR_MUTED)
        screen.blit(detail, (WINDOW_W - detail.get_width() - 24, 60))

    status_line = f"{'playing' if playing else 'paused'}   speed: {speed:.1f} steps/s"
    screen.blit(font.render(status_line, True, COLOR_MUTED), (24, WINDOW_H - 66))

    help_line = "space play/pause    left/right step    up/down speed    r reset    esc quit"
    screen.blit(font.render(help_line, True, COLOR_MUTED), (24, WINDOW_H - 36))


def main():
    parser = argparse.ArgumentParser(description="Pygame visualizer for tm_simulator machines.")
    parser.add_argument("machine_file")
    parser.add_argument("input_str")
    parser.add_argument("--speed", type=float, default=3.0, help="steps per second (default 3)")
    args = parser.parse_args()

    tm = load_machine(args.machine_file)
    snapshots = list(step_machine(tm, args.input_str))
    blank = tm["blank"]

    pygame.init()
    pygame.display.set_caption(f"Turing Machine Visualizer - {args.machine_file}")
    screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("consolas", 20)
    big_font = pygame.font.SysFont("consolas", 26, bold=True)

    idx = 0
    playing = False
    speed = args.speed
    time_acc = 0.0

    running = True
    while running:
        dt = clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    playing = not playing
                elif event.key == pygame.K_RIGHT:
                    playing = False
                    idx = min(idx + 1, len(snapshots) - 1)
                elif event.key == pygame.K_LEFT:
                    playing = False
                    idx = max(idx - 1, 0)
                elif event.key == pygame.K_UP:
                    speed = min(speed * 1.5, 60.0)
                elif event.key == pygame.K_DOWN:
                    speed = max(speed / 1.5, 0.25)
                elif event.key == pygame.K_r:
                    idx = 0
                    playing = False
                    time_acc = 0.0

        if playing and idx < len(snapshots) - 1:
            time_acc += dt
            step_interval = 1.0 / speed
            while time_acc >= step_interval and idx < len(snapshots) - 1:
                idx += 1
                time_acc -= step_interval
            if idx >= len(snapshots) - 1:
                playing = False
        else:
            time_acc = 0.0

        snapshot = snapshots[idx]

        screen.fill(COLOR_BG)
        draw_tape(screen, font, snapshot, blank)
        draw_hud(screen, font, big_font, snapshot, idx, len(snapshots), args.input_str, playing, speed)
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    try:
        main()
    except (ParseError, FileNotFoundError) as e:
        print(f"Error: {e}")
        sys.exit(1)
