export interface HealthResponse {
  status: "ok";
  service: string;
  environment: string;
  database: "ready";
}
