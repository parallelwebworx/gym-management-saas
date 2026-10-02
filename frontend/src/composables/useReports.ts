import { useQuery } from "@tanstack/vue-query";
import { computed, type MaybeRefOrGetter, toValue } from "vue";

import { api, unwrap } from "@/lib/api";

export interface Period {
  from?: string;
  to?: string;
}

export interface Overview {
  from: string;
  to: string;
  gross_paise: number;
  refunds_paise: number;
  net_paise: number;
  discount_paise: number;
  discount_rate_pct: number;
  transactions: number;
  enrollments: number;
  renewals: number;
  prev_net_paise: number;
  revenue_change_pct: number | null;
}

export interface Anomaly {
  severity: "warning" | "info";
  code: string;
  title: string;
  detail: string;
}

export interface TrendPoint {
  date: string;
  revenue_paise: number;
  cumulative_paise: number;
}

export interface PlanSale {
  plan_name: string;
  count: number;
  revenue_paise: number;
}

export interface StaffDiscount {
  staff_id: number | null;
  staff_name: string;
  sales: number;
  total_discount_paise: number;
  gross_paise: number;
  avg_discount_paise: number;
}

export function useOverviewReport(period: MaybeRefOrGetter<Period>) {
  return useQuery({
    queryKey: computed(() => ["report-overview", toValue(period)]),
    queryFn: () =>
      unwrap<{ overview: Overview; anomalies: Anomaly[]; trend: TrendPoint[] }>(
        api.get("/reports/overview/", { params: toValue(period) }),
      ),
  });
}

export function useRevenueReport(period: MaybeRefOrGetter<Period>) {
  return useQuery({
    queryKey: computed(() => ["report-revenue", toValue(period)]),
    queryFn: () =>
      unwrap<{ series: TrendPoint[] }>(api.get("/reports/revenue/", { params: toValue(period) })),
  });
}

export function usePlansReport(period: MaybeRefOrGetter<Period>) {
  return useQuery({
    queryKey: computed(() => ["report-plans", toValue(period)]),
    queryFn: () =>
      unwrap<{ plans: PlanSale[] }>(api.get("/reports/plans/", { params: toValue(period) })),
  });
}

export function useDiscountsReport(period: MaybeRefOrGetter<Period>) {
  return useQuery({
    queryKey: computed(() => ["report-discounts", toValue(period)]),
    queryFn: () =>
      unwrap<{ staff: StaffDiscount[] }>(api.get("/reports/discounts/", { params: toValue(period) })),
  });
}

export async function downloadReport(path: string, period: Period) {
  const resp = await api.get(path, { params: { ...period, export: "xlsx" }, responseType: "blob" });
  const url = URL.createObjectURL(resp.data as Blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = path.split("/").filter(Boolean).pop() + ".xlsx";
  a.click();
  URL.revokeObjectURL(url);
}
