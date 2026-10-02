import { useMutation, useQuery, useQueryClient } from "@tanstack/vue-query";

import { api, unwrap } from "@/lib/api";
import type { Branch, Gym } from "@/stores/auth";

export interface Subscription {
  tier: "basic" | "pro";
  whatsapp_enabled: boolean;
  features: Record<string, boolean>;
}

export function useGymSettings() {
  return useQuery({
    queryKey: ["settings-gym"],
    queryFn: () => unwrap<Gym>(api.get("/settings/gym/")),
  });
}

export function useSaveGymSettings() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: Partial<Gym>) => unwrap<Gym>(api.patch("/settings/gym/", payload)),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["settings-gym"] }),
  });
}

export function useSubscription() {
  return useQuery({
    queryKey: ["subscription"],
    queryFn: () => unwrap<Subscription>(api.get("/settings/subscription/")),
  });
}

export function useBranchesAdmin() {
  return useQuery({
    queryKey: ["branches-admin"],
    queryFn: () => unwrap<{ results: Branch[] }>(api.get("/branches/")),
  });
}

export function useSaveBranch() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: Partial<Branch> & { id?: number }) => {
      const { id, ...body } = payload;
      return id
        ? unwrap<Branch>(api.patch(`/branches/${id}/`, body))
        : unwrap<Branch>(api.post("/branches/", body));
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["branches-admin"] }),
  });
}

export function useChangePassword() {
  return useMutation({
    mutationFn: (payload: { current_password: string; new_password: string }) =>
      unwrap(api.post("/settings/password/", payload)),
  });
}

export async function downloadDataExport() {
  const resp = await api.get("/settings/export/", { responseType: "blob" });
  const url = URL.createObjectURL(resp.data as Blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "gym_export.xlsx";
  a.click();
  URL.revokeObjectURL(url);
}
