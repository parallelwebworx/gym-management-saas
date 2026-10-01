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

export type MembershipStatus = "active" | "expired" | "cancelled";

export interface MembershipAddOn {
  id: number;
  addon: number;
  name: string;
  addon_type: string;
  price_paise: number;
  auto_applied: boolean;
}

export interface Membership {
  id: number;
  member: number;
  member_name: string;
  plan: number;
  plan_name: string;
  duration_days: number;
  plan_price_paise: number;
  start_date: string;
  end_date: string;
  original_end_date: string;
  status: MembershipStatus;
  correction_count: number;
  cancelled_at: string | null;
  cancel_effective_date: string | null;
  cancel_reason: string;
  previous: number | null;
  addons: MembershipAddOn[];
  net_paid_paise: number;
  created_at: string;
}

export type PaymentKind = "enrollment" | "renewal" | "refund" | "adjustment";
export type PaymentMethod = "cash" | "card" | "upi" | "bank" | "other";

export interface Payment {
  id: number;
  member: number;
  member_name: string;
  membership: number | null;
  kind: PaymentKind;
  method: PaymentMethod;
  amount_paise: number;
  discount_paise: number;
  invoice_number: string;
  refund_of: number | null;
  reason: string;
  edited: boolean;
  edited_at: string | null;
  original_amount_paise: number | null;
  created_by: number | null;
  created_by_name: string | null;
  created_at: string;
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
