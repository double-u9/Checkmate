"""Opponent Profiler — analyzes play style, aggression, risk, and psychology."""

import chess
import chess.pgn
import io
import numpy as np
from loguru import logger
from typing import Optional


class OpponentProfiler:
    """
    Profiles an opponent's playing style from their game history.
    Detects: aggression, risk tolerance, tactical vs positional preference,
    opening habits, and generates a psychological profile.
    """

    # Opening classification by ECO code prefix
    OPENING_STYLES = {
        "aggressive": ["B", "C"],   # Sicilian, King's Pawn openings
        "positional": ["D", "E"],    # Queen's Pawn, Indian systems
        "solid": ["A"],              # Flank openings
    }

    async def analyze(self, player_name: str, pgn_games: list[str]) -> dict:
        """
        Analyze multiple games to build an opponent profile.

        Args:
            player_name: Name of the player to profile
            pgn_games: List of PGN game strings

        Returns:
            Profile data dict
        """
        all_features = []

        for pgn_str in pgn_games:
            try:
                features = self._extract_game_features(pgn_str, player_name)
                if features:
                    all_features.append(features)
            except Exception as e:
                logger.warning(f"Failed to parse game: {e}")

        if not all_features:
            return self._default_profile()

        # Aggregate features
        profile = self._aggregate_features(all_features)

        # Classify style
        profile["style"] = self._classify_style(profile)

        # Generate psychological profile
        profile["psychological_profile"] = self._generate_psych_profile(profile)

        # Opening stats
        profile["opening_stats"] = self._aggregate_opening_stats(all_features)

        return profile

    def _extract_game_features(self, pgn_str: str, player_name: str) -> Optional[dict]:
        """Extract behavioral features from a single game."""
        pgn_io = io.StringIO(pgn_str)
        game = chess.pgn.read_game(pgn_io)
        if game is None:
            return None

        # Determine if player is White or Black
        white = game.headers.get("White", "")
        black = game.headers.get("Black", "")

        if player_name.lower() in white.lower():
            player_color = chess.WHITE
        elif player_name.lower() in black.lower():
            player_color = chess.BLACK
        else:
            return None

        board = game.board()
        features = {
            "captures": 0,
            "checks": 0,
            "castled": False,
            "castling_side": None,
            "piece_sacrifices": 0,
            "pawn_advances": 0,
            "center_moves": 0,
            "king_moves": 0,
            "total_moves": 0,
            "early_queen_moves": 0,
            "exchanges_initiated": 0,
            "opening_eco": game.headers.get("ECO", ""),
            "result": game.headers.get("Result", "*"),
        }

        move_num = 0
        material_balance = 0
        prev_material = self._count_material(board)

        for node in game.mainline():
            move = node.move
            is_player_move = board.turn == player_color

            if is_player_move:
                features["total_moves"] += 1
                move_num += 1

                # Captures
                if board.is_capture(move):
                    features["captures"] += 1

                    # Check for sacrifice
                    moving_piece = board.piece_at(move.from_square)
                    captured_piece = board.piece_at(move.to_square)
                    if moving_piece and captured_piece:
                        if self._piece_value(moving_piece.piece_type) > self._piece_value(captured_piece.piece_type):
                            features["piece_sacrifices"] += 1

                # Checks
                board.push(move)
                if board.is_check():
                    features["checks"] += 1
                board.pop()

                # Castling
                if board.is_castling(move):
                    features["castled"] = True
                    features["castling_side"] = "kingside" if chess.square_file(move.to_square) > 4 else "queenside"

                # Pawn advances
                piece = board.piece_at(move.from_square)
                if piece and piece.piece_type == chess.PAWN:
                    features["pawn_advances"] += 1

                # Center control
                to_file = chess.square_file(move.to_square)
                to_rank = chess.square_rank(move.to_square)
                if 2 <= to_file <= 5 and 2 <= to_rank <= 5:
                    features["center_moves"] += 1

                # Early queen moves
                if piece and piece.piece_type == chess.QUEEN and move_num <= 10:
                    features["early_queen_moves"] += 1

                # King moves (non-castling)
                if piece and piece.piece_type == chess.KING and not board.is_castling(move):
                    features["king_moves"] += 1

            board.push(move)

            # Track material exchanges
            curr_material = self._count_material(board)
            if curr_material < prev_material and is_player_move:
                features["exchanges_initiated"] += 1
            prev_material = curr_material

        return features

    def _aggregate_features(self, all_features: list[dict]) -> dict:
        """Aggregate features across multiple games into profile scores."""
        n = len(all_features)

        # Normalize per-game averages
        avg_captures = np.mean([f["captures"] / max(f["total_moves"], 1) for f in all_features])
        avg_checks = np.mean([f["checks"] / max(f["total_moves"], 1) for f in all_features])
        avg_sacrifices = np.mean([f["piece_sacrifices"] for f in all_features])
        avg_center = np.mean([f["center_moves"] / max(f["total_moves"], 1) for f in all_features])
        avg_exchanges = np.mean([f["exchanges_initiated"] / max(f["total_moves"], 1) for f in all_features])
        castled_ratio = np.mean([1 if f["castled"] else 0 for f in all_features])
        avg_king_moves = np.mean([f["king_moves"] / max(f["total_moves"], 1) for f in all_features])

        # Calculate scores (0-1 range)
        aggression = min(1.0, (avg_captures * 3 + avg_checks * 5 + avg_sacrifices * 0.3) / 2)
        risk_tolerance = min(1.0, (avg_sacrifices * 0.5 + (1 - castled_ratio) * 0.3 + avg_king_moves * 3))
        tactical_pref = min(1.0, (avg_captures * 3 + avg_checks * 5 + avg_sacrifices * 0.3) / 1.5)
        positional_pref = min(1.0, avg_center * 3 + castled_ratio * 0.3)

        # P13 fix: Calculate endgame skill from actual game features.
        # Heuristic: Good endgame players have active king play (high king_moves)
        # in longer games, plus high pawn activity and capture efficiency.
        # We use king activity + game length + pawn advancement ratio as proxies.
        avg_game_length = np.mean([f["total_moves"] for f in all_features])
        length_factor = min(1.0, avg_game_length / 40.0)  # Longer games suggest endgame reach
        king_activity = min(1.0, avg_king_moves * 8)  # Active king play in endgames
        pawn_ratio = np.mean([f["pawn_advances"] / max(f["total_moves"], 1) for f in all_features])
        exchange_factor = min(1.0, avg_exchanges * 6)  # Willingness to simplify

        # Endgame skill is a weighted combination of these heuristics
        endgame_skill = min(1.0, (
            king_activity * 0.35 +
            length_factor * 0.25 +
            pawn_ratio * 2.0 * 0.2 +
            exchange_factor * 0.2
        ))

        return {
            "aggression_score": round(float(aggression), 3),
            "risk_tolerance": round(float(risk_tolerance), 3),
            "tactical_preference": round(float(tactical_pref), 3),
            "positional_preference": round(float(positional_pref), 3),
            "endgame_skill": round(float(endgame_skill), 3),
        }

    def _classify_style(self, profile: dict) -> str:
        """Classify playing style based on profile scores."""
        agg = profile["aggression_score"]
        tac = profile["tactical_preference"]
        pos = profile["positional_preference"]

        if agg > 0.7 and tac > 0.6:
            return "attacker"
        elif pos > 0.6 and agg < 0.4:
            return "positional"
        elif agg < 0.3 and tac < 0.4:
            return "defender"
        else:
            return "universal"

    def _generate_psych_profile(self, profile: dict) -> dict:
        """Generate a psychological profile from the stats."""
        agg = profile["aggression_score"]
        risk = profile["risk_tolerance"]
        tac = profile["tactical_preference"]
        pos = profile["positional_preference"]

        traits = []
        if agg > 0.7:
            traits.append("Highly aggressive — prefers sharp, tactical positions")
        elif agg > 0.4:
            traits.append("Balanced approach — adapts between tactical and quiet play")
        else:
            traits.append("Conservative — prefers solid, low-risk positions")

        if risk > 0.6:
            traits.append("Risk-taker — willing to sacrifice material for initiative")
        else:
            traits.append("Risk-averse — prioritizes safety and material balance")

        if tac > pos + 0.2:
            traits.append("Tactical player — looks for combinations and forcing moves")
        elif pos > tac + 0.2:
            traits.append("Positional player — values pawn structure and piece placement")
        else:
            traits.append("Versatile — comfortable in both tactical and positional play")

        # Weaknesses
        weaknesses = []
        if risk > 0.7:
            weaknesses.append("May overextend in pursuit of attack")
        if agg < 0.3:
            weaknesses.append("Can be passive against sharp openings")
        if profile.get("endgame_skill", 0.5) < 0.4:
            weaknesses.append("Endgame technique may be a weakness")

        # Recommendations
        recommendations = []
        if agg > 0.6:
            recommendations.append("Play solidly — deny tactical opportunities")
            recommendations.append("Trade queens early to neutralize attacking ambitions")
        else:
            recommendations.append("Create complications — force tactical decisions")
            recommendations.append("Avoid simplified positions where patience is rewarded")

        return {
            "traits": traits,
            "weaknesses": weaknesses,
            "recommendations": recommendations,
            "confidence": "high" if len(traits) >= 3 else "moderate",
        }

    def _aggregate_opening_stats(self, all_features: list[dict]) -> dict:
        """Aggregate opening preferences."""
        openings = {}
        for f in all_features:
            eco = f.get("opening_eco", "")
            if eco:
                prefix = eco[0] if eco else "?"
                openings[prefix] = openings.get(prefix, 0) + 1

        total = sum(openings.values()) or 1
        return {
            "distribution": {k: round(v / total, 2) for k, v in openings.items()},
            "total_games": len(all_features),
            "preferred_type": max(openings, key=openings.get) if openings else "unknown",
        }

    def _default_profile(self) -> dict:
        """Return a default profile when no games are available."""
        return {
            "style": "unknown",
            "aggression_score": 0.5,
            "risk_tolerance": 0.5,
            "tactical_preference": 0.5,
            "positional_preference": 0.5,
            "endgame_skill": 0.5,
            "opening_stats": {},
            "psychological_profile": {
                "traits": ["Insufficient data for analysis"],
                "weaknesses": [],
                "recommendations": ["Gather more game data for accurate profiling"],
                "confidence": "low",
            },
        }

    @staticmethod
    def _piece_value(piece_type: int) -> int:
        values = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3, chess.ROOK: 5, chess.QUEEN: 9, chess.KING: 0}
        return values.get(piece_type, 0)

    @staticmethod
    def _count_material(board: chess.Board) -> int:
        total = 0
        for sq in chess.SQUARES:
            piece = board.piece_at(sq)
            if piece and piece.piece_type != chess.KING:
                total += OpponentProfiler._piece_value(piece.piece_type)
        return total
