export interface BoardDetectionResponse {
  fen: string;
  confidence: number;
  board_detected: boolean;
  squares: SquareDetection[] | null;
  processing_time_ms: number;
}

export interface SquareDetection {
  square: string;
  piece: string;
  confidence: number;
}

export interface MoveEvaluation {
  move_uci: string;
  move_san: string;
  score: number;
  mate_in: number | null;
  is_best: boolean;
  classification: MoveClassification;
}

export type MoveClassification = 'brilliant' | 'excellent' | 'good' | 'inaccuracy' | 'mistake' | 'blunder' | 'best';

export interface ThreatInfo {
  type: string;
  description: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  squares: string[];
}

export interface AnalysisResponse {
  fen: string;
  evaluation: number;
  mate_in: number | null;
  best_move: MoveEvaluation;
  top_lines: MoveEvaluation[][];
  threats: ThreatInfo[];
  explanation: string;
  strategic_themes: string[];
  position_type: 'opening' | 'middlegame' | 'endgame';
  heatmap: number[][] | null;
}

export interface ExplanationResponse {
  move_san: string;
  evaluation_before: number;
  evaluation_after: number;
  explanation: string;
  tactical_motifs: string[];
  strategic_ideas: string[];
  classification: MoveClassification;
}

export interface GameResponse {
  id: string;
  white_name: string;
  black_name: string;
  result: string | null;
  pgn: string | null;
  opening_eco: string | null;
  opening_name: string | null;
  source: string;
  created_at: string;
  move_count: number;
}

export interface ProfileResponse {
  id: string;
  player_name: string;
  style: string | null;
  aggression_score: number;
  risk_tolerance: number;
  tactical_preference: number;
  positional_preference: number;
  endgame_skill: number;
  opening_stats: Record<string, unknown> | null;
  psychological_profile: PsychProfile | null;
  total_games_analyzed: number;
  avg_centipawn_loss: number | null;
}

export interface PsychProfile {
  traits: string[];
  weaknesses: string[];
  recommendations: string[];
  confidence: 'low' | 'moderate' | 'high';
}

export interface WSAnalysisMessage {
  type: 'analysis' | 'no_change' | 'no_board' | 'error';
  fen?: string;
  evaluation?: number;
  mate_in?: number | null;
  best_move?: string;
  explanation?: string;
  threats?: ThreatInfo[];
  heatmap?: number[][];
  processing_time_ms?: number;
  message?: string;
}

export const CLASSIFICATION_COLORS: Record<MoveClassification, string> = {
  brilliant: '#38bdf8',
  excellent: '#34d399',
  good: '#22c55e',
  best: '#60a5fa',
  inaccuracy: '#fbbf24',
  mistake: '#f97316',
  blunder: '#fb7185',
};
