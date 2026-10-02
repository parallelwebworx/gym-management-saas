import { useMutation, useQuery, useQueryClient } from "@tanstack/vue-query";
import { computed, type MaybeRefOrGetter, toValue } from "vue";

import { api, unwrap } from "@/lib/api";
import type { Paginated } from "@/lib/types";

export interface Notification {
  id: number;
  member: number | null;
  member_name: string | null;
  membership: number | null;
  payment: number | null;
  event: string;
  channel: string;
  to_phone: string;
  body: string;
  status: "pending" | "sent" | "failed";
  attempts: number;
  error: string;
  sent_at: string | null;
  created_at: string;
}

export function useNotifications(params: MaybeRefOrGetter<{ member?: number; status?: string }>) {
  return useQuery({
    queryKey: computed(() => ["notifications", toValue(params)]),
    queryFn: () =>
      unwrap<Paginated<Notification>>(api.get("/notifications/", { params: toValue(params) })),
  });
}

export function useResendNotification() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => unwrap<Notification>(api.post(`/notifications/${id}/resend/`)),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["notifications"] }),
  });
}

export function useSendTestMessage() {
  return useMutation({
    mutationFn: (args: { phone: string; channel?: string }) =>
      unwrap<Notification>(api.post("/notifications/test/", args)),
  });
}
