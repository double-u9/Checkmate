"""FEN generator — converts classified board grid to FEN notation."""

import chess
from loguru import logger


class FENGenerator:
    """Converts a classified 8x8 piece grid into a valid FEN string."""

    def generate(
        self,
        grid: list[list[tuple[str, float]]],
        active_color: str = "w",
        castling: str = "KQkq",
        en_passant: str = "-",
        halfmove: int = 0,
        fullmove: int = 1,
    ) -> str:
        """
        Generate FEN from classified grid.

        Args:
            grid: 8x8 list of (piece_symbol, confidence) tuples
                  grid[0][0] = a8, grid[7][7] = h1
            active_color: "w" or "b"
            castling: Castling availability string
            en_passant: En passant target square or "-"
            halfmove: Halfmove clock
            fullmove: Fullmove number

        Returns:
            Complete FEN string
        """
        ranks = []
        for row in grid:
            rank_str = ""
            empty_count = 0

            for piece_symbol, confidence in row:
                if piece_symbol == ".":
                    empty_count += 1
                else:
                    if empty_count > 0:
                        rank_str += str(empty_count)
                        empty_count = 0
                    rank_str += piece_symbol

            if empty_count > 0:
                rank_str += str(empty_count)

            ranks.append(rank_str)

        position = "/".join(ranks)
        fen = f"{position} {active_color} {castling} {en_passant} {halfmove} {fullmove}"

        # Validate with python-chess
        if self.validate(fen):
            logger.debug(f"Generated valid FEN: {fen}")
            return fen
        else:
            logger.warning(f"Generated FEN failed validation: {fen}")
            # Try to fix common issues
            fixed = self._attempt_fix(fen)
            if fixed:
                return fixed
            return fen  # Return anyway, let downstream handle it

    @staticmethod
    def validate(fen: str) -> bool:
        """Check if a FEN string represents a valid chess position."""
        try:
            board = chess.Board(fen)
            return board.is_valid()
        except (ValueError, Exception):
            return False

    def _attempt_fix(self, fen: str) -> str | None:
        """Attempt to fix common FEN issues."""
        parts = fen.split(" ")
        if len(parts) < 6:
            return None

        position = parts[0]

        # Ensure each rank has exactly 8 squares
        ranks = position.split("/")
        if len(ranks) != 8:
            return None

        fixed_ranks = []
        for rank in ranks:
            count = 0
            for ch in rank:
                if ch.isdigit():
                    count += int(ch)
                elif ch in "pnbrqkPNBRQK":
                    count += 1
            if count != 8:
                # Pad with empty squares
                diff = 8 - count
                if diff > 0:
                    rank += str(diff)
                else:
                    return None
            fixed_ranks.append(rank)

        parts[0] = "/".join(fixed_ranks)
        fixed_fen = " ".join(parts)

        if self.validate(fixed_fen):
            logger.info(f"Fixed FEN: {fixed_fen}")
            return fixed_fen

        return None
