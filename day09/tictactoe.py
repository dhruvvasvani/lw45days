#!/usr/bin/env python
# coding: utf-8

# In[1]:


# import pygame

board = [" ", " ", " ", " ", " ", " ", " ", " ", " "]
player = "X"
running = True

while running:
    print("\n")
    print(board[0], "|", board[1], "|", board[2])
    print("--|---|--")
    print(board[3], "|", board[4], "|", board[5])
    print("--|---|--")
    print(board[6], "|", board[7], "|", board[8])
    print("\n")

    try:
        pos = int(input("Player " + player + ", choose the position from (1-9): ")) - 1

        if pos < 0 or pos > 8:
            print("Invalid input! Please choose a number between 1 and 9.")
            continue

        if board[pos] != " ":
            print("Position already taken! Try another spot.")
            continue

        board[pos] = player

        win_conditions = [
            [0, 1, 2], [3, 4, 5], [6, 7, 8],
            [0, 3, 6], [1, 4, 7], [2, 5, 8],
            [0, 4, 8], [2, 4, 6]
        ]

        is_win = False
        for condition in win_conditions:
            if board[condition[0]] == board[condition[1]] == board[condition[2]] == player:
                is_win = True
                break

        if is_win:
            print("\n")
            print(board[0], "|", board[1], "|", board[2])
            print("---|---|---")
            print(board[3], "|", board[4], "|", board[5])
            print("---|---|---")
            print(board[6], "|", board[7], "|", board[8])
            print(f"\nGame Over! Player {player} wins!")
            running = False
            continue

        if " " not in board:
            print("\n")
            print(board[0], "|", board[1], "|", board[2])
            print("---|---|---")
            print(board[3], "|", board[4], "|", board[5])
            print("---|---|---")
            print(board[6], "|", board[7], "|", board[8])
            print("\nGame Over! It's a draw!")
            running = False
            continue

        if player == "X":
            player = "O"
        else:
            player = "X"

    except ValueError:
        print("Please enter a valid number.")


# In[ ]:




