from __future__ import annotations
import torch
import torch.nn as nn
import os
import random
import time
import threading
from src.handlers import BaseHandler
from scripts.paths.abalone_paths import abalone_nnue_path


class AbaloneNNUE(nn.Module):
    def __init__(self, input_features=121, hidden_dim=256):
        super().__init__()
        self.accumulator = nn.Linear(input_features, hidden_dim)
        self.hidden = nn.Sequential(
            nn.Linear(hidden_dim, 128),
            nn.LeakyReLU(0.1),
            nn.Linear(128, 64),
        )
        self.skip = nn.Linear(hidden_dim, 64)
        self.output = nn.Sequential(
            nn.LeakyReLU(0.1),
            nn.Linear(64, 1),
        )
        self._init_weights()

    def _init_weights(self):
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.kaiming_normal_(m.weight, nonlinearity='leaky_relu')
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)

    def forward(self, x):
        acc = torch.nn.functional.leaky_relu(self.accumulator(x), 0.1)
        return self.output(self.hidden(acc) + self.skip(acc))


class _SearchTimeout(Exception):
    pass

_thread_local = threading.local()

EMPTY = 0
BLACK = 1  # Gracz MAX
WHITE = -1  # Gracz MIN
WALL = 99  # Ściana ochronna (padding)

# Stałe offsety oparte na współrzędnych osiowych (Axial) dla macierzy 11x11
# r rośnie w dół (I=1 na górze, A=9 na dole), q rośnie w prawo.
# 1: NW, 2: NE, 3: E, 4: SE, 5: SW, 6: W
OFFSETS = {
    1: -11,  # NW (dr=-1, dq=0)
    2: -10,  # NE (dr=-1, dq=+1)
    3: 1,    # E  (dr=0,  dq=+1)
    4: 11,   # SE (dr=+1, dq=0)
    5: 10,   # SW (dr=+1, dq=-1)
    6: -1    # W  (dr=0,  dq=-1)
}

# Inicjalizacja tablicy Zobrista dla 121 pól i 3 stanów (WHITE=-1, EMPTY=0, BLACK=1)
# Mapujemy stan piece na indeks: piece + 1 (WHITE:0, EMPTY:1, BLACK:2)
ZOBRIST_TABLE = [[random.getrandbits(64) for _ in range(3)] for _ in range(121)]
ZOBRIST_BLACK_TO_MOVE = random.getrandbits(64)


class VectorBoard:
    def __init__(self, initial_setup=True):
        # Inicjalizacja pełnej macierzy 11x11 (121 pól) jako ŚCIANY
        self.board = [WALL] * 121
        self._carve_playable_area()
        if initial_setup:
            self._setup_initial_position()
            self.current_hash = self.get_zobrist_hash()
        else:
            self.current_hash = 0  # Będzie przypisane ręcznie przy kopiowaniu stanu

    def _carve_playable_area(self):
        """Wydrążamy legalne pola (0) wewnątrz ścian na podstawie mappera."""
        for idx in mapper.idx_to_str.keys():
            self.board[idx] = EMPTY

    def _setup_initial_position(self):
        """Ustawia standardową pozycję początkową Abalone."""
        # Czarne (BLACK=1) na górze (Rzędy A, B i część C) we frontendzie y=4,3,2
        for notation in ['A1', 'A2', 'A3', 'A4', 'A5', 'B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'C3', 'C4', 'C5']:
            self.board[mapper.to_index(notation)] = BLACK
            
        # Białe (WHITE=-1) na dole (Rzędy I, H i część G) we frontendzie y=-4,-3,-2
        for notation in ['I5', 'I6', 'I7', 'I8', 'I9', 'H4', 'H5', 'H6', 'H7', 'H8', 'H9', 'G5', 'G6', 'G7']:
            self.board[mapper.to_index(notation)] = WHITE

    def get_zobrist_hash(self, current_player=BLACK):
        """Oblicza pełny hasz Zobrista dla aktualnego stanu planszy."""
        h = 0
        for idx in range(121):
            piece = self.board[idx]
            if piece != WALL:
                # piece + 1 mapuje -1, 0, 1 na 0, 1, 2
                h ^= ZOBRIST_TABLE[idx][piece + 1]
        if current_player == BLACK:
            h ^= ZOBRIST_BLACK_TO_MOVE
        return h

    def _get_alignment(self, indices):
        """Sprawdzamy czy kule leżą w jednej linii (offset 1, 10 lub 11)."""
        if len(indices) == 1:
            return 0
        diff = indices[1] - indices[0]
        if diff in [1, 10, 11]:
            if len(indices) == 2 or (indices[2] - indices[1] == diff):
                return diff
        return None

    def display(self):
        """Wyświetla planszę w konsoli (I na górze, A na dole)."""
        rows = ['I', 'H', 'G', 'F', 'E', 'D', 'C', 'B', 'A']
        for row_char in rows:
            line = f"{row_char}: "
            # Dodajemy wcięcia dla heksagonalnego wyglądu
            padding = " " * (abs(ord(row_char) - ord('E')))
            line += padding
            for col in range(1, 10):
                try:
                    idx = mapper.to_index(f"{row_char}{col}")
                    val = self.board[idx]
                    if val == BLACK: line += "B "
                    elif val == WHITE: line += "W "
                    else: line += ". "
                except ValueError:
                    line += "  "
            print(line)

    def generate_legal_moves(self, player):
        """Znajduje wszystkie legalne ruchy."""
        legal_moves = []
        own_marbles = []
        for idx in range(121):
            if self.board[idx] == player:
                own_marbles.append(idx)

        groups = []
        # Budujemy grupy wzdłuż osi: 1 (E), 10 (NW), 11 (NE)
        for start_idx in own_marbles:
            groups.append([start_idx])
            for build_dir in [1, 10, 11]:
                idx2 = start_idx + build_dir
                if 0 <= idx2 < 121 and self.board[idx2] == player:
                    groups.append([start_idx, idx2])
                    idx3 = idx2 + build_dir
                    if 0 <= idx3 < 121 and self.board[idx3] == player:
                        groups.append([start_idx, idx2, idx3])

        # Wszystkie 6 offsetów z OFFSETS
        for group in groups:
            for move_dir_idx, move_offset in OFFSETS.items():
                result = self.apply_move(group, move_offset, player)
                if result is not None:
                    new_board, points, is_push, new_hash = result
                    legal_moves.append({
                        'marbles': group,
                        'direction': move_offset,
                        'direction_idx': move_dir_idx,
                        'points': points,
                        'is_push': is_push,
                        'new_state': new_board,
                        'new_hash': new_hash
                    })
        return legal_moves


    def apply_move(self, indices, direction_offset, player):
        """
        Główna funkcja poruszania kulami.
        :param indices: Lista indeksów kul, które gracz chce ruszyć (np. [60, 61]). MUSI być posortowana.
        :param direction_offset: Wartość z OFFSETS (np. 1 dla Wschodu)
        :param player: Kto wykonuje ruch (BLACK = 1, WHITE = -1)
        :return: (nowa_plansza, zdobyte_punkty, is_push, nowy_hash) LUB None, jeśli ruch jest nielegalny.
        """
        # 1. Walidacja podstawowa
        if not (1 <= len(indices) <= 3):
            return None  # Można ruszyć od 1 do 3 kul
        for idx in indices:
            if self.board[idx] != player:
                return None  # Kula nie należy do gracza

        alignment = self._get_alignment(indices)
        if len(indices) > 1 and alignment is None:
            return None  # Kule nie leżą w prostej linii

        # 2. Określenie typu ruchu (W Osi / Równoległy)
        is_inline = False
        if len(indices) == 1:
            is_inline = True
        elif abs(direction_offset) == alignment:
            is_inline = True

        new_board = list(self.board)  # Kopia tablicy dla nowego węzła drzewa
        new_hash = self.current_hash ^ ZOBRIST_BLACK_TO_MOVE  # Zmiana tury
        points = 0
        is_push = False

        # ==========================================
        # PRZYPADEK A: Ruch Boczny (Broadside)
        # ==========================================
        if not is_inline:
            # W ruchu bocznym KAŻDE pole docelowe MUSI być całkowicie puste.
            for idx in indices:
                if self.board[idx + direction_offset] != EMPTY:
                    return None  # Zablokowane przez wroga, własną kulę lub ścianę

            # Wykonanie ruchu
            for idx in indices:
                new_board[idx] = EMPTY
                # player + 1 i EMPTY + 1 (czyli 1)
                new_hash ^= ZOBRIST_TABLE[idx][player + 1] ^ ZOBRIST_TABLE[idx][1]
            for idx in indices:
                new_board[idx + direction_offset] = player
                new_hash ^= ZOBRIST_TABLE[idx + direction_offset][1] ^ ZOBRIST_TABLE[idx + direction_offset][player + 1]

            return new_board, points, is_push, new_hash

        # ==========================================
        # PRZYPADEK B: Ruch w Linii (In-line & Sumito)
        # ==========================================
        else:
            # Ustalenie "przodu" grupy, w zależności od kierunku ruchu
            if direction_offset > 0:
                front_idx = indices[-1]  # Idziemy w górę indeksów (np. wschód)
            else:
                front_idx = indices[0]  # Idziemy w dół indeksów (np. zachód)

            own_count = len(indices)
            enemy_count = 0
            current_idx = front_idx + direction_offset
            enemies_to_push = []

            # Analiza tego, co stoi na drodze
            while 0 <= current_idx < 121:
                piece = self.board[current_idx]

                if piece == player:
                    return None  # Uderzamy we własną kulę! (Ruch nielegalny)

                elif piece == -player:  # Trafiliśmy na wroga
                    enemy_count += 1
                    if enemy_count >= own_count:
                        return None  # Zbyt duża masa wroga (np. 2 własne na 2 wrogie)
                    enemies_to_push.append(current_idx)

                elif piece == EMPTY:
                    break  # Puste miejsce, mamy gdzie popchnąć!

                elif piece == WALL:
                    if enemy_count == 0:
                        return None  # Samobójstwo własnej kuli!
                    # Sukces - zepchnęliśmy wroga ze ściany (ZBICIE / CAPTURE)
                    points = 1
                    break

                current_idx += direction_offset

            if enemy_count > 0:
                is_push = True

            # Wykonanie ruchu In-line na nowej planszy

            # Krok 1: Przesunięcie kul wroga (od najdalszej do najbliższej nam)
            for i in range(len(enemies_to_push) - 1, -1, -1):
                idx = enemies_to_push[i]
                target_idx = idx + direction_offset
                # Jeśli cel to nie ściana (czyli wróg zostaje na planszy), wpisujemy tam kule
                if new_board[target_idx] != WALL:
                    new_board[target_idx] = -player
                    new_hash ^= ZOBRIST_TABLE[target_idx][1] ^ ZOBRIST_TABLE[target_idx][-player + 1]
                
                # Pole na którym stał wróg staje się puste
                new_board[idx] = EMPTY
                new_hash ^= ZOBRIST_TABLE[idx][-player + 1] ^ ZOBRIST_TABLE[idx][1]

            # Krok 2: Usunięcie własnych kul ze starych pozycji
            for idx in indices:
                # Jeśli pole nie zostało jeszcze opróżnione przez przesunięcie wroga
                if new_board[idx] != EMPTY:
                    new_hash ^= ZOBRIST_TABLE[idx][player + 1] ^ ZOBRIST_TABLE[idx][1]
                    new_board[idx] = EMPTY

            # Krok 3: Wpisanie własnych kul na nowe pozycje
            for idx in indices:
                target_idx = idx + direction_offset
                new_hash ^= ZOBRIST_TABLE[target_idx][1] ^ ZOBRIST_TABLE[target_idx][player + 1]
                new_board[target_idx] = player

            return new_board, points, is_push, new_hash


class CoordinateMapper:
    def __init__(self):
        # 1. Definiujemy rzędy planszy Abalone (A-I) i ich legalne kolumny
        # To jest standardowa notacja AGN (Abalone Game Notation)
        self.valid_cells = {
            'A': [1, 2, 3, 4, 5],
            'B': [1, 2, 3, 4, 5, 6],
            'C': [1, 2, 3, 4, 5, 6, 7],
            'D': [1, 2, 3, 4, 5, 6, 7, 8],
            'E': [1, 2, 3, 4, 5, 6, 7, 8, 9],
            'F': [2, 3, 4, 5, 6, 7, 8, 9],
            'G': [3, 4, 5, 6, 7, 8, 9],
            'H': [4, 5, 6, 7, 8, 9],
            'I': [5, 6, 7, 8, 9]
        }

        # Słowniki zapewniające błyskawiczny dostęp O(1) w obie strony
        self.str_to_idx = {}
        self.idx_to_str = {}

        # Budujemy mapowanie przy inicjalizacji
        self._build_maps()

    def _build_maps(self):
        # Mapowanie rzędów I-A na numery 1-9 (I=Top=1, A=Bottom=9)
        # To synchronizuje silnik z frontendem Angularowym (y=-4 dla I, y=4 dla A)
        rows = ['I', 'H', 'G', 'F', 'E', 'D', 'C', 'B', 'A']
        for i, row_char in enumerate(rows):
            row_num = i + 1  # I=1, H=2, ..., A=9
            cols = self.valid_cells[row_char]
            for col_num in cols:
                index = (row_num * 11) + col_num
                coord_str = f"{row_char}{col_num}"
                self.str_to_idx[coord_str] = index
                self.idx_to_str[index] = coord_str

    def to_index(self, coord_str: str) -> int:
        """
        Zamienia string z frontendu (np. 'E5') na indeks w wektorze 11x11.
        Zwraca indeks lub rzuca wyjątek ValueError dla niepoprawnych koordynatów.
        """
        coord_str = coord_str.upper()  # Zabezpieczenie przed błędami z frontendu ('e5' -> 'E5')
        if coord_str not in self.str_to_idx:
            raise ValueError(f"Nielegalne lub nieistniejące pole: {coord_str}")
        return self.str_to_idx[coord_str]

    def to_string(self, index: int) -> str:
        """
        Zamienia indeks z wektora 11x11 na string (np. 60 -> 'E5') dla frontendu.
        """
        if index not in self.idx_to_str:
            raise ValueError(f"Indeks {index} jest poza planszą (np. jest to ŚCIANA/Padding)")
        return self.idx_to_str[index]


# Inicjalizujemy globalny mapper dla całego silnika
mapper = CoordinateMapper()


class AlphaBetaAI:
    def __init__(self, max_depth=3, model_path=None):
        self.max_depth = max_depth
        # Grywalne pola (bez ścian) dla szybszej ewaluacji
        self.playable_indices = [idx for idx, val in enumerate(mapper.idx_to_str.keys())]
        
        # Wagi pozycyjne - im bliżej środka (E5 = indeks 60), tym lepiej.
        self.positional_weights = [0] * 121
        self._precalculate_center_weights()
        
        # Killer Moves: depth -> [move_id1, move_id2]
        self.killer_moves = {}
        # Transposition Table: hash -> {depth, score, flag, best_move_id}
        self.tt = {}
        # PV Table ( pomocnicza do move ordering )
        self.pv_table = {}

        # Flagi dla TT
        self.EXACT = 0
        self.LOWERBOUND = 1
        self.UPPERBOUND = 2

        # NNUE Model Support — CPU only (PyTorch 1.11 nie obsługuje sm_120)
        self.device = torch.device("cpu")
        self.model = None
        if model_path and os.path.exists(model_path):
            from src.agents.web_abalone import AbaloneNNUE
            self.model = AbaloneNNUE().to(self.device)
            try:
                try:
                    state_dict = torch.load(model_path, map_location=self.device, weights_only=True)
                except TypeError:
                    state_dict = torch.load(model_path, map_location=self.device)
                # Oczyszczanie kluczy z prefiksu _orig_mod. (jeśli model był kompilowany)
                new_state_dict = {k.replace("_orig_mod.", ""): v for k, v in state_dict.items()}
                self.model.load_state_dict(new_state_dict)
                self.model.eval()
                print(f"AlphaBetaAI: Załadowano model NNUE z {model_path}")
            except Exception as e:
                print(f"AlphaBetaAI Warning: Nie udało się załadować modelu ({e}). Używam klasycznej oceny.")
                self.model = None

    def _precalculate_center_weights(self):
        center_row, center_col = 5, 5
        self._center_dist = [0] * 121
        for row in range(1, 10):
            for col in range(1, 10):
                idx = (row * 11) + col
                dist = max(
                    abs(row - center_row),
                    abs(col - center_col),
                    abs((row + col) - (center_row + center_col))
                )
                self._center_dist[idx] = dist
                self.positional_weights[idx] = max(0, 1.0 - (dist * 0.2))

    def get_move_id(self, move):
        return (tuple(sorted(move['marbles'])), move['direction'])

    def score_move(self, move, depth, pv_move_id=None):
        move_id = self.get_move_id(move)

        if move['points'] > 0:
            return 1_000_000 + random.random()

        if pv_move_id and move_id == pv_move_id:
            return 900_000 + random.random()

        if depth in self.killer_moves and move_id in self.killer_moves[depth]:
            return 800_000 + random.random()

        if move['is_push'] and len(move['marbles']) == 3:
            return 750_000 + random.random()  # Sumito 3:2

        if move['is_push']:
            return 700_000 + random.random()

        center_diff = sum(
            self.positional_weights[idx + move['direction']] - self.positional_weights[idx]
            for idx in move['marbles']
        )

        if len(move['marbles']) >= 2 and center_diff > 0:
            return 600_000 + center_diff + random.random()

        return center_diff + random.random()

    def evaluate(self, board_array, current_player):
        if self.model is not None:
            # Wszystko liczymy z perspektywy BLACK (tak jak NNUE)
            black_count = 0
            white_count = 0
            black_center = 0.0
            white_center = 0.0
            wall_pressure = 0.0  # pozytywne = WHITE przy krawędzi (dobrze dla BLACK)

            for idx in mapper.idx_to_str.keys():
                piece = board_array[idx]
                if piece == BLACK:
                    black_count += 1
                    black_center += self.positional_weights[idx]
                elif piece == WHITE:
                    white_count += 1
                    white_center += self.positional_weights[idx]
                    wall_n = sum(
                        1 for offset in OFFSETS.values()
                        if 0 <= idx + offset < 121 and board_array[idx + offset] == WALL
                    )
                    wall_pressure += wall_n * 5.0
                if piece == BLACK:
                    wall_n = sum(
                        1 for offset in OFFSETS.values()
                        if 0 <= idx + offset < 121 and board_array[idx + offset] == WALL
                    )
                    wall_pressure -= wall_n * 2.5

            # Sprawdź wygraną/przegraną
            if current_player == BLACK:
                if white_count <= 8: return 1_000_000.0
                if black_count <= 8: return -1_000_000.0
            else:
                if black_count <= 8: return 1_000_000.0
                if white_count <= 8: return -1_000_000.0

            with torch.no_grad():
                board_tensor = torch.tensor(board_array, dtype=torch.float32, device=self.device).unsqueeze(0)
                nnue_score = self.model(board_tensor).item() * 100.0

            center_bonus = black_center - white_center
            marble_diff = (black_count - white_count) * 40.0
            score = nnue_score + center_bonus * 2.0 + wall_pressure + marble_diff
            return score if current_player == BLACK else -score

        my_count = 0
        enemy_count = 0
        score = 0.0

        for idx in mapper.idx_to_str.keys():
            piece = board_array[idx]
            if piece == 0:
                continue

            pos_weight = self.positional_weights[idx]
            same_neighbors = 0
            wall_neighbors = 0

            for offset in OFFSETS.values():
                ni = idx + offset
                if 0 <= ni < 121:
                    nb = board_array[ni]
                    if nb == piece:
                        same_neighbors += 1
                    elif nb == WALL:
                        wall_neighbors += 1

            if piece == current_player:
                my_count += 1
                score += (
                    3.0
                    + pos_weight * 2.5
                    + same_neighbors * 0.5
                    - wall_neighbors * 2.0
                )
            else:
                enemy_count += 1
                # Kule wroga przy krawędzi = okazja do zbicia — nagradzamy agresywnie
                score -= (3.0 + pos_weight * 2.5 + same_neighbors * 0.5)
                score += wall_neighbors * 6.0

        if enemy_count <= 8:
            return 1_000_000.0
        if my_count <= 8:
            return -1_000_000.0

        marble_diff = my_count - enemy_count
        score += marble_diff * 50.0

        # Im większa przewaga, tym bardziej agresywna wycena kulek przy krawędzi
        if marble_diff > 0:
            score += marble_diff * 5.0

        return score

    def get_best_move(self, board_instance, player, history=None, time_limit=5.0):
        self.killer_moves = {}
        _thread_local.deadline = time.time() + time_limit
        best_move = None
        best_val = -float('inf')
        root_scored_moves = []
        start_time = time.time()

        if history is None:
            history = set()

        if board_instance.current_hash == 0:
            board_instance.current_hash = board_instance.get_zobrist_hash(player)

        for current_depth in range(1, self.max_depth + 1):
            if time.time() - start_time >= time_limit:
                break

            alpha = -float('inf')
            beta = float('inf')

            moves = board_instance.generate_legal_moves(player)
            if not moves:
                break

            board_hash = board_instance.current_hash
            entry = self.tt.get(board_hash)
            pv_move_id = entry['move'] if entry else None

            moves.sort(key=lambda m: self.score_move(m, current_depth, pv_move_id), reverse=True)

            temp_best_move = None
            temp_best_val = -float('inf')
            temp_scored = []

            timed_out = False
            for move in moves:
                try:
                    val = -self.negamax_raw(move['new_state'], move['new_hash'], current_depth - 1, -beta, -alpha, -player, history)
                except _SearchTimeout:
                    timed_out = True
                    break
                temp_scored.append((move, val))

                if val > temp_best_val:
                    temp_best_val = val
                    temp_best_move = move

                alpha = max(alpha, temp_best_val)
                if alpha >= beta:
                    break

            if timed_out:
                break

            if temp_best_move is not None:
                best_move = temp_best_move
                best_val = temp_best_val
                root_scored_moves = temp_scored  # keep last complete depth's scores
                self.tt[board_hash] = {
                    'depth': current_depth,
                    'score': best_val,
                    'flag': self.EXACT,
                    'move': self.get_move_id(best_move)
                }

        # Losowość tylko w otwarciu (obie strony mają pełne komplety kulek)
        black_count = board_instance.board.count(BLACK)
        white_count = board_instance.board.count(WHITE)
        is_opening = (black_count == 14 and white_count == 14)
        if is_opening and root_scored_moves and best_val > -float('inf'):
            margin = 1.5
            candidates = [m for m, s in root_scored_moves if s >= best_val - margin]
            if len(candidates) > 1:
                best_move = random.choice(candidates)

        return best_move, best_val, root_scored_moves

    def negamax_raw(self, board_array, board_hash, depth, alpha, beta, player, history):
        # Przerwij jeśli skończył się czas
        if time.time() >= getattr(_thread_local, 'deadline', float('inf')):
            raise _SearchTimeout()

        # 0. Repetition Detection
        if board_hash in history:
            return -50

        alpha_orig = alpha

        # 1. Transposition Table
        entry = self.tt.get(board_hash)
        if entry and entry['depth'] >= depth:
            if entry['flag'] == self.EXACT:
                return entry['score']
            elif entry['flag'] == self.LOWERBOUND:
                alpha = max(alpha, entry['score'])
            elif entry['flag'] == self.UPPERBOUND:
                beta = min(beta, entry['score'])
            if alpha >= beta:
                return entry['score']

        if depth <= 0:
            return self.evaluate(board_array, player)

        temp_board = VectorBoard(initial_setup=False)
        temp_board.board = board_array
        temp_board.current_hash = board_hash

        moves = temp_board.generate_legal_moves(player)
        if not moves:
            return self.evaluate(board_array, player)

        pv_move_id = entry['move'] if entry else None
        moves.sort(key=lambda m: self.score_move(m, depth, pv_move_id), reverse=True)

        best_val = -float('inf')
        best_move_id = None

        history.add(board_hash)
        try:
            for move in moves:
                val = -self.negamax_raw(move['new_state'], move['new_hash'], depth - 1, -beta, -alpha, -player, history)

                if val > best_val:
                    best_val = val
                    best_move_id = self.get_move_id(move)

                alpha = max(alpha, best_val)
                if alpha >= beta:
                    if depth not in self.killer_moves:
                        self.killer_moves[depth] = []
                    if best_move_id not in self.killer_moves[depth]:
                        self.killer_moves[depth].append(best_move_id)
                        if len(self.killer_moves[depth]) > 2:
                            self.killer_moves[depth].pop(0)
                    break
        finally:
            history.discard(board_hash)

        new_entry = {'depth': depth, 'score': best_val, 'move': best_move_id}
        if best_val <= alpha_orig:
            new_entry['flag'] = self.UPPERBOUND
        elif best_val >= beta:
            new_entry['flag'] = self.LOWERBOUND
        else:
            new_entry['flag'] = self.EXACT

        if len(self.tt) > 200_000:
            self.tt.clear()
        self.tt[board_hash] = new_entry
        return best_val


def board_from_state(state_data: dict) -> VectorBoard:
    board = VectorBoard(initial_setup=False)
    for notation, color in state_data.get('board', {}).items():
        try:
            idx = mapper.to_index(notation)
            color_upper = color.upper()
            if color_upper == "BLACK":
                board.board[idx] = BLACK
            elif color_upper == "WHITE":
                board.board[idx] = WHITE
            else:
                board.board[idx] = EMPTY
        except ValueError:
            continue
    board.current_hash = board.get_zobrist_hash(BLACK)
    return board


def get_abalone_move(state: dict, player_val: int, engine: AlphaBetaAI, game_history: set = None) -> dict:
    current_player = state.get("currentPlayer", "").upper()
    phase = state.get("phase", "").upper()
    my_color = "BLACK" if player_val == BLACK else "WHITE"

    if current_player != my_color or phase != "SELECT":
        return {}

    board = board_from_state(state)

    if game_history is not None:
        game_history.add(board.current_hash)

    move, _, _ = engine.get_best_move(board, player_val, history=set(game_history) if game_history else None)

    if move is None:
        return {}

    return {
        "marbles": [mapper.to_string(idx) for idx in move["marbles"]],
        "direction": move["direction_idx"],
    }


class AbaloneAgent(BaseHandler):
    _repeatable = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._game_history: set = set()
        self._lock = threading.Lock()
        try:
            self._engine = AlphaBetaAI(max_depth=3, model_path=abalone_nnue_path)
        except Exception:
            self._engine = AlphaBetaAI(max_depth=3)

    def choose_move(self, data: dict) -> dict:
        if not self._lock.acquire(blocking=False):
            return {}
        try:
            state = data.get("state", {})
            board = state.get("board", {})
            if sum(1 for v in board.values() if v in ("BLACK", "WHITE")) == 28:
                self._engine.tt.clear()
                self._game_history.clear()
            player_val = WHITE if data.get("playerId", 0) == 0 else BLACK
            return get_abalone_move(state, player_val, self._engine, self._game_history)
        except Exception as e:
            print(f"[AbaloneAgent] error: {e}")
            return {}
        finally:
            self._lock.release()

