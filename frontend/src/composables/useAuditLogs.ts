import { useQuery } from "@tanstack/vue-query";
import { computed, type MaybeRefOrGetter, toValue } from "vue";

import { api, unwrap } from "@/lib/api";
import type { Paginated } from "@/lib/types";

export interface AuditLog {
  id: number;
  action: string;
  entity_type: string;
  entity_id: string;
  before: Record<string, unknown> | null;
  after: Record<string, unknown> | null;
  summary: string;
  actor: number | null;
  actor_name: string | null;
  actor_email: string | null;
  branch: number | null;
  created_at: string;
}

export interface AuditParams {
  action?: string;
  entity_type?: string;
  from?: string;
  to?: string;
  page?: number;
}

export function useAuditLogs(params: MaybeRefOrGetter<AuditParams>) {
  return useQuery({
    queryKey: computed(() => ["audit-logs", toValue(params)]),
    queryFn: () =>
      unwrap<Paginated<AuditLog>>(api.get("/audit-logs/", { params: toValue(params) })),
  });
}

export async function downloadAuditExport(params: AuditParams) {
  const resp = await api.get("/audit-logs/export/", { params, responseType: "blob" });
  const url = URL.createObjectURL(resp.data as Blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "audit_log.xlsx";
  a.click();
  URL.revokeObjectURL(url);
}
