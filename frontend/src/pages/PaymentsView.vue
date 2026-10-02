<script setup lang="ts">
import { computed, reactive } from "vue";
import { useRouter } from "vue-router";

import { usePayments } from "@/composables/usePayments";
import { formatPaise } from "@/lib/money";

const router = useRouter();
const filters = reactive({ kind: "", from: "", to: "", page: 1 });
const { data } = usePayments(() => ({ ...filters }));

// Net revenue across the current page's rows (signed sum).
const pageNet = computed(() =>
  (data.value?.results ?? []).reduce((s, p) => s + p.amount_paise, 0),
);
const totalPages = computed(() => data.value?.num_pages ?? 1);
const kindClass: Record<string, string> = { refund: "text-red-600" };
</script>

<template>
  <div class="space-y-4">
    <h1 class="text-xl font-semibold text-slate-800">Payments</h1>

    <div class="flex flex-wrap items-center gap-2">
      <select v-model="filters.kind" class="rounded border border-slate-300 px-2 py-2 text-sm" @change="filters.page = 1">
        <option value="">All kinds</option>
        <option value="enrollment">Enrollment</option>
        <option value="renewal">Renewal</option>
        <option value="refund">Refund</option>
        <option value="adjustment">Adjustment</option>
      </select>
      <label class="text-sm text-slate-500">From <input v-model="filters.from" type="date" class="rounded border border-slate-300 px-2 py-1 text-sm" @change="filters.page = 1" /></label>
      <label class="text-sm text-slate-500">To <input v-model="filters.to" type="date" class="rounded border border-slate-300 px-2 py-1 text-sm" @change="filters.page = 1" /></label>
      <span class="ml-auto text-sm text-slate-600">Page net: <b>{{ formatPaise(pageNet) }}</b></span>
    </div>

    <div class="rounded-xl border border-slate-200 bg-white overflow-hidden">
      <table class="w-full text-sm">
        <thead class="bg-slate-50 text-left text-slate-500">
          <tr>
            <th class="px-4 py-2">Invoice</th><th class="px-4 py-2">Member</th>
            <th class="px-4 py-2">Kind</th><th class="px-4 py-2">Amount</th>
            <th class="px-4 py-2">Discount</th><th class="px-4 py-2">By</th>
            <th class="px-4 py-2">Date</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="data && data.results.length === 0"><td colspan="7" class="px-4 py-8 text-center text-slate-400">No payments.</td></tr>
          <tr
            v-for="p in data?.results"
            :key="p.id"
            class="border-t hover:bg-slate-50 cursor-pointer"
            @click="router.push(`/members/${p.member}`)"
          >
            <td class="px-4 py-2">{{ p.invoice_number }}</td>
            <td class="px-4 py-2">{{ p.member_name }}</td>
            <td class="px-4 py-2 capitalize">{{ p.kind }}</td>
            <td class="px-4 py-2" :class="kindClass[p.kind]">{{ formatPaise(p.amount_paise) }}</td>
            <td class="px-4 py-2">{{ p.discount_paise ? formatPaise(p.discount_paise) : "—" }}</td>
            <td class="px-4 py-2 text-slate-500">{{ p.created_by_name || "—" }}</td>
            <td class="px-4 py-2 text-slate-500">{{ new Date(p.created_at).toLocaleDateString() }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="data" class="flex items-center justify-between text-sm text-slate-600">
      <span>{{ data.count }} payment(s)</span>
      <div class="flex items-center gap-2">
        <button class="rounded border px-2 py-1 disabled:opacity-40" :disabled="filters.page <= 1" @click="filters.page--">Prev</button>
        <span>Page {{ filters.page }} / {{ totalPages }}</span>
        <button class="rounded border px-2 py-1 disabled:opacity-40" :disabled="filters.page >= totalPages" @click="filters.page++">Next</button>
      </div>
    </div>
  </div>
</template>
