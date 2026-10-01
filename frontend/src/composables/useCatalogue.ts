import { useMutation, useQuery, useQueryClient } from "@tanstack/vue-query";

import { api, unwrap } from "@/lib/api";
import type { AddOn, Paginated, Plan } from "@/lib/types";

export function usePlans() {
  return useQuery({
    queryKey: ["plans"],
    queryFn: () => unwrap<Paginated<Plan>>(api.get("/plans/", { params: { page_size: 200 } })),
  });
}

export function useSavePlan() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: Partial<Plan> & { id?: number }) => {
      const { id, ...body } = payload;
      return id
        ? unwrap<Plan>(api.patch(`/plans/${id}/`, body))
        : unwrap<Plan>(api.post("/plans/", body));
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["plans"] }),
  });
}

export function useDeletePlan() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => api.delete(`/plans/${id}/`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["plans"] }),
  });
}

export function useAddOns() {
  return useQuery({
    queryKey: ["addons"],
    queryFn: () => unwrap<Paginated<AddOn>>(api.get("/add-ons/", { params: { page_size: 200 } })),
  });
}

export function useSaveAddOn() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: Partial<AddOn> & { id?: number }) => {
      const { id, ...body } = payload;
      return id
        ? unwrap<AddOn>(api.patch(`/add-ons/${id}/`, body))
        : unwrap<AddOn>(api.post("/add-ons/", body));
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["addons"] }),
  });
}

export function useDeleteAddOn() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => api.delete(`/add-ons/${id}/`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["addons"] }),
  });
}
