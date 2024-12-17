import socket
import threading
import json
import tkinter as tk
from tkinter import messagebox
import random


class MinesweeperClient:
    def _init_(self, host="127.0.0.1", port=65432):
        self.host = host
        self.port = port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self):
        try:
            self.client_socket.connect((self.host, self.port))
            print(f"Conectado al servidor {self.host}:{self.port}")
        except Exception as e:
            print(f"Error conectando al servidor: {e}")

    def send_command(self, command):
        try:
            self.client_socket.send(json.dumps(command).encode("utf-8"))
            response = self.client_socket.recv(1024).decode("utf-8")
            return json.loads(response)
        except Exception as e:
            print(f"Error enviando comando: {e}")

    def close(self):
        self.client_socket.close()


class MinesweeperGUI:
    def _init_(self):
        self.client = MinesweeperClient()
        self.client.connect()

        self.root = tk.Tk()
        self.root.title("Buscaminas")

        self.rows = 5
        self.cols = 5
        self.mines = 5
        self.board = []
        self.flags = set()  # Celdas marcadas con banderas
        self.revealed_cells = set()  # Celdas ya despejadas

        init_command = {"command": "INIT", "rows": self.rows, "cols": self.cols, "mines": self.mines}
        response = self.client.send_command(init_command)
        self.board = response["board"]

        self.buttons = []
        for r in range(self.rows):
            row = []
            for c in range(self.cols):
                button = tk.Button(self.root, text="", width=3, height=2, 
                                   command=lambda r=r, c=c: self.on_click(r, c))
                button.bind("<Button-3>", lambda event, r=r, c=c: self.on_right_click(r, c))  # Click derecho
                button.grid(row=r, column=c)
                row.append(button)
            self.buttons.append(row)

        resolve_button = tk.Button(self.root, text="Resolver", command=self.reveal_mines)
        resolve_button.grid(row=self.rows, column=0, columnspan=self.cols)

    def on_click(self, row, col):
        if (row, col) in self.flags:
            return  # No permitir despejar celdas marcadas con bandera

        click_command = {"command": "CLICK", "row": row, "col": col}
        response = self.client.send_command(click_command)

        if response["status"] == "GAME OVER":
            messagebox.showinfo("Fin del juego", "¡Has perdido!")
            self.reveal_mines()
            return

        for r, c in response["cells"]:
            self.buttons[r][c].config(text=str(self.board[r][c]), state="disabled")
            self.revealed_cells.add((r, c))

        if self.check_victory():
            messagebox.showinfo("¡Victoria!", "¡Has ganado!")
            self.reveal_mines()

    def on_right_click(self, row, col):
        """Manejar el evento de click derecho para marcar/desmarcar una bandera."""
        button = self.buttons[row][col]
        if button["text"] == "F":
            button.config(text="", bg="SystemButtonFace")
            self.flags.remove((row, col))
        else:
            button.config(text="F", bg="yellow")
            self.flags.add((row, col))

    def check_victory(self):
        """Verificar si todas las celdas que no son minas han sido despejadas."""
        total_cells = self.rows * self.cols
        non_mine_cells = total_cells - self.mines
        return len(self.revealed_cells) == non_mine_cells

    def reveal_mines(self):
        resolve_command = {"command": "RESOLVE"}
        response = self.client.send_command(resolve_command)
        for r, c in response["mines"]:
            self.buttons[r][c].config(text="M", bg="red")

    def run(self):
        self.root.mainloop()
        self.client.close()


if _name_ == "_main_":
    gui = MinesweeperGUI()
    gui.run()