<script setup lang="ts">
import TodayList from "@/components/TodayList.vue";
import { type TodayRow, useLogReminder, useToday } from "@/composables/useToday";
import { formatPaise } from "@/lib/money";

const { data, isLoading, refetch } = useToday();
const logReminder = useLogReminder();

async function remind(row: TodayRow, channel: "whatsapp" | "call") {
  await logReminder.mutateAsync({ member: row.member_id, membership: row.membership_id, channel });
}
function fmtDelta(p: number) {
  const s = p >= 0 ? "+" : "−";
  return `${s}${formatPaise(Math.abs(p))}`;
}
</script>

<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <h1 class="text-xl font-semibold text-slate-800">Today</h1>
      <button class="rounded border border-slate-300 px-3 py-1.5 text-sm hover:bg-slate-50" @click="refetch()">Refresh</button>
    </div>

    <div v-if="isLoading" class="text-slate-400">Loading…</div>

    <template v-else-if="data">
      <div class="grid grid-cols-2 gap-4 md:grid-cols-4">
        <div class="rounded-xl border border-slate-200 bg-white p-4">
          <div class="text-sm text-slate-500">Revenue today</div>
          <div class="mt-1 text-2xl font-semibold">{{ formatPaise(data.metrics.revenue_today_paise) }}</div>
          <div class="text-xs" :class="data.metrics.revenue_delta_paise >= 0 ? 'text-emerald-600' : 'text-red-600'">
            {{ fmtDelta(data.metrics.revenue_delta_paise) }} vs yesterday
          </div>
        </div>
        <div class="rounded-xl border border-slate-200 bg-white p-4">
          <div class="text-sm text-slate-500">New enrollments</div>
          <div class="mt-1 text-2xl font-semibold">{{ data.metrics.new_enrollments_today }}</div>
          <div class="text-xs text-slate-400">today</div>
        </div>
        <div class="rounded-xl border border-slate-200 bg-white p-4">
          <div class="text-sm text-slate-500">Expiring (14d)</div>
          <div class="mt-1 text-2xl font-semibold">{{ data.metrics.expiring_14d }}</div>
          <div class="text-xs text-slate-400">{{ data.metrics.expiring_7d }} in 7d · {{ data.metrics.expiring_3d }} in 3d</div>
        </div>
        <div class="rounded-xl border border-slate-200 bg-white p-4">
          <div class="text-sm text-slate-500">Frozen now</div>
          <div class="mt-1 text-2xl font-semibold">{{ data.metrics.frozen_now }}</div>
          <div class="text-xs text-slate-400">memberships</div>
        </div>
      </div>

      <section>
        <h2 class="mb-2 font-medium text-slate-700">Expiring soon</h2>
        <TodayList :rows="data.expiring_soon" empty="Nobody expiring in the next 14 days." show-days @remind="remind" />
      </section>

      <section>
        <h2 class="mb-2 font-medium text-slate-700">Recently expired</h2>
        <TodayList :rows="data.recently_expired" empty="No recent expiries." @remind="remind" />
      </section>

      <section>
        <h2 class="mb-2 font-medium text-slate-700">Enrolled today</h2>
        <TodayList :rows="data.enrolled_today" empty="No enrollments yet today." hide-actions @remind="remind" />
      </section>
    </template>
  </div>
</template>
