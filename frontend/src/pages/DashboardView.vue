<script setup lang="ts">
import { useAuthStore } from "@/stores/auth";

const auth = useAuthStore();
</script>

<template>
  <div class="space-y-4">
    <h1 class="text-xl font-semibold text-slate-800">Today</h1>
    <div class="rounded-xl border border-slate-200 bg-white p-6">
      <p class="text-slate-600">
        Welcome, <span class="font-medium">{{ auth.user?.full_name || auth.user?.email }}</span>.
      </p>
      <p class="text-sm text-slate-500 mt-2">
        Foundation is up. The Today dashboard, members, revenue loop, and reports
        land in the next phases.
      </p>
    </div>
  </div>
</template>
