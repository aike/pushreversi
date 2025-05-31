# pygameを使用するバージョン
import pygame
import pygame.midi
import time

import sys

global midi_out
global midi_out_id

def midi_init():
  pygame.init()
  pygame.midi.init()    

  global midi_out
  global midi_out_id
  # MIDI出力デバイスIDを取得
  for dev in range(pygame.midi.get_count()):
    info = pygame.midi.get_device_info(dev)
    print(info)
    if info[1].decode() == 'Ableton Push 2' and info[3] == 1:
      midi_out_id = dev
      break
  # MIDI出力デバイスをオープン
  midi_out = pygame.midi.Output(midi_out_id)
  print(midi_out)

def midi_cleanup():
  midi_out.close()
  pygame.midi.quit()
  pygame.quit()

LED_BLACK = 0
LED_WHITE = 122
LED_BLUE  = 125
LED_GREEN = 126
LED_RED   = 127

def midi_put(x, y, color):
  note = 36 + (y * 8 + x)
  midi_out.note_on(note, color, 0)


EMPTY = '.'
BLACK = 'B'
WHITE = 'W'

DIRECTIONS = [(-1, -1), (-1, 0), (-1, 1),
              (0, -1),          (0, 1),
              (1, -1),  (1, 0),  (1, 1)]


def initialize_board():
  board = [[EMPTY for _ in range(8)] for _ in range(8)]
  board[3][3] = WHITE
  board[3][4] = BLACK
  board[4][3] = BLACK
  board[4][4] = WHITE
  return board

# 出力処理
def display_board(board):
  for y in range(8):
    for x in range(8):
      if board[y][x] == EMPTY:
        midi_put(x, y, LED_BLACK)
      elif board[y][x] == BLACK:
        midi_put(x, y, LED_BLUE)
      elif board[y][x] == WHITE:
        midi_put(x, y, LED_RED)

def clear():
  for y in range(8):
    for x in range(8):
      note = 36 + (y * 8 + x)
      midi_out.note_on(note, LED_BLACK, 0)


def display_board_text(board):
  # 列番号ヘッダ
  print('  ' + ' '.join(str(x) for x in range(8)))
  for y in range(8):
    row = board[y]
    print(f"{y} " + ' '.join(row))
  print()


def on_board(x, y):
  return 0 <= x < 8 and 0 <= y < 8


def opponent(player):
  return BLACK if player == WHITE else WHITE


def get_flips(board, player, x, y):
  if board[y][x] != EMPTY:
    return []
  flips = []
  opp = opponent(player)
  for dx, dy in DIRECTIONS:
    nx, ny = x + dx, y + dy
    line = []
    while on_board(nx, ny) and board[ny][nx] == opp:
      line.append((nx, ny))
      nx += dx
      ny += dy
    if on_board(nx, ny) and board[ny][nx] == player and line:
      flips.extend(line)
  return flips


def has_any_valid_move(board, player):
  for y in range(8):
    for x in range(8):
      if get_flips(board, player, x, y):
        return True
  return False


def get_valid_moves(board, player):
  moves = []
  for y in range(8):
    for x in range(8):
      if get_flips(board, player, x, y):
        moves.append((x, y))
  return moves


def make_move(board, player, x, y):
  flips = get_flips(board, player, x, y)
  if not flips:
    return False
  board[y][x] = player
  for fx, fy in flips:
    board[fy][fx] = player
  return True


def score(board):
  blacks = sum(row.count(BLACK) for row in board)
  whites = sum(row.count(WHITE) for row in board)
  return blacks, whites


# 入力処理
def parse_input(prompt):
  while True:
    s = input(prompt).strip()
    if s.lower() in ('q', 'quit', 'exit'):
      print('Game aborted.')
      sys.exit(0)
    parts = s.split()
    if len(parts) != 2:
      print('Invalid input. Please enter: x y (e.g. "3 2").')
      continue
    try:
      x, y = map(int, parts)
      if on_board(x, y):
        return x, y
      else:
        print('Coordinates out of range (0-7).')
    except ValueError:
      print('Invalid numbers. Please enter integers 0-7.')


def main():
  board = initialize_board()
  current = BLACK
  skip_count = 0

  while True:
    # 出力処理
    display_board(board)

    blacks, whites = score(board)
    print(f"Score -> Black: {blacks}, White: {whites}")

    if not has_any_valid_move(board, current):
      print(f"{current} has no valid moves. Skipping.")
      skip_count += 1
      if skip_count >= 2:
        print('No moves for both players. Game over.')
        break
      current = opponent(current)
      continue
    skip_count = 0

    moves = get_valid_moves(board, current)
    print(f"{current}'s turn. Valid moves: {moves}")

    # 入力処理
    x, y = parse_input(f"Enter move for {current} (or 'q' to quit): ")

    if not make_move(board, current, x, y):
      print('Invalid move. Try again.')
      continue
    current = opponent(current)

  # 出力処理
  display_board(board)

  blacks, whites = score(board)
  print(f"Final Score -> Black: {blacks}, White: {whites}")
  if blacks > whites:
    print('Black wins!')
  elif whites > blacks:
    print('White wins!')
  else:
    print('It\'s a tie!')


if __name__ == '__main__':
  midi_init()
  main()
  midi_cleanup()
