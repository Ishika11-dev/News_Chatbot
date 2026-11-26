export interface DependencyCheck {
  connected: boolean;
  error?: string | null;
}

export interface HealthResponse {
  status: "HEALTHY" | "DEGRADED" | string;
  connected: boolean;
  timestamp: string;
  version: string;
  service: string;
  checks: {
    postgres: DependencyCheck;
    qdrant: DependencyCheck;
  };
}

