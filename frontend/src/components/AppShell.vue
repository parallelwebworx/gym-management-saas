<script setup lang="ts">
import {
  BarChart3,
  Bell,
  CreditCard,
  Dumbbell,
  Home,
  LogOut,
  Plus,
  ScrollText,
  Settings as SettingsIcon,
  Tag,
  Users,
} from "@lucide/vue";
import { computed, onMounted, type Component } from "vue";
import { useRoute, useRouter } from "vue-router";

import CommandPalette from "@/components/CommandPalette.vue";
import Button from "@/components/ui/Button.vue";
import { useAuthStore } from "@/stores/auth";

const auth = useAuthStore();
const router = useRouter();
const route = useRoute();

onMounted(() => {
  if (!auth.user) auth.fetchMe().catch(() => logout());
});

interface NavItem { label: string; to: string; icon: Component; roles: string[] }

const nav = computed<NavItem[]>(() => {
  const role = auth.role;
  const all: NavItem[] = [
    { label: "Today", to: "/", icon: Home, roles: ["owner", "branch_manager", "receptionist"] },
    { label: "Members", to: "/members", icon: Users, roles: ["owner", "branch_manager", "receptionist"] },
    { label: "Catalogue", to: "/catalogue", icon: Tag, roles: ["owner", "branch_manager"] },
    { label: "Payments", to: "/payments", icon: CreditCard, roles: ["owner", "branch_manager"] },
    { label: "Reports", to: "/reports", icon: BarChart3, roles: ["owner", "branch_manager"] },
    { label: "Audit Log", to: "/audit", icon: ScrollText, roles: ["owner", "branch_manager"] },
    { label: "Settings", to: "/settings", icon: SettingsIcon, roles: ["owner"] },
  ];
  return all.filter((i) => (role ? i.roles.includes(role) : false));
});

const PAGE: Record<string, { title: string; subtitle: string }> = {
  dashboard: { title: "Today", subtitle: "Your gym at a glance" },
  members: { title: "Members", subtitle: "Manage your member base" },
  "member-detail": { title: "Member", subtitle: "Profile, membership & payments" },
  catalogue: { title: "Catalogue", subtitle: "Plans and add-ons" },
  payments: { title: "Payments", subtitle: "Revenue ledger" },
  reports: { title: "Reports", subtitle: "Analytics & insights" },
  audit: { title: "Audit Log", subtitle: "Every change, tracked" },
  settings: { title: "Settings", subtitle: "Gym configuration" },
};
const page = computed(() => PAGE[(route.name as string) ?? ""] ?? { title: "GymPro", subtitle: "" });

function logout() {
  auth.logout();
  router.push({ name: "login" });
}
</script>

<template>
  <div class="flex min-h-screen">
    <!-- Sidebar -->
    <aside class="flex w-64 shrink-0 flex-col bg-sidebar text-sidebar-foreground">
      <div class="flex items-center gap-3 px-5 py-5">
        <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-white/15">
          <Dumbbell class="h-5 w-5" />
        </div>
        <div class="leading-tight">
          <div class="font-bold">GymPro</div>
          <div class="text-xs text-sidebar-muted">Management System</div>
        </div>
      </div>

      <div class="px-5 pb-2 pt-3 text-[11px] font-semibold uppercase tracking-wider text-sidebar-muted">
        Main menu
      </div>
      <nav class="flex-1 space-y-1 px-3">
        <RouterLink
          v-for="item in nav"
          :key="item.to"
          :to="item.to"
          class="flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-sidebar-foreground/80 transition-colors hover:bg-white/10 hover:text-sidebar-foreground"
          active-class="!bg-white/15 !text-sidebar-foreground shadow-sm"
          :class="{ '!bg-white/15 !text-sidebar-foreground': route.path === item.to }"
        >
          <component :is="item.icon" class="h-[18px] w-[18px]" />
          {{ item.label }}
        </RouterLink>
      </nav>

      <div class="p-3">
        <div class="rounded-xl bg-white/10 px-4 py-3">
          <div class="text-sm font-semibold">{{ auth.user?.gym?.name ?? "…" }}</div>
          <div class="text-xs text-sidebar-muted">{{ auth.user?.branch?.name ?? "" }}</div>
        </div>
      </div>
    </aside>

    <!-- Main -->
    <div class="flex min-w-0 flex-1 flex-col">
      <header class="sticky top-0 z-10 flex h-16 items-center justify-between border-b border-border bg-card/80 px-6 backdrop-blur">
        <div>
          <h1 class="text-lg font-bold tracking-tight">{{ page.title }}</h1>
          <p class="text-xs text-muted-foreground">{{ page.subtitle }}</p>
        </div>
        <div class="flex items-center gap-3">
          <span
            v-if="auth.user?.gym"
            class="hidden rounded-full px-2.5 py-0.5 text-xs font-medium sm:inline"
            :class="auth.user.gym.subscription_tier === 'pro' ? 'bg-accent/15 text-accent' : 'bg-muted text-muted-foreground'"
          >
            {{ auth.user.gym.subscription_tier.toUpperCase() }}
          </span>
          <button class="relative rounded-lg border border-border p-2 text-muted-foreground transition-colors hover:bg-muted" title="Notifications">
            <Bell class="h-[18px] w-[18px]" />
          </button>
          <Button variant="gradient" size="sm" class="h-9" @click="router.push('/members')">
            <Plus class="h-4 w-4" /> Quick Add
          </Button>
          <div class="flex items-center gap-2 pl-1">
            <span class="hidden text-sm text-muted-foreground md:inline">{{ auth.user?.email }}</span>
            <button class="rounded-lg p-2 text-muted-foreground transition-colors hover:bg-muted hover:text-destructive" title="Sign out" @click="logout">
              <LogOut class="h-[18px] w-[18px]" />
            </button>
          </div>
        </div>
      </header>

      <main class="flex-1 p-6">
        <RouterView v-slot="{ Component: View }">
          <component :is="View" :key="route.fullPath" class="animate-fade-in-up" />
        </RouterView>
      </main>
    </div>

    <CommandPalette />
  </div>
</template>
