import { useMutation, useQuery, useQueryClient } from "@tanstack/vue-query";

import { api, unwrap } from "@/lib/api";

export interface TodayRow {
  membership_id: number;
  member_id: number;
  member_name: string;
  phone: string;
  plan_name: string;
  end_date: string;
  days_left: number;
  last_reminded_at: string | null;
}

export interface TodayData {
  date: string;
  metrics: {
    revenue_today_paise: number;
    revenue_delta_paise: number;
    new_enrollments_today: number;
    expiring_14d: number;
    expiring_7d: number;
    expiring_3d: number;
    frozen_now: number;
  };
  expiring_soon: TodayRow[];
  recently_expired: TodayRow[];
  enrolled_today: TodayRow[];
}

export function useToday() {
  return useQuery({
    queryKey: ["today"],
    queryFn: () => unwrap<TodayData>(api.get("/today/")),
  });
}

export function useLogReminder() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (args: { member: number; membership?: number; channel: string; note?: string }) =>
      unwrap(api.post("/reminders/", args)),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["today"] }),
  });
}
