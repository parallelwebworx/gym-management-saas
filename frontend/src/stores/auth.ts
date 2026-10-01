import { defineStore } from "pinia";
import { computed, ref } from "vue";

import { api, tokenStore, unwrap } from "@/lib/api";

export type Role = "super_admin" | "owner" | "branch_manager" | "receptionist";

export interface Branch {
  id: number;
  name: string;
  is_active: boolean;
}

export interface Gym {
  id: number;
  name: string;
  gstin: string;
  invoice_prefix: string;
  subscription_tier: "basic" | "pro";
  notifications_enabled: boolean;
}

export interface CurrentUser {
  id: number;
  email: string;
  full_name: string;
  role: Role;
  gym: Gym | null;
  branch: Branch | null;
}

export const useAuthStore = defineStore("auth", () => {
  const user = ref<CurrentUser | null>(null);
  const loading = ref(false);

  const isAuthenticated = computed(() => !!tokenStore.access);
  const role = computed<Role | null>(() => user.value?.role ?? null);

  async function login(email: string, password: string) {
    loading.value = true;
    try {
      const data = await unwrap<{
        access: string;
        refresh: string;
        user: CurrentUser;
      }>(api.post("/auth/login/", { email, password }));
      tokenStore.set(data.access, data.refresh);
      user.value = data.user;
    } finally {
      loading.value = false;
    }
  }

  async function fetchMe() {
    if (!tokenStore.access) return;
    user.value = await unwrap<CurrentUser>(api.get("/auth/me/"));
  }

  function logout() {
    tokenStore.clear();
    user.value = null;
  }

  return { user, loading, isAuthenticated, role, login, fetchMe, logout };
});
