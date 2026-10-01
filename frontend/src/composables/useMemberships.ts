import { useMutation, useQuery, useQueryClient } from "@tanstack/vue-query";
import { computed, type MaybeRefOrGetter, toValue } from "vue";

import { api, unwrap } from "@/lib/api";
import type { Membership, Paginated, Payment } from "@/lib/types";

export interface EnrollPayload {
  member_id?: number;
  member?: { full_name: string; phone: string };
  plan_id: number;
  addon_ids?: number[];
  discount_paise?: number;
  method?: string;
  amount_paid_paise?: number | null;
  start_date?: string | null;
  expected_total_paise?: number;
}

export interface RenewPayload {
  plan_id: number;
  addon_ids?: number[];
  discount_paise?: number;
  method?: string;
  amount_paid_paise?: number | null;
  start_mode?: "from_today" | "from_previous_end" | "custom";
  custom_start_date?: string | null;
  expected_total_paise?: number;
}

export function useMemberMemberships(memberId: MaybeRefOrGetter<number | null>) {
  return useQuery({
    queryKey: computed(() => ["memberships", toValue(memberId)]),
    enabled: () => toValue(memberId) != null,
    queryFn: () =>
      unwrap<Paginated<Membership>>(
        api.get("/memberships/", { params: { member: toValue(memberId) } }),
      ),
  });
}

function invalidate(qc: ReturnType<typeof useQueryClient>) {
  qc.invalidateQueries({ queryKey: ["memberships"] });
  qc.invalidateQueries({ queryKey: ["payments"] });
}

export function useEnroll() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: EnrollPayload) =>
      unwrap<{ membership: Membership; payment: Payment | null }>(
        api.post("/memberships/enroll/", payload),
      ),
    onSuccess: () => invalidate(qc),
  });
}

export function useRenew() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (args: { id: number; payload: RenewPayload }) =>
      unwrap<{ membership: Membership; payment: Payment | null }>(
        api.post(`/memberships/${args.id}/renew/`, args.payload),
      ),
    onSuccess: () => invalidate(qc),
  });
}

export function useCancelMembership() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (args: {
      id: number;
      effective_date: string;
      prorated_refund: boolean;
      reason?: string;
    }) => unwrap(api.post(`/memberships/${args.id}/cancel/`, args)),
    onSuccess: () => invalidate(qc),
  });
}

export function useCorrectMembership() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (args: {
      id: number;
      plan_id?: number;
      start_date?: string;
      addon_ids?: number[];
      reason: string;
    }) => unwrap(api.post(`/memberships/${args.id}/correct/`, args)),
    onSuccess: () => invalidate(qc),
  });
}

export async function fetchCanCorrect(id: number) {
  return unwrap<{ allowed: boolean; reason: string }>(
    api.get(`/memberships/${id}/can-correct/`),
  );
}
