<script setup lang="ts">
import {
  CalendarClock,
  CreditCard,
  IndianRupee,
  Snowflake,
  Tag,
  TrendingUp,
  UserPlus,
  Users,
} from "@lucide/vue";
import { useRouter } from "vue-router";

import StatCard from "@/components/StatCard.vue";
import TodayList from "@/components/TodayList.vue";
import Button from "@/components/ui/Button.vue";
import Card from "@/components/ui/Card.vue";
import { type TodayRow, useLogReminder, useToday } from "@/composables/useToday";
import { formatPaise } from "@/lib/money";

const router = useRouter();
const { data, isLoading, refetch } = useToday();
const logReminder = useLogReminder();

async function remind(row: TodayRow, channel: "whatsapp" | "call") {
  await logReminder.mutateAsync({ member: row.member_id, membership: row.membership_id, channel });
}
function fmtDelta(p: number) {
  return `${p >= 0 ? "+" : "−"}${formatPaise(Math.abs(p))} vs yesterday`;
}

const quickActions = [
  { label: "Add member", icon: Users, to: "/members" },
  { label: "Catalogue", icon: Tag, to: "/catalogue" },
  { label: "Record payment", icon: CreditCard, to: "/payments" },
  { label: "View reports", icon: TrendingUp, to: "/reports" },
];
</script>

<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <h2 class="text-base font-semibold text-muted-foreground">Overview</h2>
      <Button variant="outline" size="sm" @click="refetch()">Refresh</Button>
    </div>

    <div v-if="isLoading" class="text-muted-foreground">Loading…</div>

    <template v-else-if="data">
      <!-- KPIs -->
      <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Revenue today" :value="formatPaise(data.metrics.revenue_today_paise)"
          :delta="fmtDelta(data.metrics.revenue_delta_paise)" :delta-positive="data.metrics.revenue_delta_paise >= 0"
          :icon="IndianRupee" tone="green" />
        <StatCard label="New enrollments" :value="data.metrics.new_enrollments_today" sub="today"
          :icon="UserPlus" tone="blue" />
        <StatCard label="Expiring (14d)" :value="data.metrics.expiring_14d"
          :sub="`${data.metrics.expiring_7d} in 7d · ${data.metrics.expiring_3d} in 3d`"
          :icon="CalendarClock" tone="amber" />
        <StatCard label="Frozen now" :value="data.metrics.frozen_now" sub="memberships"
          :icon="Snowflake" tone="sky" />
      </div>

      <!-- Quick actions -->
      <Card class="p-5">
        <h3 class="mb-3 font-semibold">Quick actions</h3>
        <div class="grid grid-cols-2 gap-3 md:grid-cols-4">
          <button
            v-for="a in quickActions" :key="a.to"
            class="flex flex-col items-center gap-2 rounded-lg border border-border bg-card px-4 py-4 text-sm font-medium transition-all hover:-translate-y-0.5 hover:border-primary/40 hover:shadow-card-hover"
            @click="router.push(a.to)"
          >
            <component :is="a.icon" class="h-5 w-5 text-primary" />
            {{ a.label }}
          </button>
        </div>
      </Card>

      <div class="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <section>
          <h3 class="mb-2 font-semibold">Expiring soon</h3>
          <TodayList :rows="data.expiring_soon" empty="Nobody expiring in the next 14 days." show-days @remind="remind" />
        </section>
        <section>
          <h3 class="mb-2 font-semibold">Recently expired</h3>
          <TodayList :rows="data.recently_expired" empty="No recent expiries." @remind="remind" />
        </section>
      </div>

      <section>
        <h3 class="mb-2 font-semibold">Enrolled today</h3>
        <TodayList :rows="data.enrolled_today" empty="No enrollments yet today." hide-actions @remind="remind" />
      </section>
    </template>
  </div>
</template>
