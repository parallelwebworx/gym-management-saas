import { useMutation, useQuery, useQueryClient } from "@tanstack/vue-query";
import { computed, type MaybeRefOrGetter, toValue } from "vue";

import { api, unwrap } from "@/lib/api";
import type { ImportResult, Member, Paginated } from "@/lib/types";

export interface MemberListParams {
  search?: string;
  gender?: string;
  sort?: string;
  page?: number;
  page_size?: number;
}

export function useMembers(params: MaybeRefOrGetter<MemberListParams>) {
  return useQuery({
    queryKey: computed(() => ["members", toValue(params)]),
    queryFn: () =>
      unwrap<Paginated<Member>>(
        api.get("/members/", { params: toValue(params) }),
      ),
  });
}

export function useMember(id: MaybeRefOrGetter<number | null>) {
  return useQuery({
    queryKey: computed(() => ["member", toValue(id)]),
    enabled: () => toValue(id) != null,
    queryFn: () => unwrap<Member>(api.get(`/members/${toValue(id)}/`)),
  });
}

export function useCheckPhone() {
  return useMutation({
    mutationFn: (args: { phone: string; exclude?: number }) =>
      unwrap<{ phone: string; exists: boolean; member: { id: number; full_name: string } | null }>(
        api.get("/members/check-phone/", { params: args }),
      ),
  });
}

export function useSaveMember() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: Partial<Member> & { id?: number }) => {
      const { id, ...body } = payload;
      return id
        ? unwrap<Member>(api.patch(`/members/${id}/`, body))
        : unwrap<Member>(api.post("/members/", body));
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["members"] }),
  });
}

export function useDeleteMember() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => api.delete(`/members/${id}/`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["members"] }),
  });
}

export function useRestoreMember() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => unwrap<Member>(api.post(`/members/${id}/restore/`)),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["members"] }),
  });
}

export function useImportMembers() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (args: { file: File; commit: boolean }) => {
      const form = new FormData();
      form.append("file", args.file);
      return unwrap<ImportResult>(
        api.post("/members/import/", form, {
          params: { commit: args.commit },
          headers: { "Content-Type": "multipart/form-data" },
        }),
      );
    },
    onSuccess: (_d, vars) => {
      if (vars.commit) qc.invalidateQueries({ queryKey: ["members"] });
    },
  });
}

/** Trigger a browser download of the members .xlsx export. */
export async function downloadMembersExport(params: MemberListParams) {
  const resp = await api.get("/members/export/", { params, responseType: "blob" });
  const url = URL.createObjectURL(resp.data as Blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "members.xlsx";
  a.click();
  URL.revokeObjectURL(url);
}
