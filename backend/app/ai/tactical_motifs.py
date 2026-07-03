"""Tactical motif detector — identifies forks, pins, skewers, sacrifices, etc."""

import chess
from typing import Optional


class TacticalMotifDetector:
    """Detects tactical patterns in a position after a given move."""

    def detect_motifs(self, board: chess.Board, move: chess.Move) -> list[str]:
        """
        Detect tactical motifs created by the given move.

        Args:
            board: Board BEFORE the move
            move: The move to analyze

        Returns:
            List of motif descriptions
        """
        motifs = []

        piece = board.piece_at(move.from_square)
        if piece is None:
            return motifs

        captured = board.piece_at(move.to_square)
        piece_name = chess.piece_name(piece.piece_type)

        # Check captures
        if captured:
            cap_name = chess.piece_name(captured.piece_type)
            cap_value = self._piece_value(captured.piece_type)
            piece_value = self._piece_value(piece.piece_type)

            if piece_value < cap_value:
                motifs.append(f"winning exchange: {piece_name} captures {cap_name}")
            elif piece_value > cap_value:
                motifs.append(f"material sacrifice: {piece_name} captures {cap_name}")
            else:
                motifs.append(f"capture: {piece_name} captures {cap_name}")

        # Apply move
        board_after = board.copy()
        board_after.push(move)

        # Check
        if board_after.is_check():
            if board_after.is_checkmate():
                motifs.append("checkmate!")
            else:
                motifs.append("check — forcing opponent to respond")

        # Fork detection
        fork_targets = self._detect_fork_after(board_after, move.to_square, piece)
        if fork_targets:
            target_names = [chess.piece_name(t.piece_type) for t in fork_targets]
            motifs.append(f"fork — {piece_name} attacks {' and '.join(target_names)}")

        # Pin creation
        pin = self._detect_pin_created(board_after, piece.color)
        if pin:
            motifs.append(pin)

        # Discovered attack
        disc = self._detect_discovered(board, board_after, move, piece.color)
        if disc:
            motifs.append(disc)

        # Promotion
        if move.promotion:
            promo_name = chess.piece_name(move.promotion)
            motifs.append(f"pawn promotion to {promo_name}")

        # En passant
        if board.is_en_passant(move):
            motifs.append("en passant capture")

        # Castling
        if board.is_castling(move):
            side = "kingside" if chess.square_file(move.to_square) > 4 else "queenside"
            motifs.append(f"{side} castling — improving king safety")

        return motifs

    def _detect_fork_after(
        self, board: chess.Board, square: int, piece: chess.Piece
    ) -> list[chess.Piece]:
        """Check if the piece on square is forking multiple valuable pieces."""
        attacks = board.attacks(square)
        targets = []

        for target_sq in attacks:
            target = board.piece_at(target_sq)
            if target and target.color != piece.color:
                if target.piece_type in (chess.QUEEN, chess.ROOK, chess.KING):
                    targets.append(target)
                elif target.piece_type in (chess.BISHOP, chess.KNIGHT) and piece.piece_type == chess.PAWN:
                    targets.append(target)

        return targets if len(targets) >= 2 else []

    def _detect_pin_created(self, board: chess.Board, color: bool) -> Optional[str]:
        """Check if our move created a new pin on an opponent piece."""
        opponent = not color
        king_sq = board.king(opponent)
        if king_sq is None:
            return None

        # Check each opponent piece (excluding king) to see if it's pinned
        for sq in chess.SQUARES:
            piece = board.piece_at(sq)
            if piece and piece.color == opponent and piece.piece_type != chess.KING:
                if board.is_pinned(opponent, sq):
                    # Find the pinner (our piece creating the pin)
                    pin_mask = board.pin(opponent, sq)
                    for pinner_sq in chess.SQUARES:
                        pinner = board.piece_at(pinner_sq)
                        if (pinner and pinner.color == color
                            and pinner.piece_type in (chess.BISHOP, chess.ROOK, chess.QUEEN)
                            and pin_mask & chess.BB_SQUARES[pinner_sq]):
                            pinned_name = chess.piece_name(piece.piece_type)
                            pinner_name = chess.piece_name(pinner.piece_type)
                            return f"pin — {pinner_name} pins {pinned_name} to the king"

        return None

    def _detect_discovered(
        self, board_before: chess.Board, board_after: chess.Board,
        move: chess.Move, color: bool
    ) -> Optional[str]:
        """Detect if moving created a discovered attack."""
        # Check if a piece behind the moved piece now attacks something valuable
        from_sq = move.from_square
        opponent = not color

        for sq in chess.SQUARES:
            piece = board_after.piece_at(sq)
            if piece and piece.color == color and sq != move.to_square:
                attacks_after = board_after.attacks(sq)
                attacks_before = board_before.attacks(sq)
                new_attacks = attacks_after & ~attacks_before

                for target_sq in new_attacks:
                    target = board_after.piece_at(target_sq)
                    if target and target.color == opponent:
                        if target.piece_type in (chess.QUEEN, chess.ROOK, chess.KING):
                            piece_name = chess.piece_name(piece.piece_type)
                            target_name = chess.piece_name(target.piece_type)
                            return f"discovered attack — {piece_name} now targets {target_name}"

        return None

    @staticmethod
    def _piece_value(piece_type: int) -> int:
        """Get standard piece value."""
        values = {
            chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3,
            chess.ROOK: 5, chess.QUEEN: 9, chess.KING: 0,
        }
        return values.get(piece_type, 0)
