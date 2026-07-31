export type WorkflowStatus = "started" | "succeeded" | "failed" | "denied" | "skipped";

export type WorkflowNode = {
  node_id: string;
  label: string;
  kind: string;
  status: WorkflowStatus;
  started_sequence: number;
  completed_sequence: number | null;
  duration_ms: number | null;
};

export type WorkflowEdge = {
  source: string;
  target: string;
};

export type WorkflowEvent = {
  event_id: string;
  sequence: number;
  type: string;
  status: WorkflowStatus;
  actor_type: string;
  actor_name: string;
  timestamp: string;
  duration_ms: number | null;
  parent_event_id: string | null;
  correlation_id: string;
  data: Record<string, unknown>;
};

export type WorkflowReplay = {
  mapping_version: "workflow-event-mapping-v1";
  run_id: string;
  correlation_id: string;
  last_sequence: number;
  final_event_type: string;
  catalog_version: string | null;
  skill_id: string | null;
  skill_version: string | null;
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
  timeline: WorkflowEvent[];
};
