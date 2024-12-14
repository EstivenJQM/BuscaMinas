import socket
import threading
import json
import tkinter as tk
from tkinter import messagebox
import random


class MinesweeperServer:
    def __init__(self, host="127.0.0.1", port=65432):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.clients = []
        print(f"Servidor iniciado en {self.host}:{self.port}")

    def handle_client(self, client_socket):
        try:
            while True:
                data = client_socket.recv(1024).decode("utf-8")
                if not data:
                    break

                message = json.loads(data)
                command = message.get("command")
                
                if command == "INIT":
                    rows = message["rows"]
                    cols = message["cols"]
                    mines = message["mines"]
                    board = self.create_board(rows, cols, mines)
                    client_socket.send(json.dumps({"board": board}).encode("utf-8"))

                elif command == "CLICK":
                    row = message["row"]
                    col = message["col"]
                    response = self.evaluate_click(row, col, client_socket)
                    client_socket.send(json.dumps(response).encode("utf-8"))

                elif command == "RESOLVE":
                    mines_positions = self.get_mines_positions()
                    client_socket.send(json.dumps({"mines": mines_positions}).encode("utf-8"))

        except Exception as e:
            print(f"Error manejando cliente: {e}")
        finally:
            client_socket.close()

    def create_board(self, rows, cols, mines):
        self.board = [[0 for _ in range(cols)] for _ in range(rows)]
        self.mines_positions = set()

        while len(self.mines_positions) < mines:
            r = random.randint(0, rows - 1)
            c = random.randint(0, cols - 1)
            if (r, c) not in self.mines_positions:
                self.mines_positions.add((r, c))
                self.board[r][c] = "M"

        for r, c in self.mines_positions:
            for dr in range(-1, 2):
                for dc in range(-1, 2):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < rows and 0 <= nc < cols and self.board[nr][nc] != "M":
                        self.board[nr][nc] += 1

        return self.board

    def evaluate_click(self, row, col, client_socket):
        if self.board[row][col] == "M":
            return {"status": "GAME OVER"}

        visited = set()
        cells_to_reveal = []

        def reveal(r, c):
            if (r, c) in visited or not (0 <= r < len(self.board) and 0 <= c < len(self.board[0])):
                return
            visited.add((r, c))

            if self.board[r][c] == 0:
                cells_to_reveal.append((r, c))
                for dr in range(-1, 2):
                    for dc in range(-1, 2):
                        reveal(r + dr, c + dc)
            else:
                cells_to_reveal.append((r, c))

        reveal(row, col)

        return {"status": "CONTINUE", "cells": cells_to_reveal}

    def get_mines_positions(self):
        return list(self.mines_positions)

    def start(self):
        print("Servidor esperando conexiones...")
        try:
            while True:
                client_socket, client_address = self.server_socket.accept()
                print(f"Cliente conectado desde {client_address}")
                self.clients.append(client_socket)
                threading.Thread(target=self.handle_client, args=(client_socket,)).start()
        except KeyboardInterrupt:
            print("Servidor apagándose...")
        finally:
            self.server_socket.close()

if __name__ == "__main__":
    server = MinesweeperServer()
    server.start()
