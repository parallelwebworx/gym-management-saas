<script setup lang="ts">
import { computed, onMounted } from "vue";
import { useRouter } from "vue-router";

import CommandPalette from "@/components/CommandPalette.vue";
import { useAuthStore } from "@/stores/auth";

const auth = useAuthStore();
const router = useRouter();

onMounted(() => {
  if (!auth.user) auth.fetchMe().catch(() => logout());
});

// Role-aware nav. Items are filtered by the current user's role; Phase 0 wires
// the shell + Dashboard, later phases fill in the feature routes.
const nav = computed(() => {
  const role = auth.role;
  const all = [
    { label: "Today", to: "/", roles: ["owner", "branch_manager", "receptionist"] },
    { label: "Members", to: "/members", roles: ["owner", "branch_manager", "receptionist"] },
    { label: "Catalogue", to: "/catalogue", roles: ["owner", "branch_manager"] },
    { label: "Reports", to: "/reports", roles: ["owner", "branch_manager"] },
    { label: "Audit Log", to: "/audit", roles: ["owner", "branch_manager"] },
    { label: "Settings", to: "/settings", roles: ["owner"] },
  ];
  return all.filter((i) => (role ? i.roles.includes(role) : false));
});

function logout() {
  auth.logout();
  router.push({ name: "login" });
}
</script>

<template>
  <div class="min-h-screen flex">
    <aside class="w-60 shrink-0 border-r border-slate-200 bg-white flex flex-col">
      <div class="h-14 flex items-center px-4 font-semibold text-slate-800 border-b">
        Gym Manager
      </div>
      <nav class="flex-1 p-2 space-y-1">
        <RouterLink
          v-for="item in nav"
          :key="item.to"
          :to="item.to"
          class="block rounded px-3 py-2 text-sm text-slate-600 hover:bg-slate-100"
          active-class="bg-slate-100 text-slate-900 font-medium"
        >
          {{ item.label }}
        </RouterLink>
      </nav>
    </aside>

    <div class="flex-1 flex flex-col">
      <header class="h-14 flex items-center justify-between px-6 border-b border-slate-200 bg-white">
        <div class="flex items-center gap-3">
          <span class="font-medium text-slate-800">{{ auth.user?.gym?.name ?? "…" }}</span>
          <span
            v-if="auth.user?.branch"
            class="text-xs rounded bg-slate-100 px-2 py-0.5 text-slate-600"
          >
            {{ auth.user.branch.name }}
          </span>
          <span
            v-if="auth.user?.gym"
            class="text-xs rounded px-2 py-0.5"
            :class="auth.user.gym.subscription_tier === 'pro'
              ? 'bg-amber-100 text-amber-700'
              : 'bg-slate-100 text-slate-500'"
          >
            {{ auth.user.gym.subscription_tier.toUpperCase() }}
          </span>
        </div>
        <div class="flex items-center gap-3 text-sm">
          <span class="hidden items-center gap-1 rounded border border-slate-200 px-2 py-0.5 text-xs text-slate-400 sm:flex">
            Search <kbd class="font-sans">⌘K</kbd>
          </span>
          <span class="text-slate-500">{{ auth.user?.email }}</span>
          <button class="text-slate-600 hover:text-slate-900" @click="logout">Sign out</button>
        </div>
      </header>

      <main class="flex-1 p-6">
        <RouterView />
      </main>
    </div>

    <CommandPalette />
  </div>
</template>
