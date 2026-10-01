import { createRouter, createWebHistory } from "vue-router";

import { tokenStore } from "@/lib/api";

const routes = [
  {
    path: "/login",
    name: "login",
    component: () => import("@/pages/LoginView.vue"),
    meta: { public: true },
  },
  {
    path: "/",
    component: () => import("@/components/AppShell.vue"),
    children: [
      {
        path: "",
        name: "dashboard",
        component: () => import("@/pages/DashboardView.vue"),
      },
    ],
  },
];

export const router = createRouter({
  history: createWebHistory(),
  routes,
});

// Global guard: anything not marked `public` requires a token.
router.beforeEach((to) => {
  const authed = !!tokenStore.access;
  if (!to.meta.public && !authed) {
    return { name: "login", query: { next: to.fullPath } };
  }
  if (to.name === "login" && authed) {
    return { name: "dashboard" };
  }
  return true;
});
