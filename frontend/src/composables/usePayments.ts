import { useMutation, useQuery, useQueryClient } from "@tanstack/vue-query";
import { computed, type MaybeRefOrGetter, toValue } from "vue";

import { api, unwrap } from "@/lib/api";
import type { Paginated, Payment } from "@/lib/types";

export interface PaymentParams {
  member?: number;
  membership?: number;
  kind?: string;
  from?: string;
  to?: string;
  page?: number;
}

export function usePayments(params: MaybeRefOrGetter<PaymentParams>) {
  return useQuery({
    queryKey: computed(() => ["payments", toValue(params)]),
    queryFn: () =>
      unwrap<Paginated<Payment>>(api.get("/payments/", { params: toValue(params) })),
  });
}

function invalidate(qc: ReturnType<typeof useQueryClient>) {
  qc.invalidateQueries({ queryKey: ["payments"] });
  qc.invalidateQueries({ queryKey: ["memberships"] });
}

export function useRefundPayment() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (args: { id: number; amount_paise: number; reason?: string }) =>
      unwrap<{ refund: Payment }>(
        api.post(`/payments/${args.id}/refund/`, {
          amount_paise: args.amount_paise,
          reason: args.reason,
        }),
      ),
    onSuccess: () => invalidate(qc),
  });
}

export function useEditPayment() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (args: { id: number; amount_paise: number; reason: string }) =>
      unwrap<Payment>(
        api.post(`/payments/${args.id}/edit/`, {
          amount_paise: args.amount_paise,
          reason: args.reason,
        }),
      ),
    onSuccess: () => invalidate(qc),
  });
}
