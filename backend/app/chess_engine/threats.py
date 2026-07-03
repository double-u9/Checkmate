"""Threat detection — identifies tactical threats in a position."""

import chess
from loguru import logger


class ThreatDetector:
    """Detects tactical threats: forks, pins, skewers, hanging pieces, mate threats."""

    def detect_threats(self, board: chess.Board) -> list[dict]:
        """
        Analyze the current position for tactical threats.

        Returns:
            List of threat dicts with type, description, severity, squares
        """
        threats = []
        threats.extend(self._detect_hanging_pieces(board))
        threats.extend(self._detect_forks(board))
        threats.extend(self._detect_pins(board))
        threats.extend(self._detect_mate_threats(board))
        threats.extend(self._detect_discovered_attacks(board))
        return threats

    def _detect_hanging_pieces(self, board: chess.Board) -> list[dict]:
        """Detect undefended pieces that can be captured."""
        threats = []
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece is None:
                continue

            # Check if any opponent piece attacks this square
            attackers = board.attackers(not piece.color, square)
            if attackers:
                defenders = board.attackers(piece.color, square)
                if not defenders and piece.piece_type != chess.KING:
                    sq_name = chess.square_name(square)
                    piece_name = chess.piece_name(piece.piece_type)
                    color = "White" if piece.color == chess.WHITE else "Black"
                    threats.append({
                        "type": "hanging_piece",
                        "description": f"{color}'s {piece_name} on {sq_name} is undefended and can be captured",
                        "severity": "high" if piece.piece_type in (chess.QUEEN, chess.ROOK) else "medium",
                        "squares": [sq_name],
                    })
        return threats

    def _detect_forks(self, board: chess.Board) -> list[dict]:
        """Detect possible forks (one piece attacking multiple valuable targets)."""
        threats = []
        side = board.turn

        for move in board.legal_moves:
            board.push(move)
            moving_piece = board.piece_at(move.to_square)
            if moving_piece:
                attacked = board.attacks(move.to_square)
                valuable_targets = []
                for target_sq in attacked:
                    target = board.piece_at(target_sq)
                    if target and target.color != side:
                        if target.piece_type in (chess.QUEEN, chess.ROOK, chess.KING):
                            valuable_targets.append(target_sq)

                if len(valuable_targets) >= 2:
                    sq_name = chess.square_name(move.to_square)
                    piece_name = chess.piece_name(moving_piece.piece_type)
                    target_names = [chess.square_name(s) for s in valuable_targets]
                    threats.append({
                        "type": "fork",
                        "description": f"{piece_name} on {sq_name} can fork pieces on {', '.join(target_names)}",
                        "severity": "critical",
                        "squares": [sq_name] + target_names,
                    })
            board.pop()

            if len(threats) >= 3:  # Limit for performance
                break

        return threats

    def _detect_pins(self, board: chess.Board) -> list[dict]:
        """Detect absolute and relative pins."""
        threats = []

        for color in [chess.WHITE, chess.BLACK]:
            king_square = board.king(color)
            if king_square is None:
                continue

            # Check for pins along all rays from the king
            for direction in [
                (1, 0), (-1, 0), (0, 1), (0, -1),
                (1, 1), (1, -1), (-1, 1), (-1, -1)
            ]:
                pinned = self._check_pin_ray(board, king_square, direction, color)
                if pinned:
                    threats.append(pinned)

        return threats

    def _check_pin_ray(self, board: chess.Board, king_sq: int, direction: tuple, color: bool) -> dict | None:
        """Check for a pin along a specific ray from the king."""
        king_file = chess.square_file(king_sq)
        king_rank = chess.square_rank(king_sq)

        first_piece = None
        first_square = None

        df, dr = direction
        f, r = king_file + df, king_rank + dr

        while 0 <= f <= 7 and 0 <= r <= 7:
            sq = chess.square(f, r)
            piece = board.piece_at(sq)

            if piece:
                if first_piece is None:
                    if piece.color == color:
                        first_piece = piece
                        first_square = sq
                    else:
                        break  # Enemy piece directly — no pin
                else:
                    # Second piece found — check if it creates a pin
                    if piece.color != color:
                        # Check if this attacker can actually attack along this ray
                        is_diagonal = abs(df) == 1 and abs(dr) == 1
                        can_pin = (
                            piece.piece_type == chess.QUEEN or
                            (piece.piece_type == chess.BISHOP and is_diagonal) or
                            (piece.piece_type == chess.ROOK and not is_diagonal)
                        )
                        if can_pin:
                            pinned_name = chess.square_name(first_square)
                            pinner_name = chess.square_name(sq)
                            piece_name = chess.piece_name(first_piece.piece_type)
                            return {
                                "type": "pin",
                                "description": f"{piece_name} on {pinned_name} is pinned by piece on {pinner_name}",
                                "severity": "high",
                                "squares": [pinned_name, pinner_name],
                            }
                    break
            f += df
            r += dr

        return None

    def _detect_mate_threats(self, board: chess.Board) -> list[dict]:
        """Detect if there's a checkmate threat in 1 or 2 moves."""
        threats = []

        for move in board.legal_moves:
            board.push(move)
            if board.is_checkmate():
                sq_name = chess.square_name(move.to_square)
                threats.append({
                    "type": "mate_threat",
                    "description": f"Checkmate threat with move to {sq_name}!",
                    "severity": "critical",
                    "squares": [chess.square_name(move.from_square), sq_name],
                })
                board.pop()
                break
            board.pop()

        return threats

    def _detect_discovered_attacks(self, board: chess.Board) -> list[dict]:
        """Detect possible discovered attacks."""
        threats = []
        side = board.turn

        for move in list(board.legal_moves)[:30]:  # Sample for performance
            piece = board.piece_at(move.from_square)
            if piece is None:
                continue

            # Check attacks before
            board.push(move)
            # See if moving this piece revealed an attack from a piece behind
            for sq in chess.SQUARES:
                attacker = board.piece_at(sq)
                if attacker and attacker.color == side and sq != move.to_square:
                    attacks_after = board.attacks(sq)
                    board.pop()
                    attacks_before = board.attacks(sq)
                    board.push(move)

                    new_attacks = attacks_after & ~attacks_before
                    for target in new_attacks:
                        target_piece = board.piece_at(target)
                        if target_piece and target_piece.color != side:
                            if target_piece.piece_type in (chess.QUEEN, chess.ROOK, chess.KING):
                                threats.append({
                                    "type": "discovered_attack",
                                    "description": f"Discovered attack on {chess.square_name(target)}",
                                    "severity": "high",
                                    "squares": [chess.square_name(sq), chess.square_name(target)],
                                })
                                board.pop()
                                return threats  # One is enough
            board.pop()

        return threats
