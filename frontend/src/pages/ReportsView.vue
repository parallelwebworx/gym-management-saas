<script setup lang="ts">
import { reactive, ref } from "vue";

import RevenueChart from "@/components/RevenueChart.vue";
import {
  downloadReport,
  useDiscountsReport,
  useOverviewReport,
  usePlansReport,
  useRevenueReport,
} from "@/composables/useReports";
import { formatPaise } from "@/lib/money";

const period = reactive<{ from: string; to: string }>({
  from: new Date(Date.now() - 29 * 864e5).toISOString().slice(0, 10),
  to: new Date().toISOString().slice(0, 10),
});
const tab = ref<"overview" | "revenue" | "plans" | "discounts">("overview");

const overview = useOverviewReport(() => ({ ...period }));
const revenue = useRevenueReport(() => ({ ...period }));
const plans = usePlansReport(() => ({ ...period }));
const discounts = useDiscountsReport(() => ({ ...period }));

const tabs = [
  { key: "overview", label: "Overview" },
  { key: "revenue", label: "Revenue" },
  { key: "plans", label: "Plan sales" },
  { key: "discounts", label: "Discount leakage" },
] as const;

const sevClass: Record<string, string> = {
  warning: "border-amber-300 bg-amber-50",
  info: "border-sky-300 bg-sky-50",
};
</script>

<template>
  <div class="space-y-4">
    <div class="flex flex-wrap items-center justify-between gap-2">
      <h1 class="text-xl font-semibold text-foreground">Reports</h1>
      <div class="flex items-center gap-2 text-sm">
        <label>From <input v-model="period.from" type="date" class="rounded border border-input px-2 py-1" /></label>
        <label>To <input v-model="period.to" type="date" class="rounded border border-input px-2 py-1" /></label>
      </div>
    </div>

    <div class="flex gap-1 border-b border-border">
      <button
        v-for="t in tabs"
        :key="t.key"
        class="px-3 py-2 text-sm -mb-px border-b-2"
        :class="tab === t.key ? 'border-slate-800 text-foreground font-medium' : 'border-transparent text-muted-foreground hover:text-foreground'"
        @click="tab = t.key"
      >
        {{ t.label }}
      </button>
    </div>

    <!-- Overview -->
    <div v-if="tab === 'overview'" class="space-y-4">
      <div v-if="overview.data.value" class="grid grid-cols-2 gap-4 md:grid-cols-4">
        <div class="rounded-xl border border-border bg-card p-4">
          <div class="text-sm text-muted-foreground">Net revenue</div>
          <div class="mt-1 text-2xl font-semibold">{{ formatPaise(overview.data.value.overview.net_paise) }}</div>
          <div v-if="overview.data.value.overview.revenue_change_pct !== null" class="text-xs"
               :class="overview.data.value.overview.revenue_change_pct >= 0 ? 'text-emerald-600' : 'text-red-600'">
            {{ overview.data.value.overview.revenue_change_pct }}% vs previous
          </div>
        </div>
        <div class="rounded-xl border border-border bg-card p-4">
          <div class="text-sm text-muted-foreground">Discounts</div>
          <div class="mt-1 text-2xl font-semibold">{{ formatPaise(overview.data.value.overview.discount_paise) }}</div>
          <div class="text-xs text-muted-foreground">{{ overview.data.value.overview.discount_rate_pct }}% of list</div>
        </div>
        <div class="rounded-xl border border-border bg-card p-4">
          <div class="text-sm text-muted-foreground">Refunds</div>
          <div class="mt-1 text-2xl font-semibold">{{ formatPaise(overview.data.value.overview.refunds_paise) }}</div>
        </div>
        <div class="rounded-xl border border-border bg-card p-4">
          <div class="text-sm text-muted-foreground">Enrollments / Renewals</div>
          <div class="mt-1 text-2xl font-semibold">
            {{ overview.data.value.overview.enrollments }} / {{ overview.data.value.overview.renewals }}
          </div>
        </div>
      </div>

      <div v-if="overview.data.value?.anomalies.length" class="space-y-2">
        <div v-for="a in overview.data.value.anomalies" :key="a.code"
             class="rounded-lg border px-4 py-2 text-sm" :class="sevClass[a.severity]">
          <span class="font-medium">{{ a.title }}</span> — {{ a.detail }}
        </div>
      </div>
      <p v-else-if="overview.data.value" class="text-sm text-emerald-600">No anomalies detected this period.</p>

      <div v-if="overview.data.value" class="rounded-xl border border-border bg-card p-4">
        <RevenueChart :points="overview.data.value.trend" />
      </div>
    </div>

    <!-- Revenue -->
    <div v-else-if="tab === 'revenue'" class="space-y-3">
      <div class="flex justify-end">
        <button class="rounded border border-input px-3 py-1.5 text-sm hover:bg-muted/40" @click="downloadReport('/reports/revenue/', period)">Export Excel</button>
      </div>
      <div v-if="revenue.data.value" class="rounded-xl border border-border bg-card p-4">
        <RevenueChart :points="revenue.data.value.series" />
      </div>
    </div>

    <!-- Plans -->
    <div v-else-if="tab === 'plans'" class="space-y-3">
      <div class="flex justify-end">
        <button class="rounded border border-input px-3 py-1.5 text-sm hover:bg-muted/40" @click="downloadReport('/reports/plans/', period)">Export Excel</button>
      </div>
      <div class="rounded-xl border border-border bg-card overflow-hidden">
        <table class="w-full text-sm">
          <thead class="bg-muted/40 text-left text-muted-foreground"><tr><th class="px-4 py-2">Plan</th><th class="px-4 py-2">Sales</th><th class="px-4 py-2">Revenue</th></tr></thead>
          <tbody>
            <tr v-if="plans.data.value && plans.data.value.plans.length === 0"><td colspan="3" class="px-4 py-6 text-center text-muted-foreground">No sales in this period.</td></tr>
            <tr v-for="p in plans.data.value?.plans" :key="p.plan_name" class="border-t">
              <td class="px-4 py-2">{{ p.plan_name }}</td>
              <td class="px-4 py-2">{{ p.count }}</td>
              <td class="px-4 py-2">{{ formatPaise(p.revenue_paise) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Discounts -->
    <div v-else class="space-y-3">
      <div class="flex justify-end">
        <button class="rounded border border-input px-3 py-1.5 text-sm hover:bg-muted/40" @click="downloadReport('/reports/discounts/', period)">Export Excel</button>
      </div>
      <div class="rounded-xl border border-border bg-card overflow-hidden">
        <table class="w-full text-sm">
          <thead class="bg-muted/40 text-left text-muted-foreground">
            <tr><th class="px-4 py-2">Staff</th><th class="px-4 py-2">Sales</th><th class="px-4 py-2">Total discount</th><th class="px-4 py-2">Avg discount</th><th class="px-4 py-2">Gross</th></tr>
          </thead>
          <tbody>
            <tr v-if="discounts.data.value && discounts.data.value.staff.length === 0"><td colspan="5" class="px-4 py-6 text-center text-muted-foreground">No data.</td></tr>
            <tr v-for="s in discounts.data.value?.staff" :key="s.staff_id ?? s.staff_name" class="border-t">
              <td class="px-4 py-2">{{ s.staff_name }}</td>
              <td class="px-4 py-2">{{ s.sales }}</td>
              <td class="px-4 py-2">{{ formatPaise(s.total_discount_paise) }}</td>
              <td class="px-4 py-2">{{ formatPaise(s.avg_discount_paise) }}</td>
              <td class="px-4 py-2">{{ formatPaise(s.gross_paise) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
