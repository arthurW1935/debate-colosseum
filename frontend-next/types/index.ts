export type RunStatus = 'running' | 'awaiting_review' | 'completed' | 'error';
export type Recommendation = 'proceed' | 'proceed-with-caution' | 'do-not-proceed';
export type AgentRole = 'growth' | 'finance' | 'risk';

export interface RiskItem {
  description: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  likelihood: 'low' | 'medium' | 'high';
  mitigation?: string;
}

export interface ExpertAnalysis {
  agent_role: AgentRole;
  round: '1' | '2' | 'feedback';
  recommendation: Recommendation;
  confidence: number;
  summary: string;
  key_assumptions: string[];
  supporting_evidence: string[];
  risks: RiskItem[];
  dissent_notes?: string;
}

export interface DecisionMemo {
  executive_summary: string;
  recommendation: Recommendation;
  confidence: number;
  expert_positions: ExpertAnalysis[];
  key_agreements: string[];
  key_disagreements: string[];
  arbitration_summary?: string;
  risk_register: RiskItem[];
  next_steps: string[];
  generated_at: string;
  feedback_revision_count: number;
}

export interface RunStatusResponse {
  run_id: string;
  status: RunStatus;
  current_turn: number;
  feedback_round: number;
  guardrail_passed: boolean;
  final_memo?: DecisionMemo;
  action_status?: string;
  error?: string;
}

export interface StoredRun {
  run_id: string;
  problem_statement: string;
  created_at: string;
  status: RunStatus;
}

export interface MemoVersion {
  memo: DecisionMemo;
  version: number;
  feedbackText?: string;
}
