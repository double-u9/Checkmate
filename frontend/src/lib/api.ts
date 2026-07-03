/* API client for Aethelred backend */

import type { AnalysisResponse, BoardDetectionResponse, ExplanationResponse, GameResponse, ProfileResponse } from './types';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class AethelredAPI {
  private baseUrl: string;

  constructor(baseUrl: string = API_URL) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(path: string, options?: RequestInit): Promise<T> {
    const res = await fetch(`${this.baseUrl}${path}`, {
      headers: { 'Content-Type': 'application/json', ...options?.headers },
      ...options,
    });
    if (!res.ok) {
      const error = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(error.detail || 'API request failed');
    }
    return res.json();
  }

  // Vision
  async detectBoard(file: File): Promise<BoardDetectionResponse> {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${this.baseUrl}/api/v1/vision/detect`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) throw new Error('Board detection failed');
    return res.json();
  }

  async detectBoardBase64(imageData: string): Promise<BoardDetectionResponse> {
    return this.request('/api/v1/vision/detect-base64', {
      method: 'POST',
      body: JSON.stringify({ image: imageData }),
    });
  }

  // Analysis
  async analyzePosition(fen: string, depth = 20, numLines = 3): Promise<AnalysisResponse> {
    return this.request('/api/v1/analysis/position', {
      method: 'POST',
      body: JSON.stringify({ fen, depth, num_lines: numLines }),
    });
  }

  async explainMove(fen: string, moveUci: string, depth = 20): Promise<ExplanationResponse> {
    return this.request('/api/v1/analysis/explain', {
      method: 'POST',
      body: JSON.stringify({ fen, move_uci: moveUci, depth }),
    });
  }

  // Games
  async createGame(whiteName = 'White', blackName = 'Black', source = 'manual'): Promise<GameResponse> {
    return this.request('/api/v1/games/', {
      method: 'POST',
      body: JSON.stringify({ white_name: whiteName, black_name: blackName, source }),
    });
  }

  async getGame(gameId: string): Promise<GameResponse> {
    return this.request(`/api/v1/games/${gameId}`);
  }

  async addMove(gameId: string, fen: string, moveUci?: string, moveSan?: string) {
    return this.request(`/api/v1/games/${gameId}/moves`, {
      method: 'PUT',
      body: JSON.stringify({ fen, move_uci: moveUci, move_san: moveSan }),
    });
  }

  async exportPgn(gameId: string): Promise<{ pgn: string }> {
    return this.request(`/api/v1/games/${gameId}/pgn`);
  }

  // Profiles
  async analyzeProfile(playerName: string, pgnGames: string[]): Promise<ProfileResponse> {
    return this.request('/api/v1/profiles/analyze', {
      method: 'POST',
      body: JSON.stringify({ player_name: playerName, pgn_games: pgnGames }),
    });
  }

  async getProfile(profileId: string): Promise<ProfileResponse> {
    return this.request(`/api/v1/profiles/${profileId}`);
  }

  // Health
  async health(): Promise<{ status: string }> {
    return this.request('/health');
  }
}

export const api = new AethelredAPI();
export default api;
