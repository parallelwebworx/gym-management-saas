<script setup lang="ts">
import { ref } from "vue";
import { useRoute, useRouter } from "vue-router";

import { useAuthStore } from "@/stores/auth";

const auth = useAuthStore();
const router = useRouter();
const route = useRoute();

const email = ref("");
const password = ref("");
const error = ref("");

async function submit() {
  error.value = "";
  try {
    await auth.login(email.value, password.value);
    const next = (route.query.next as string) || "/";
    router.push(next);
  } catch (e) {
    error.value = e instanceof Error ? e.message : "Login failed";
  }
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center px-4">
    <form
      class="w-full max-w-sm bg-white rounded-xl shadow-sm border border-slate-200 p-6 space-y-4"
      @submit.prevent="submit"
    >
      <h1 class="text-lg font-semibold text-slate-800">Sign in</h1>

      <div class="space-y-1">
        <label class="text-sm text-slate-600" for="email">Email</label>
        <input
          id="email"
          v-model="email"
          type="email"
          autocomplete="username"
          required
          class="w-full rounded border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-400"
        />
      </div>

      <div class="space-y-1">
        <label class="text-sm text-slate-600" for="password">Password</label>
        <input
          id="password"
          v-model="password"
          type="password"
          autocomplete="current-password"
          required
          class="w-full rounded border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-400"
        />
      </div>

      <p v-if="error" class="text-sm text-red-600">{{ error }}</p>

      <button
        type="submit"
        :disabled="auth.loading"
        class="w-full rounded bg-slate-900 px-3 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-60"
      >
        {{ auth.loading ? "Signing in…" : "Sign in" }}
      </button>
    </form>
  </div>
</template>
