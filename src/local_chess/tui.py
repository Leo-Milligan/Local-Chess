#!/usr/bin/env python3

from .board import chess_board
from .game import game
from .pieces import *
from .network import network

from textual import on
from textual.app import App
from textual.containers import Grid, HorizontalGroup, VerticalGroup
from textual.widgets import Select, Static, Input, Label, Button, Footer, DataTable, Tabs, Tab, Digits
from textual.color import Color
from textual.reactive import reactive
from textual.screen import Screen, ModalScreen
from textual.message import Message

import copy
import json
import os
import socket
import threading
import time

current_directory = os.path.dirname(os.path.abspath(__file__))
style_sheet_path = os.path.join(current_directory, "ui_style_sheet.json")

ui_style_sheet = json.load(open(style_sheet_path, encoding="utf-8"))


class MainMenu(Screen):

    def compose(self):

        title = "\
 ██╗       ██████╗   ██████╗  █████╗  ██╗              ██████╗ ██╗  ██╗ ███████╗ ███████╗ ███████╗\n\
 ██║      ██╔═══██╗ ██╔════╝ ██╔══██╗ ██║             ██╔════╝ ██║  ██║ ██╔════╝ ██╔════╝ ██╔════╝\n\
 ██║      ██║   ██║ ██║      ███████║ ██║      █████╗ ██║      ███████║ █████╗   ███████╗ ███████╗\n\
 ██║      ██║   ██║ ██║      ██╔══██║ ██║      ╚════╝ ██║      ██╔══██║ ██╔══╝   ╚════██║ ╚════██║\n\
 ███████╗ ╚██████╔╝ ╚██████╗ ██║  ██║ ███████╗        ╚██████╗ ██║  ██║ ███████╗ ███████║ ███████║\n\
 ╚══════╝  ╚═════╝   ╚═════╝ ╚═╝  ╚═╝ ╚══════╝         ╚═════╝ ╚═╝  ╚═╝ ╚══════╝ ╚══════╝ ╚══════╝"


        with Grid(id="main_menu_grid"):
            yield Label(title, id="title")
            yield Button("Singleplayer - Comming Soon!", variant="success", disabled=True, id="play_button_ai")
            yield Button("Multiplayer (Local)", variant="success", id="play_button_local")
            yield Button("Multiplayer (LAN)", variant="success", id="play_button_lan")
            yield Button("Quit", variant="error", id="quit_button")

    def on_mount(self):

        self.query_one("#main_menu_grid", Grid).border_title = "Welcome To"

    def on_button_pressed(self, event):

        if event.button.id == "quit_button":
            self.app.exit()
        elif event.button.id == "play_button_local":
            self.app.push_screen(GamePreferencesScreen())
        elif event.button.id == "play_button_lan":
            self.app.push_screen(LanChoiceScreen())

class LanChoiceScreen(Screen):

    def __init__(self):
        super().__init__()
        self.host = socket.gethostbyname(socket.gethostname())
        self.port = 9999
        self.player_colour = "white"

    def compose(self):

        with Grid(id="lan_choice_grid"):

            yield Tabs(Tab("Host", id="host_tab"),
                       Tab("Join", id="join_tab"))

            with Grid(id="tab_content_grid"):

                with HorizontalGroup(id="host_ip_line"):
                    yield Label("IP Address: ", id="ip_address_label", classes="centered_label")
                    yield Digits(self.host, id="ip_display")
                yield Button("Start Server", variant="success", id="host_button")

                with HorizontalGroup(id="join_input_line"):
                    yield Label("Enter IP: ", id="join_message", classes="centered_label")
                    yield Input(placeholder= "e.g. 127.0.0.1", id="join_input")
                yield Button("Join", variant="success", id="join_button")

                yield Button("Back To Menu", variant="error", id="return_main_menu")

    def on_tabs_tab_activated(self, event):

        host_button = self.query_one("#host_button", Button)
        host_ip_line = self.query_one("#host_ip_line", HorizontalGroup)
        join_button = self.query_one("#join_button", Button)
        join_input_line = self.query_one("#join_input_line", HorizontalGroup)

        if event.tab.id == "host_tab":
            host_ip_line.display = True
            host_button.display = True

            join_input_line.display = False
            join_button.display = False
        else:
            join_input_line.display = True
            join_button.display = True

            host_ip_line.display = False
            host_button.display = False

    def on_button_pressed(self, event):

        if event.button.id == "return_main_menu":
            self.app.network.handle_disconnection()

        elif event.button.id == "host_button":

            if not self.app.network_running:
                self.app.network.host_game(self.host, self.port)

            elif self.app.network_running:
                self.app.network.close_connection()

        elif event.button.id == "join_button":

            join_input = self.query_one("#join_input", Input)
            host = join_input.value
            self.app.network.connect_to_game(host, self.port)

    def watch_network_running(self):

            if not self.app.network_running:
                self.query_one("#host_button", Button).label = "Start Server"
                self.query_one("#host_button", Button).variant = "success"
                self.query_one("#join_button", Button).disabled = False

            elif self.app.network_running:
                self.query_one("#host_button", Button).label = "Stop Server"
                self.query_one("#host_button", Button).variant = "warning"
                self.query_one("#join_button", Button).disabled = True

    def watch_connection_made(self):

        if self.app.connection_made:
            if self.app.network.is_server:
                self.app.push_screen(GamePreferencesScreen())
            else:
                self.app.push_screen(WaitingRoomScreen())

    def on_mount(self):
        self.query_one("#lan_choice_grid", Grid).border_title = "Multiplayer (LAN)"
        self.watch(self.app, "network_running", self.watch_network_running)
        self.watch(self.app, "connection_made", self.watch_connection_made)

class GamePreferencesScreen(Screen):

    def __init__(self):
        super().__init__()

    def compose(self):

        with Grid(id="game_preferences_grid"):

            with Grid(id="drop_downs_and_labels"):
                yield Label("Player-1 Colour: ", classes="centered_label")
                yield Select(options = (("white", "white"),
                                        ("black", "black")),
                             allow_blank = False, id="player_colour_select")

                yield Label("Time Control", classes="centered_label")
                yield Select(options = (("Unlimited", (None, None)),
                                        ("15 + 10", (15*60,10)),
                                        ("10 + 5", (10*60,5)),
                                        ("10 + 0", (10*60,0)),
                                        ("5 + 0", (5*60,0)),
                                        ("3 + 2", (3*60,2)),
                                        ("3 + 0", (3*60,0))),
                             allow_blank = False, id="time_control_select")

                yield Label("Piece Type: ", classes="centered_label")
                yield Select(options = (("large", "large"),
                                        ("small", "small"),
                                        ("letters", "letters")),
                             allow_blank = False, id="piece_type_select")

                yield Label("Board Colours: ", classes="centered_label")
                yield Select(options = (("default", "default"),
                                        ("forest", "forest"),
                                        ("lilac", "lilac"),
                                        ("ocean", "ocean"),
                                        ("buttercup", "buttercup")),
                             allow_blank = False, id="board_colour_select")

            yield Button("Start Game", variant = "success", id="start_game_button")
            yield Button("Back To Menu", variant="error", id="return_main_menu")

    def on_button_pressed(self, event):

        if event.button.id == "return_main_menu":
            self.app.network.handle_disconnection()

        elif event.button.id == "start_game_button":

            player_1_colour = self.query_one("#player_colour_select", Select).selection
            piece_type = self.query_one("#piece_type_select", Select).selection
            board_colour = self.query_one("#board_colour_select", Select).selection
            time_control = self.query_one("#time_control_select", Select).selection
            time_allowance = time_control[0]
            time_increment = time_control[1]

            self.app.push_screen(ChessGame(piece_style=piece_type, board_colour=board_colour, player_colour=player_1_colour, time_allowance = time_allowance, time_increment = time_increment))

            if self.app.connection_made:

                player_2_colour = "white" if player_1_colour == "black" else "black"

                message = {"game_action": "start_game", "piece_type": piece_type, "board_colour": board_colour, "player_2_colour": player_2_colour, "time_allowance": time_allowance, "time_increment": time_increment}
                self.app.network.send_move(message)

    def on_mount(self):

        self.query_one("#game_preferences_grid", Grid).border_title = "Game Setup"
        self.query_one("#start_game_button", Button).focus()


class WaitingRoomScreen(Screen):

    def compose(self):

        with Grid(id="waiting_room_grid"):

            yield Label("Waiting for host to begin the game...", classes="centered_label", id="waiting_room_message")
            yield Button("Disconnect", variant="error", id="return_main_menu")

    def on_button_pressed(self, event):

        if event.button.id == "return_main_menu":
            self.app.network.handle_disconnection()

    def listen_for_game_start(self, move_information):

        if move_information.get("game_action") == "start_game":
            piece_type = move_information["piece_type"]
            board_colour = move_information["board_colour"]
            player_2_colour = move_information["player_2_colour"]
            time_allowance = move_information["time_allowance"]
            time_increment = move_information["time_increment"]
            self.app.push_screen(ChessGame(piece_style=piece_type, board_colour=board_colour, player_colour=player_2_colour, time_allowance=time_allowance, time_increment=time_increment))

    def on_mount(self):

        self.query_one("#waiting_room_grid", Grid).border_title = "Waiting Room"
        self.app.network.move_callback = self.listen_for_game_start

class Cell(Static):

    def __init__(self, board, board_colour, piece_symbols, row, col):

        super().__init__(classes = "cell")
        self.board = board
        self.piece_symbols = piece_symbols
        self.board_colour = board_colour
        self.row = row
        self.col = col

    def colour_cell(self):
        if (self.row + self.col) % 2:
            self.styles.background = Color.parse(ui_style_sheet["board_colours"][self.board_colour]["dark_square_colour"])
        else:
            self.styles.background = Color.parse(ui_style_sheet["board_colours"][self.board_colour]["light_square_colour"])

    def populate_cell(self):

        cell_contents = self.board[self.col][self.row]

        if cell_contents == None:
            piece_symbol = ""
            piece_colour = None
        else:
            piece_name = type(cell_contents).__name__
            piece_colour = cell_contents.colour
            piece_symbol = ui_style_sheet["piece_symbols"][self.piece_symbols][piece_name]

        self.update(piece_symbol)

        if piece_colour == "black":
            self.styles.color = Color.parse(ui_style_sheet["board_colours"][self.board_colour]["dark_piece_colour"])
        elif piece_colour == "white":
            self.styles.color = Color.parse(ui_style_sheet["board_colours"][self.board_colour]["light_piece_colour"])

class ChessBoardGrid(Grid):

    def __init__(self, board, num_rows, num_cols, piece_symbols, board_colour, colour_at_bottom):

        super().__init__(id="chess_board_grid")
        self.board = board
        self.game = game
        self.num_rows = num_rows
        self.num_cols = num_cols
        self.piece_symbols = piece_symbols
        self.board_colour = board_colour
        self.colour_at_bottom = colour_at_bottom

    def compose(self):

        self.styles.grid_size_columns = self.num_cols
        self.styles.grid_size_rows = self.num_rows

        if self.colour_at_bottom == "white":
            col_range = range(self.num_cols-1,-1,-1)
            row_range = range(self.num_rows)
        else:
            col_range = range(self.num_cols)
            row_range = range(self.num_rows - 1, -1, -1)

        for col in col_range:
            for row in row_range:
                cell = Cell(self.board, self.board_colour, self.piece_symbols, row, col)
                cell.colour_cell()
                cell.populate_cell()
                yield cell

    def update_board(self):
        for cell in self.query(Cell):
            cell.populate_cell()

class TurnLabel(Label):

    turn_colour = reactive("white")

    def watch_turn_colour(self):
        self.update(f" {"W" if self.turn_colour == "white" else "B"} | ")

class GameOverScreen(ModalScreen):

    def __init__(self, game_over_message):

        super().__init__()
        self.game_over_message = game_over_message

    def compose(self):

        with Grid(id="dialog"):
            yield Label(self.game_over_message, id="message")
            yield Button("Restart", variant="success", id="restart_button")
            yield Button("Review", variant="warning", id="review_button")
            yield Button("Menu", variant="error", id="menu_button")

    def on_button_pressed(self, event):

        if event.button.id == "menu_button":
            self.dismiss("menu")
        elif event.button.id == "restart_button":
            self.dismiss("restart")
        elif event.button.id == "review_button":
            self.dismiss("review")

class StatusBar(Static):

    def compose(self):

        with HorizontalGroup():
            yield TurnLabel()
            yield Label("Enter Move: ", id = "command_line_prompt")
            yield Input(compact = True, id = "command_line")

        yield Label(id = "message_line")

class CapturedPiecesDisplay(Label):

    captured_piece_list = reactive([])

    def __init__(self, id):

        super().__init__(id=id)
        self.piece_type_counts = {"king": 0, "queen": 0, "rook": 0, "bishop": 0, "knight": 0, "pawn": 0}

    def watch_captured_piece_list(self):

        string = ""

        self.update_piece_type_counts()

        for piece_type in self.piece_type_counts:
            if self.piece_type_counts[piece_type] > 0:
                piece_symbol = ui_style_sheet["piece_symbols"]["small"][piece_type]
                number_of_pieces = self.piece_type_counts[piece_type]
                string += f"{piece_symbol} x{number_of_pieces} "

        self.update(string)

    def update_piece_type_counts(self):

        self.piece_type_counts = {"king": 0, "queen": 0, "rook": 0, "bishop": 0, "knight": 0, "pawn": 0}

        for piece in self.captured_piece_list:
            piece_name = type(piece).__name__
            if piece_name in list(self.piece_type_counts):
                self.piece_type_counts[piece_name] += 1

class TimeDisplay(Label):

    start_time = reactive(0)
    time = reactive(1)
    total_time_elapsed = reactive(0)

    def __init__(self, time_allowance, id):
        super().__init__(id=id)
        self.time_allowance = time_allowance
        self.time = self.time_allowance

    def on_mount(self):
        self.update_timer = self.set_interval(1 / 60, self.update_time, pause=True)

    def update_time(self):
        next_time = self.time_allowance - ( self.total_time_elapsed + (time.monotonic() - self.start_time) )
        if next_time < 0:
            self.time = 0
        else:
            self.time = next_time

    def watch_time(self, time):
        minutes, seconds = divmod(time, 60)
        self.update(f"{minutes:02.0f}:{seconds:05.2f}")

        if self.time == 0:
            self.post_message(self.TimeDepleted())

    def start(self):
        self.start_time = time.monotonic()
        self.update_timer.resume()

    def stop(self):
        self.update_timer.pause()
        if self.start_time > 0:
            self.total_time_elapsed += time.monotonic() - self.start_time

    def add_increment(self, increment):

        self.time += increment
        self.total_time_elapsed -= increment

    class TimeDepleted(Message):

        def __init__(self):
            super().__init__()

class MoveDataTable(DataTable):

    move_notation_history = reactive({"white": [],
                                      "black": []})

    def watch_move_notation_history(self):

        self.clear()

        for i in range(len(self.move_notation_history["white"])):

            row_number = i + 1
            current_white_move = self.move_notation_history["white"][i] if i < len(self.move_notation_history["white"]) else ""
            current_black_move = self.move_notation_history["black"][i] if i < len(self.move_notation_history["black"]) else ""

            self.add_row(row_number,current_white_move,current_black_move)

        self.adjust_column_size()

    def adjust_column_size(self):

        total_width = self.size.width
        total_padding = 2 * (self.cell_padding * len(self.columns))
        column_width = (total_width - total_padding) // len(self.columns)
        for column in self.columns.values():
            column.auto_width = False
            column.width = column_width
        self.refresh()

    def on_mount(self):
        self.add_columns(("Turn", "turn"),
                         ("White", "white"),
                         ("Black", "black"))
        self.can_focus = False
        self.cursor_type = "row"

    def on_resize(self):
        self.adjust_column_size()

class PositionMarker(Static):

    def __init__(self, marker_type, index, board_colour):
        super().__init__()
        self.marker_type = marker_type
        self.index = index
        self.board_colour = board_colour

    def populate_cell(self):

        if self.marker_type == "column":
            contents = str(chr(self.index + 97))
        else:
            contents = str(self.index + 1)

        self.update(contents)

    def on_mount(self):

        self.styles.background = Color.parse(ui_style_sheet["board_colours"][self.board_colour]["border_colour"])
        self.populate_cell()

class BorderCorner(Static):

    def __init__(self, board_colour):
        super().__init__()
        self.board_colour = board_colour

    def on_mount(self):
        self.styles.background = Color.parse(ui_style_sheet["board_colours"][self.board_colour]["border_colour"])

class ChessBoardWithAccessories(Static):

    def __init__(self, board, num_rows, num_cols, piece_style, board_colour, colour_at_bottom, time_allowance):
        super().__init__()
        self.board = board
        self.colour_at_bottom = colour_at_bottom
        self.num_rows = num_rows
        self.num_cols = num_cols
        self.piece_style = piece_style
        self.board_colour = board_colour
        self.time_allowance = time_allowance

    def compose(self):

        if self.colour_at_bottom == "white":
            upper_captured_pieces_display_id = "white_captured_pieces_display"
            lower_captured_pieces_display_id = "black_captured_pieces_display"
            upper_time_display_id = "black_time_display"
            lower_time_display_id = "white_time_display"
        else:
            upper_captured_pieces_display_id = "black_captured_pieces_display"
            lower_captured_pieces_display_id = "white_captured_pieces_display"
            upper_time_display_id = "white_time_display"
            lower_time_display_id = "black_time_display"

        if self.colour_at_bottom == "white":
            vertical_range = range(self.num_cols - 1, -1, -1)
            horizontal_range = range(self.num_cols)
        else:
            vertical_range = range(self.num_cols)
            horizontal_range = range(self.num_cols - 1, -1, -1)

        with HorizontalGroup(classes="information_bar"):
            yield CapturedPiecesDisplay(id=upper_captured_pieces_display_id)
            if self.time_allowance:
                yield TimeDisplay(self.time_allowance, id=upper_time_display_id)

        with Grid(id="chess_board_with_markers_grid"):

            yield BorderCorner(self.board_colour)
            with HorizontalGroup():
                for i in horizontal_range:
                    yield PositionMarker("column", i, self.board_colour)
            yield BorderCorner(self.board_colour)

            with VerticalGroup():
                for i in vertical_range:
                    marker = PositionMarker("row", i, self.board_colour)
                    marker.styles.content_align = ("left", "middle")
                    yield marker

            yield ChessBoardGrid(self.board, self.num_rows, self.num_cols, self.piece_style, self.board_colour, self.colour_at_bottom)

            with VerticalGroup():
                for i in vertical_range:
                    marker = PositionMarker("row", i, self.board_colour)
                    marker.styles.content_align = ("right", "middle")
                    yield marker

            yield BorderCorner(self.board_colour)
            with HorizontalGroup():
                for i in horizontal_range:
                    yield PositionMarker("column", i, self.board_colour)
            yield BorderCorner(self.board_colour)

        with HorizontalGroup(classes="information_bar"):
            yield CapturedPiecesDisplay(id=lower_captured_pieces_display_id)
            if self.time_allowance:
                yield TimeDisplay(self.time_allowance, id=lower_time_display_id)

    def update_size(self):

        width_per_cell = (self.parent.size.width - 4) / (self.num_cols * 2.2)
        height_per_cell = (self.parent.size.height - 4) / self.num_rows

        limiting_dimention = int(min(width_per_cell, height_per_cell))

        self.styles.width = limiting_dimention * self.num_cols * 2.2
        self.styles.height = limiting_dimention * self.num_rows + 4

    def on_mount(self):

        self.update_size()

class ChessBoardContainer(Static):

    def __init__(self, board, num_rows, num_cols, piece_style, board_colour, colour_at_bottom, time_allowance):
        super().__init__()
        self.board = board
        self.colour_at_bottom = colour_at_bottom
        self.num_rows = num_rows
        self.num_cols = num_cols
        self.piece_style = piece_style
        self.board_colour = board_colour
        self.time_allowance = time_allowance

    def compose(self):
        yield ChessBoardWithAccessories(self.board, self.num_rows, self.num_cols, self.piece_style, self.board_colour, self.colour_at_bottom, self.time_allowance)

    def on_resize(self):

        width_per_cell = (self.size.width - 4) / (self.num_cols * 2.2)
        height_per_cell = (self.size.height - 4) / self.num_rows

        limiting_dimention = int(min(width_per_cell, height_per_cell))

        chess_board_with_accessories = self.query_one("ChessBoardWithAccessories")

        chess_board_with_accessories.styles.width = limiting_dimention * self.num_cols * 2.2 + 4
        chess_board_with_accessories.styles.height = limiting_dimention * self.num_rows + 4

class ChessGame(Screen):

    BINDINGS = [("a", "advance_move", "Advance Move"),
                ("u", "undo_move", "Undo Move"),
                ("q", "exit_review_mode", "Exit Review Mode")]

    def __init__(self, piece_style = "small", board_colour = "default", player_colour = "white", time_allowance = None, time_increment = None):

        super().__init__()
        self.chess_board = chess_board()
        self.game = game(self.chess_board)
        self.chess_board.set_board()

        self.num_rows = self.chess_board.num_rows
        self.num_cols = self.chess_board.num_cols
        self.piece_style = piece_style
        self.board_colour = board_colour
        self.colour_at_bottom = player_colour
        self.time_allowance = time_allowance
        self.time_increment = time_increment

        if self.app.connection_made:
            self.player_colour = player_colour
        else:
            self.player_colour = "white"

        self.pending_question_information = None
        self.cached_move_information = None
        self.last_game_over_message = None
        self.review_mode = False

    def compose(self):

        with Grid(id="game_grid"):
            yield ChessBoardContainer(self.chess_board.board, self.num_rows, self.num_cols, self.piece_style, self.board_colour, self.colour_at_bottom, self.time_allowance)
            yield MoveDataTable()

            with Grid(id="lower_section"):
                yield StatusBar()

                footer = Footer()
                footer.display = False
                yield footer

    def on_mount(self):

        self.chess_board.update_castle_flag()
        self.query_one(TurnLabel).turn_colour = self.game.turn_colour

        if self.app.connection_made:
            self.app.network.move_callback = self.action_opponent_move

    @on(Input.Submitted)
    async def handle_user_input(self):

        self.clear_message()
        command_line = self.query_one(Input)
        player_input = command_line.value.strip(" +#!?")
        command_line.value = ""

        if self.app.connection_made and self.game.pending_draw_offer_by_opponent:
            if player_input == "y":
                self.game.pending_draw_offer_by_opponent = False
                self.app.network.send_move({"valid": True, "resign": False, "draw_offer": True, "game_action": "accept_draw_offer"})
                self.update_command_line_prompt("Enter Move: ")
                self.game.immediate_draw_possible = True
                await self.action_move({"valid": True, "resign": False, "draw_offer": True})
                return
            elif player_input == "n":
                self.game.pending_draw_offer_by_opponent = False
                self.update_command_line_prompt("Enter Move: ")
                self.app.network.send_move({"game_action": "reject_draw_offer"})
                return

        if self.game.turn_colour != self.player_colour and player_input.lower() != "r":
            await self.display_message("Waiting for opponent's move...")
            return

        if self.pending_question_information:
            move_information = self.game.interperate_user_preferences_answer(player_input, self.cached_move_information, self.pending_question_information)
        else:
            move_information = self.game.interperet_move_notation(list(player_input))

        if not move_information["valid"]:
            self.update_command_line_prompt("Enter Move: ")
            self.pending_question_information = None
            self.cached_move_information = None

            if move_information.get("error") is not None:
                await self.display_message(move_information["error"])
            return

        question_information = self.game.get_user_preferences_question(move_information)

        if not self.app.connection_made and move_information["draw_offer"] and not self.game.immediate_draw_possible:
            question_id = "draw_offer"
            question = f"{self.game.turn_colour.capitalize()} wants to draw, do you accept? (y/n): "
            valid_answers = ["y", "n"]

            question_information = {"question_id": question_id, "question": question, "valid_answers": valid_answers}

        if question_information:
            self.update_command_line_prompt(question_information["question"])
            self.pending_question_information = question_information
            self.cached_move_information = move_information
            return
        else:
            self.update_command_line_prompt("Enter Move: ")
            self.pending_question_information = None
            self.cached_move_information = None

        move_information["player_colour"] = self.player_colour

        if self.game.waiting_for_draw_response:
            move_information["game_action"] = "reject_draw_due_to_move"
            self.game.waiting_for_draw_response = False
            await self.display_message("Draw offer rescinded!")

        if self.app.connection_made:
            if self.time_allowance:
                white_timer = self.query_one("#white_time_display", TimeDisplay)
                black_timer = self.query_one("#black_time_display", TimeDisplay)
                move_information["white_time"] = white_timer.time
                move_information["white_total_time_elapsed"] = white_timer.total_time_elapsed
                move_information["black_time"] = black_timer.time
                move_information["black_total_time_elapsed"] = black_timer.total_time_elapsed
            self.app.network.send_move(move_information)

        await self.action_move(move_information)

        if not self.app.connection_made:
            self.player_colour = self.game.turn_colour

    async def action_move(self, move_information):

        result = self.game.apply_move(move_information)

        if result["message"]:
            await self.display_message(result["message"])

        self.update_ui()
        self.check_for_game_end(result)

        if self.time_allowance and (not self.game.winner and not self.game.draw):
            white_timer = self.query_one("#white_time_display", TimeDisplay)
            black_timer = self.query_one("#black_time_display", TimeDisplay)

            if self.game.turn_colour == "white":
                white_timer.start()
                black_timer.stop()
                black_timer.add_increment(self.time_increment)
            else:
                black_timer.start()
                white_timer.stop()
                white_timer.add_increment(self.time_increment)

    async def action_opponent_move(self, move_information):

        if move_information.get("game_action") == "restart":
            if not self.review_mode:
                self.app.pop_screen()
                self.reset_game_and_ui()
                return
            elif self.review_mode:
                self.exit_review_mode()
                self.app.pop_screen()
                self.reset_game_and_ui()
                return

        elif move_information.get("game_action") == "time_depleted":
            white_timer = self.query_one("#white_time_display", TimeDisplay)
            black_timer = self.query_one("#black_time_display", TimeDisplay)

            white_timer.stop()
            black_timer.stop()

            white_timer.time = move_information["white_time"]
            black_timer.time = move_information["black_time"]
            return

        elif move_information.get("game_action") == "reject_draw_due_to_move":
            await self.display_message("Draw offer rescinded!")
            self.update_command_line_prompt("Enter Move: ")
            self.game.pending_draw_offer_by_opponent = False

        elif move_information.get("game_action") == "reject_draw_offer":
            await self.display_message("Draw offer refused!")
            self.game.waiting_for_draw_response = False
            return

        elif move_information.get("game_action") == "accept_draw_offer":
            self.game.waiting_for_draw_response = False
            self.game.immediate_draw_possible = True

        elif move_information["draw_offer"] and not self.game.immediate_draw_possible:
            self.update_command_line_prompt(f"{self.game.turn_colour.capitalize()} wants to draw, do you accept? (y/n): ")
            self.game.pending_draw_offer_by_opponent = True
            return

        if self.time_allowance:
            white_timer = self.query_one("#white_time_display", TimeDisplay)
            black_timer = self.query_one("#black_time_display", TimeDisplay)
            white_timer.time = move_information["white_time"]
            white_timer.total_time_elapsed = move_information["white_total_time_elapsed"]
            black_timer.time = move_information["black_time"]
            black_timer.total_time_elapsed = move_information["black_total_time_elapsed"]

        result = self.game.apply_move(move_information)

        if result["message"]:
            await self.display_message(result["message"])

        self.update_ui()
        self.check_for_game_end(result)

        if self.time_allowance and (not self.game.winner and not self.game.draw):
            white_timer = self.query_one("#white_time_display", TimeDisplay)
            black_timer = self.query_one("#black_time_display", TimeDisplay)

            if self.game.turn_colour == "white":
                white_timer.start()
                black_timer.stop()
            else:
                black_timer.start()
                white_timer.stop()

    def on_time_display_time_depleted(self, message):

        white_timer = self.query_one("#white_time_display", TimeDisplay)
        black_timer = self.query_one("#black_time_display", TimeDisplay)

        white_timer.stop()
        black_timer.stop()

        if white_timer.time == 0:
            self.game.winner = "black"
        elif black_timer.time == 0:
            self.game.winner = "white"

        result = {"check": False, "checkmate": False, "resign": False, "draw": False, "time_depleted": True, "message": ""}
        self.check_for_game_end(result)

        if self.app.connection_made:
            data = {"game_action": "time_depleted", "white_time": white_timer.time, "black_time": black_timer.time}
            self.app.network.send_move(data)

    def update_ui(self):

        self.query_one(ChessBoardGrid).update_board()
        self.query_one(TurnLabel).turn_colour = self.game.turn_colour
        self.query_one("#white_captured_pieces_display", CapturedPiecesDisplay).captured_piece_list = self.game.captured_white_pieces.copy()
        self.query_one("#black_captured_pieces_display", CapturedPiecesDisplay).captured_piece_list = self.game.captured_black_pieces.copy()
        self.query_one(MoveDataTable).move_notation_history = copy.deepcopy(self.game.move_notation_history)
        if self.game.move_number > 1:
            self.query_one(MoveDataTable).move_cursor(row = self.game.move_number // 2 - 1)

    def update_command_line_prompt(self, message):
        self.query_one("#command_line_prompt", Label).update(message)

    def check_for_game_end(self, result):

        if result["resign"] or result["checkmate"] or result["time_depleted"]:
            message = f"{self.game.winner.capitalize()} Wins!"
        elif result["draw"]:
            message = "Game ends in a draw!"
        else:
            return

        if self.time_allowance:
            self.query_one("#white_time_display", TimeDisplay).stop()
            self.query_one("#black_time_display", TimeDisplay).stop()

        self.last_game_over_message = message
        if threading.current_thread() == threading.main_thread():
            self.app.push_screen(GameOverScreen(message), self.handle_game_over)
        else:
            self.app.call_from_thread(self.app.push_screen, GameOverScreen(message), self.handle_game_over)

    def reset_game_and_ui(self):

        if self.time_allowance:
            white_timer = self.query_one("#white_time_display", TimeDisplay)
            black_timer = self.query_one("#black_time_display", TimeDisplay)

            white_timer.time = self.time_allowance
            white_timer.total_time_elapsed = 0
            black_timer.time = self.time_allowance
            black_timer.total_time_elapsed = 0

        self.game.reset_game()
        self.update_ui()

        if not self.app.connection_made:
            self.player_colour = self.game.turn_colour

    def handle_game_over(self, choice):

        if choice == "menu":
            self.app.network.handle_disconnection()

        elif choice == "restart":
            self.reset_game_and_ui()
            if self.app.connection_made:
                data = {"game_action": "restart"}
                self.app.network.send_move(data)

        elif choice == "review":
            self.enter_review_mode()

    async def display_message(self, message):

        message_line = self.query_one("#message_line", Label)
        message_line.update(message)

        self.set_timer(2.5, self.clear_message)

    def clear_message(self):
        message_line = self.query_one("#message_line", Label)
        message_line.update("")

    def enter_review_mode(self):

        if self.time_allowance:
            self.query_one("#white_time_display", TimeDisplay).display = False
            self.query_one("#black_time_display", TimeDisplay).display = False

        self.query_one(StatusBar).display = False
        self.query_one(Footer).display = True

        self.review_mode = True

    def exit_review_mode(self):

        for _ in self.game.move_history:
            self.game.advance_once_using_move_delta()
            self.update_ui()

        if self.time_allowance:
            self.query_one("#white_time_display", TimeDisplay).display = True
            self.query_one("#black_time_display", TimeDisplay).display = True

        self.query_one(StatusBar).display = True
        self.query_one(Footer).display = False

        self.review_mode = False

        self.app.push_screen(GameOverScreen(self.last_game_over_message), self.handle_game_over)

    def action_exit_review_mode(self):

        self.exit_review_mode()

    def action_advance_move(self):

        self.game.advance_once_using_move_delta()
        self.refresh_bindings()
        self.update_ui()

    def action_undo_move(self):

        self.game.undo_once_using_move_delta()
        self.refresh_bindings()
        self.update_ui()

    def check_action(self, action, parameters):

        if action == "exit_review_mode" and not self.review_mode:
            return False
        if action == "advance_move" and self.game.move_number == (len(self.game.move_history) + 1):
            return None
        if action == "undo_move" and self.game.move_number == 1:
            return None
        return True

class ChessApp(App):

    CSS_PATH = "chess_board_cell.tcss"
    SCREENS = {"main_menu": MainMenu, "chess_game": ChessGame, "lan_choice_screen": LanChoiceScreen, "game_preferences_screen": GamePreferencesScreen, "waiting_room_screen": WaitingRoomScreen}

    network_running = reactive(False)
    connection_made = reactive(False)
    pop_up_message = reactive(None)

    def __init__(self):

        super().__init__()

    def on_mount(self):
        self.theme = "nord"
        self.push_screen("main_menu")
        self.network = network(self.app)

    def watch_pop_up_message(self):

        if self.pop_up_message:
            self.app.notify(self.pop_up_message["message"], title = self.pop_up_message["title"], severity="warning")
            self.pop_up_message = None

if __name__ == "__main__":
    app = ChessApp()
    app.run()
