"""Chess utility functions."""

import chess
import chess.pgn
import io


def fen_to_board_ascii(fen: str) -> str:
    """Convert FEN to a human-readable ASCII board."""
    try:
        board = chess.Board(fen)
        return str(board)
    except ValueError:
        return "Invalid FEN"


def pgn_to_moves(pgn_str: str) -> list[dict]:
    """Parse PGN and extract all moves with FEN positions."""
    pgn_io = io.StringIO(pgn_str)
    game = chess.pgn.read_game(pgn_io)
    if game is None:
        return []

    moves = []
    board = game.board()

    for node in game.mainline():
        move = node.move
        san = board.san(move)
        moves.append({
            "move_number": board.fullmove_number,
            "side": "white" if board.turn == chess.WHITE else "black",
            "move_uci": move.uci(),
            "move_san": san,
            "fen_before": board.fen(),
        })
        board.push(move)

    return moves


def validate_fen(fen: str) -> tuple[bool, str]:
    """Validate a FEN string and return (is_valid, error_message)."""
    try:
        board = chess.Board(fen)
        if board.is_valid():
            return True, ""
        else:
            return False, "Position is not legal"
    except ValueError as e:
        return False, str(e)
