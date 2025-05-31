# pygameを使用するバージョン
import pygame
import pygame.midi

import time
import sys
import random

global midi_in
global midi_out

def midi_init():
  pygame.init()
  pygame.midi.init()    

  global midi_in
  global midi_out
  # MIDI出力デバイスIDを取得
  for dev in range(pygame.midi.get_count()):
    info = pygame.midi.get_device_info(dev)
    print(info)
    if info[1].decode() == 'Ableton Push 2' and info[3] == 0:
      midi_in_id = dev
    if info[1].decode() == 'Ableton Push 2' and info[3] == 1:
      midi_out_id = dev
  # MIDI出力デバイスをオープン
  midi_in = pygame.midi.Input(midi_in_id)
  midi_out = pygame.midi.Output(midi_out_id)
  print(midi_out)

def midi_cleanup():
  midi_out.close()
  pygame.midi.quit()
  pygame.quit()

def midi_input():
  note_status = -1
  while note_status != 144:
    while not midi_in.poll():
      time.sleep(0.01)  # 少し待機してから再チェック
    midi_events = midi_in.read(10)
    print ("full midi_events:" + str(midi_events))
    note_num = midi_events[0][0][1] #ノート番号
    note_status = midi_events[0][0][0] #ノートオン・オフ信号
  y = 7 - (note_num - 36) // 8
  x = (note_num - 36) % 8
  return x, y

LED_BLACK = 0
LED_WHITE = 122
LED_BLUE  = 125
LED_GREEN = 126
LED_RED   = 127

def midi_put(x, y, color):
  note = 36 + ((7 - y) * 8 + x)
  midi_out.note_on(note, color, 0)

def midi_blink(x, y, color):
  note = 36 + ((7 - y) * 8 + x)
  for _ in range(3):
    midi_out.note_on(note, LED_BLACK, 0)
    time.sleep(0.2)
    midi_out.note_on(note, color, 0)
    time.sleep(0.2)


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
  display_board_text(board)
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
  print('  ' + ' '.join(str(x) for x in range(8)))
  for y in range(8):
    print(f"{y} " + ' '.join(board[y]))
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
  return any(get_flips(board, player, x, y)
          for y in range(8) for x in range(8))


def get_valid_moves(board, player):
  return [(x, y)
          for y in range(8)
          for x in range(8)
          if get_flips(board, player, x, y)]


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


def computer_move(board, player):
  moves = get_valid_moves(board, player)
  if not moves:
    return None
  best_moves = []
  max_flips = -1
  for x, y in moves:
    flips = get_flips(board, player, x, y)
    if len(flips) > max_flips:
      best_moves = [(x, y)]
      max_flips = len(flips)
    elif len(flips) == max_flips:
      best_moves.append((x, y))
  return random.choice(best_moves)


def parse_input(prompt):
  while True:
    s = input(prompt).strip()
    if s.lower() in ('q', 'quit', 'exit'):
      print('Game aborted.')
      midi_cleanup()
      sys.exit(0)
    parts = s.split()
    if len(parts) != 2:
      print('Invalid input. Enter: x y')
      continue
    try:
      x, y = map(int, parts)
      if on_board(x, y):
        return x, y
      print('Coordinates must be 0-7.')
    except ValueError:
      print('Enter two integers 0-7.')


def main():
  board = initialize_board()
  human = BLACK
  computer = WHITE
  current = BLACK
  skip_count = 0

  while True:
    display_board(board)
    b_score, w_score = score(board)
    print(f"Score -> Black: {b_score}, White: {w_score}")

    if not has_any_valid_move(board, current):
      print(f"{current} has no valid moves. Skipping.")
      skip_count += 1
      if skip_count >= 2:
        print('No moves for both. Game over.')
        break
      current = opponent(current)
      continue
    skip_count = 0

    if current == human:
      moves = get_valid_moves(board, human)
      print(f"Your turn ({human}). Valid moves: {moves}")

      x, y = midi_input()
      # x, y = parse_input(f"Enter move ({human}): ")

      if not make_move(board, human, x, y):
        print('Invalid move. Try again.')
        continue
      midi_blink(x, y, LED_BLUE)
    else:
      print(f"Computer's turn ({computer}). Thinking...")
      move = computer_move(board, computer)
      if move:
        x, y = move
        midi_blink(x, y, LED_RED)
        print(f"Computer plays: {x} {y}")
        make_move(board, computer, x, y)
      else:
        print('Computer cannot move. Skipping.')

    current = opponent(current)

  # Final
  display_board(board)
  b_score, w_score = score(board)
  print(f"Final -> Black: {b_score}, White: {w_score}")
  if b_score > w_score:
    print('Black wins!')
  elif w_score > b_score:
    print('White wins!')
  else:
    print("It's a tie!")

if __name__ == '__main__':
  midi_init()
  main()
  midi_cleanup()
