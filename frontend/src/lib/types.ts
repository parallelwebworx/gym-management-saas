export interface Paginated<T> {
  results: T[];
  count: number;
  page: number;
  num_pages: number;
  page_size: number;
}

export type Gender = "male" | "female" | "other" | "unspecified";

export interface Member {
  id: number;
  full_name: string;
  phone: string;
  email: string;
  gender: Gender;
  date_of_birth: string | null;
  address: string;
  notes: string;
  branch: number | null;
  created_at: string;
  updated_at: string;
}

export type PlanType = "general" | "cardio" | "gym_cardio" | "custom";

export interface Plan {
  id: number;
  name: string;
  plan_type: PlanType;
  duration_days: number;
  price_paise: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export type AddOnType = "one_time" | "recurring";

export interface AddOn {
  id: number;
  name: string;
  addon_type: AddOnType;
  price_paise: number;
  auto_apply_on_first_enrollment: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ImportRow {
  row: number;
  full_name: string;
  phone: string;
  status: "ok" | "error" | "duplicate_in_file" | "duplicate_existing";
  errors: string[];
}

export interface ImportResult {
  committed: boolean;
  inserted: number;
  summary: { total: number; valid: number; errors: number; duplicates: number };
  rows: ImportRow[];
}
