"""Natural Language Generator — creates professional chess commentary.

This is a template-based system, not an AI/LLM. It generates context-aware
explanations by combining move classification, tactical motifs, strategic
themes, and evaluation data into coherent commentary.

For true AI-powered explanations, integrate an LLM (GPT-4, Claude, etc.)
via the generate_move_explanation method.
"""

import random


class ChessNLG:
    """Generates natural-language chess explanations like a professional coach.
    
    Note: This is explicitly template-based NLG, not AI-powered.
    The quality can be dramatically improved by integrating an LLM.
    """

    # Template banks organized by category
    POSITION_TEMPLATES = {
        "decisive_white": [
            "White has a decisive advantage ({score}). The position is winning with correct play — the focus should be on avoiding counterplay and converting efficiently.",
            "With {score} in White's favor, the position is beyond salvation for Black. The task now is technical conversion.",
            "A crushing advantage for White ({score}). Multiple winning continuations exist.",
        ],
        "winning": [
            "The position is clearly favorable. {side} has built a commanding lead with {score} advantage.",
            "{side} dominates this position ({score}). The strategic plan should focus on converting this advantage.",
            "With an evaluation of {score}, {side} is firmly in control of the game.",
        ],
        "slight_edge": [
            "{side} maintains a small but persistent edge ({score}). Precise play is needed to increase pressure.",
            "The position slightly favors {side} ({score}). This is the kind of advantage that requires patient maneuvering.",
            "{side} has a subtle positional advantage ({score}). The key is to avoid premature simplification.",
        ],
        "equal": [
            "The position is dynamically balanced. Both sides have their chances — the next few moves will be critical.",
            "Neither side has a significant advantage here. The game is balanced and wide open.",
            "A complex middlegame with roughly equal chances. Both players must tread carefully.",
            "The evaluation is close to zero: a balanced equilibrium where one inaccuracy could tip the balance.",
        ],
        "losing": [
            "{side} faces a difficult defensive task. The opponent's advantage of {score} is substantial.",
            "The position is critical for {side}. Finding the best defensive resources is essential.",
            "Under significant pressure, {side} must find precise moves to stay in the game.",
        ],
        "decisive_black": [
            "Black has a decisive advantage ({score}). White's position is beyond repair.",
            "With {score} in Black's favor, the position is winning. Black should avoid unnecessary complications.",
        ],
    }

    TACTICAL_TEMPLATES = {
        "fork": [
            "This creates a devastating fork! The {piece} simultaneously attacks multiple targets, winning material.",
            "A classic tactical motif — the {piece} forks two valuable pieces, forcing the opponent into a losing trade.",
            "A double attack by the {piece} — the opponent cannot save both pieces.",
        ],
        "pin": [
            "The pin is a powerful weapon here, restricting the opponent's piece from moving without incurring losses.",
            "By exploiting this pin, {side} gains a significant tactical advantage — the pinned piece is effectively paralyzed.",
            "A devastating pin that ties down the opponent's pieces to defense.",
        ],
        "sacrifice": [
            "A bold sacrifice! Giving up material now yields a crushing attack that more than compensates.",
            "This material investment is sound — the resulting activity and initiative will prove decisive.",
            "A calculated sacrifice that transforms the position. The compensation in activity is overwhelming.",
        ],
        "check": [
            "Check! This forces the opponent to respond immediately, gaining valuable tempo.",
            "This check disrupts the opponent's coordination and creates new tactical possibilities.",
            "An important check that seizes the initiative — the opponent must react defensively.",
        ],
        "mate_threat": [
            "A devastating checkmate threat that demands immediate attention!",
            "The threat of checkmate forces the opponent into a defensive posture, conceding the initiative entirely.",
        ],
        "discovered": [
            "A powerful discovered attack — moving one piece reveals an attack by another, creating a double threat.",
            "The discovered attack catches the opponent off guard, threatening two targets simultaneously.",
        ],
    }

    STRATEGIC_TEMPLATES = {
        "pawn_structure": [
            "The pawn structure here is crucial. {detail}",
            "Pay attention to the pawn formation — {detail}",
        ],
        "king_safety": [
            "King safety is a major factor. {detail}",
            "The exposed king creates tactical vulnerabilities. {detail}",
        ],
        "piece_activity": [
            "Piece coordination is key. {detail}",
            "Active pieces create persistent pressure. {detail}",
        ],
        "space": [
            "Space advantage provides room for maneuvering. {detail}",
            "The spatial superiority allows flexible piece repositioning. {detail}",
        ],
    }

    MOVE_QUALITY_PHRASES = {
        "brilliant": [
            "Brilliant! A move that combines creativity with precision — the kind of play that defines great games.",
            "An exceptional move that demonstrates deep understanding of the position's hidden potential.",
            "Masterful play — this unexpected resource completely transforms the game.",
        ],
        "excellent": [
            "An excellent choice that maintains the advantage while creating new threats.",
            "Strong play — this move improves the position on multiple fronts simultaneously.",
            "A high-quality move that keeps the pressure on while minimizing counterplay.",
        ],
        "good": [
            "A solid move that keeps the position under control.",
            "A reasonable continuation that maintains the balance of the position.",
            "Sound play — this move consolidates the position without taking unnecessary risks.",
        ],
        "best": [
            "The engine's top choice — this move is objectively the strongest continuation.",
            "The most precise move in the position, maintaining maximum advantage.",
        ],
        "inaccuracy": [
            "A small inaccuracy. While not losing, a more precise continuation was available.",
            "Not the most accurate move. The advantage slips slightly — the opponent gets new defensive resources.",
            "A minor imprecision that gives the opponent breathing room.",
        ],
        "mistake": [
            "A significant mistake that shifts the balance of the position.",
            "This move overlooks a tactical nuance and costs valuable ground.",
            "An error that allows the opponent to equalize or seize the initiative.",
        ],
        "blunder": [
            "A serious blunder that dramatically changes the evaluation!",
            "A critical error — the position goes from manageable to dire after this move.",
            "A game-changing mistake. The advantage swings decisively to the opponent.",
        ],
    }

    TRANSITION_PHRASES = [
        "Meanwhile,",
        "Additionally,",
        "Furthermore,",
        "On the other hand,",
        "Notably,",
        "It's worth noting that",
    ]

    def generate_position_commentary(self, score: float, side_to_move: str) -> str:
        """Generate commentary about the current position."""
        abs_score = abs(score)

        if score > 5.0:
            category = "decisive_white"
            side = "White"
        elif score > 2.0:
            category = "winning"
            side = "White"
        elif score > 0.3:
            category = "slight_edge"
            side = "White"
        elif score < -5.0:
            category = "decisive_black"
            side = "Black"
        elif score < -2.0:
            category = "winning"
            side = "Black"
        elif score < -0.3:
            category = "slight_edge"
            side = "Black"
        else:
            category = "equal"
            side = ""

        template = random.choice(self.POSITION_TEMPLATES[category])
        score_str = f"+{abs_score:.1f}" if score > 0 else f"-{abs_score:.1f}"
        return template.format(side=side, score=score_str)

    def generate_move_explanation(
        self,
        move_san: str,
        classification: str,
        tactical_motifs: list[str],
        strategic_ideas: list[str],
        score_before: float,
        score_after: float,
    ) -> str:
        """Generate a full explanation of a move.
        
        This method is the integration point for a future LLM replacement.
        The template-based approach can be swapped with an LLM call here.
        """
        parts = []

        # Move quality assessment
        quality_phrases = self.MOVE_QUALITY_PHRASES.get(classification, ["A standard move."])
        quality_phrase = random.choice(quality_phrases)
        parts.append(f"**{move_san}** — {quality_phrase}")

        # Tactical motifs — these are specific and informative
        for motif in tactical_motifs[:2]:
            parts.append(motif.capitalize() + ".")

        # Strategic ideas
        if strategic_ideas:
            transition = random.choice(self.TRANSITION_PHRASES)
            for i, idea in enumerate(strategic_ideas[:2]):
                if i == 0:
                    parts.append(f"{transition} {idea.lower()}.")
                else:
                    parts.append(idea + ".")

        # Evaluation change — contextual commentary
        delta = score_after - score_before
        if abs(delta) > 1.5:
            if delta > 0:
                parts.append(f"The evaluation swings dramatically from {score_before:+.1f} to {score_after:+.1f} — a game-changing moment.")
            else:
                parts.append(f"A significant evaluation drop from {score_before:+.1f} to {score_after:+.1f} — this changes the character of the position.")
        elif abs(delta) > 0.3:
            direction = "improves" if delta > 0 else "worsens"
            parts.append(
                f"The evaluation {direction} from {score_before:+.1f} to {score_after:+.1f}."
            )

        return " ".join(parts)

    def generate_tactical_commentary(self, motifs: list[str]) -> str:
        """Generate commentary about tactical motifs."""
        if not motifs:
            return "No immediate tactical threats in this position — the struggle is positional."

        comments = []
        for motif in motifs[:3]:
            motif_lower = motif.lower()
            if "fork" in motif_lower:
                comments.append(random.choice(self.TACTICAL_TEMPLATES["fork"]).format(
                    piece="piece", side="the attacker"
                ))
            elif "pin" in motif_lower:
                comments.append(random.choice(self.TACTICAL_TEMPLATES["pin"]).format(side="the attacker"))
            elif "sacrifice" in motif_lower:
                comments.append(random.choice(self.TACTICAL_TEMPLATES["sacrifice"]))
            elif "check" in motif_lower:
                comments.append(random.choice(self.TACTICAL_TEMPLATES["check"]))
            elif "discover" in motif_lower:
                comments.append(random.choice(self.TACTICAL_TEMPLATES["discovered"]))
            else:
                comments.append(motif)

        return " ".join(comments)
