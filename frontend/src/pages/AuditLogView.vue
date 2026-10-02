<script setup lang="ts">
import { computed, reactive, ref } from "vue";

import { type AuditLog, downloadAuditExport, useAuditLogs } from "@/composables/useAuditLogs";

const filters = reactive({ action: "", entity_type: "", from: "", to: "", page: 1 });
const { data } = useAuditLogs(() => ({ ...filters }));
const expanded = ref<number | null>(null);

const actions = [
  "enroll", "renew", "refund", "edit_payment", "correct", "cancel", "create", "update", "delete",
];
const totalPages = computed(() => data.value?.num_pages ?? 1);

function toggle(row: AuditLog) {
  expanded.value = expanded.value === row.id ? null : row.id;
}
function pretty(obj: unknown) {
  return obj ? JSON.stringify(obj, null, 2) : "—";
}
</script>

<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <h1 class="text-xl font-semibold text-slate-800">Audit log</h1>
      <button class="rounded border border-slate-300 px-3 py-1.5 text-sm hover:bg-slate-50" @click="downloadAuditExport({ ...filters })">Export Excel</button>
    </div>

    <div class="flex flex-wrap items-center gap-2 text-sm">
      <select v-model="filters.action" class="rounded border border-slate-300 px-2 py-2" @change="filters.page = 1">
        <option value="">All actions</option>
        <option v-for="a in actions" :key="a" :value="a">{{ a }}</option>
      </select>
      <input v-model="filters.entity_type" placeholder="Entity (e.g. Membership)" class="rounded border border-slate-300 px-2 py-2" @change="filters.page = 1" />
      <label>From <input v-model="filters.from" type="date" class="rounded border border-slate-300 px-2 py-1" @change="filters.page = 1" /></label>
      <label>To <input v-model="filters.to" type="date" class="rounded border border-slate-300 px-2 py-1" @change="filters.page = 1" /></label>
    </div>

    <div class="rounded-xl border border-slate-200 bg-white overflow-hidden">
      <table class="w-full text-sm">
        <thead class="bg-slate-50 text-left text-slate-500">
          <tr>
            <th class="px-4 py-2">When</th><th class="px-4 py-2">Action</th>
            <th class="px-4 py-2">Entity</th><th class="px-4 py-2">Actor</th>
            <th class="px-4 py-2">Summary</th><th class="px-4 py-2 w-16"></th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="data && data.results.length === 0"><td colspan="6" class="px-4 py-8 text-center text-slate-400">No audit entries.</td></tr>
          <template v-for="row in data?.results" :key="row.id">
            <tr class="border-t">
              <td class="px-4 py-2 text-slate-500">{{ new Date(row.created_at).toLocaleString() }}</td>
              <td class="px-4 py-2"><span class="rounded bg-slate-100 px-2 py-0.5 text-xs">{{ row.action }}</span></td>
              <td class="px-4 py-2">{{ row.entity_type }} #{{ row.entity_id }}</td>
              <td class="px-4 py-2 text-slate-500">{{ row.actor_name || row.actor_email || "—" }}</td>
              <td class="px-4 py-2">{{ row.summary }}</td>
              <td class="px-4 py-2 text-right">
                <button v-if="row.before || row.after" class="text-xs text-slate-500 hover:text-slate-800" @click="toggle(row)">
                  {{ expanded === row.id ? "Hide" : "Diff" }}
                </button>
              </td>
            </tr>
            <tr v-if="expanded === row.id" class="border-t bg-slate-50">
              <td colspan="6" class="px-4 py-3">
                <div class="grid grid-cols-2 gap-4">
                  <div>
                    <div class="mb-1 text-xs font-medium text-slate-500">Before</div>
                    <pre class="overflow-auto rounded bg-white p-2 text-xs border">{{ pretty(row.before) }}</pre>
                  </div>
                  <div>
                    <div class="mb-1 text-xs font-medium text-slate-500">After</div>
                    <pre class="overflow-auto rounded bg-white p-2 text-xs border">{{ pretty(row.after) }}</pre>
                  </div>
                </div>
              </td>
            </tr>
          </template>
        </tbody>
      </table>
    </div>

    <div v-if="data" class="flex items-center justify-between text-sm text-slate-600">
      <span>{{ data.count }} entries</span>
      <div class="flex items-center gap-2">
        <button class="rounded border px-2 py-1 disabled:opacity-40" :disabled="filters.page <= 1" @click="filters.page--">Prev</button>
        <span>Page {{ filters.page }} / {{ totalPages }}</span>
        <button class="rounded border px-2 py-1 disabled:opacity-40" :disabled="filters.page >= totalPages" @click="filters.page++">Next</button>
      </div>
    </div>
  </div>
</template>
