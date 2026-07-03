"""Strategic position analyzer — pawn structure, king safety, piece activity."""

import chess


class StrategicAnalyzer:
    """Analyzes positional/strategic factors in a chess position."""

    def analyze(self, board: chess.Board) -> dict:
        """
        Full strategic analysis of a position.

        Returns:
            Dict with pawn_structure, king_safety, piece_activity, space, themes
        """
        return {
            "pawn_structure": self._analyze_pawn_structure(board),
            "king_safety": self._analyze_king_safety(board),
            "piece_activity": self._analyze_piece_activity(board),
            "space": self._analyze_space(board),
            "themes": self._identify_themes(board),
        }

    def _analyze_pawn_structure(self, board: chess.Board) -> dict:
        """Analyze pawn structure for both sides."""
        result = {"white": {}, "black": {}}

        for color, name in [(chess.WHITE, "white"), (chess.BLACK, "black")]:
            pawns = board.pieces(chess.PAWN, color)
            isolated = []
            doubled = []
            passed = []
            backward = []

            for sq in pawns:
                file = chess.square_file(sq)
                rank = chess.square_rank(sq)

                # Isolated: no friendly pawns on adjacent files
                adj_files = [f for f in [file - 1, file + 1] if 0 <= f <= 7]
                has_neighbor = any(
                    chess.square(f, r) in pawns for f in adj_files for r in range(8)
                )
                if not has_neighbor:
                    isolated.append(chess.square_name(sq))

                # Doubled: multiple pawns on same file
                same_file = [s for s in pawns if chess.square_file(s) == file and s != sq]
                if same_file:
                    doubled.append(chess.square_name(sq))

                # Passed: no opponent pawns can block or capture
                opponent_pawns = board.pieces(chess.PAWN, not color)
                blocking_files = [f for f in [file - 1, file, file + 1] if 0 <= f <= 7]
                is_passed = True
                for opp_sq in opponent_pawns:
                    opp_file = chess.square_file(opp_sq)
                    opp_rank = chess.square_rank(opp_sq)
                    if opp_file in blocking_files:
                        if color == chess.WHITE and opp_rank > rank:
                            is_passed = False
                            break
                        elif color == chess.BLACK and opp_rank < rank:
                            is_passed = False
                            break
                if is_passed:
                    passed.append(chess.square_name(sq))

            result[name] = {
                "count": len(pawns),
                "isolated": isolated,
                "doubled": doubled,
                "passed": passed,
            }

        return result

    def _analyze_king_safety(self, board: chess.Board) -> dict:
        """Analyze king safety for both sides."""
        result = {}

        for color, name in [(chess.WHITE, "white"), (chess.BLACK, "black")]:
            king_sq = board.king(color)
            if king_sq is None:
                result[name] = {"score": 0, "details": "no king"}
                continue

            score = 10  # Start at max safety
            details = []

            king_file = chess.square_file(king_sq)
            king_rank = chess.square_rank(king_sq)

            # Castled bonus
            if king_file in [1, 2, 6] and (
                (color == chess.WHITE and king_rank == 0) or
                (color == chess.BLACK and king_rank == 7)
            ):
                details.append("castled")
            else:
                score -= 2
                if king_file in [3, 4]:
                    details.append("king in center (vulnerable)")
                    score -= 2

            # Pawn shield
            pawns = board.pieces(chess.PAWN, color)
            shield_rank = king_rank + (1 if color == chess.WHITE else -1)
            shield_files = [f for f in [king_file - 1, king_file, king_file + 1] if 0 <= f <= 7]

            if 0 <= shield_rank <= 7:
                shield_pawns = sum(
                    1 for f in shield_files
                    if chess.square(f, shield_rank) in pawns
                )
                if shield_pawns >= 2:
                    details.append("good pawn shield")
                elif shield_pawns == 1:
                    score -= 1
                    details.append("partial pawn shield")
                else:
                    score -= 3
                    details.append("no pawn shield")

            # Attackers near king
            enemy_attackers = len(board.attackers(not color, king_sq))
            score -= enemy_attackers

            result[name] = {
                "score": max(0, min(10, score)),
                "details": ", ".join(details) if details else "neutral",
            }

        return result

    def _analyze_piece_activity(self, board: chess.Board) -> dict:
        """Measure piece mobility and centralization."""
        result = {}

        for color, name in [(chess.WHITE, "white"), (chess.BLACK, "black")]:
            total_mobility = 0
            centralized = 0

            # Temporarily set turn to this color to count legal moves
            temp = board.copy()
            temp.turn = color

            for sq in chess.SQUARES:
                piece = board.piece_at(sq)
                if piece and piece.color == color and piece.piece_type != chess.KING:
                    attacks = len(board.attacks(sq))
                    total_mobility += attacks

                    # Central squares bonus
                    file = chess.square_file(sq)
                    rank = chess.square_rank(sq)
                    if 2 <= file <= 5 and 2 <= rank <= 5:
                        centralized += 1

            result[name] = {
                "mobility": total_mobility,
                "centralized_pieces": centralized,
            }

        return result

    def _analyze_space(self, board: chess.Board) -> dict:
        """Count controlled squares for each side."""
        white_control = 0
        black_control = 0

        for sq in chess.SQUARES:
            w = len(board.attackers(chess.WHITE, sq))
            b = len(board.attackers(chess.BLACK, sq))
            if w > b:
                white_control += 1
            elif b > w:
                black_control += 1

        return {
            "white": white_control,
            "black": black_control,
            "advantage": "White" if white_control > black_control else "Black" if black_control > white_control else "Equal",
        }

    def _identify_themes(self, board: chess.Board) -> list[str]:
        """Identify key strategic themes."""
        themes = []
        ps = self._analyze_pawn_structure(board)

        if ps["white"]["passed"] or ps["black"]["passed"]:
            themes.append("passed pawn play")
        if ps["white"]["isolated"] or ps["black"]["isolated"]:
            themes.append("isolated pawn weakness")

        # Bishop pair
        for color, name in [(chess.WHITE, "White"), (chess.BLACK, "Black")]:
            if len(board.pieces(chess.BISHOP, color)) >= 2:
                themes.append(f"{name} has the bishop pair")

        # Open position
        total_pawns = len(board.pieces(chess.PAWN, chess.WHITE)) + len(board.pieces(chess.PAWN, chess.BLACK))
        if total_pawns <= 8:
            themes.append("open position favoring bishops and rooks")
        elif total_pawns >= 14:
            themes.append("closed position favoring knights")

        return themes
