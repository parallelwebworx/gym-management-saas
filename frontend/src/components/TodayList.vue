<script setup lang="ts">
import { useRouter } from "vue-router";

import type { TodayRow } from "@/composables/useToday";

defineProps<{
  rows: TodayRow[];
  empty: string;
  showDays?: boolean;
  hideActions?: boolean;
}>();
const emit = defineEmits<{ remind: [row: TodayRow, channel: "whatsapp" | "call"] }>();
const router = useRouter();

function wa(phone: string) {
  return `https://wa.me/${phone.replace(/\D/g, "")}`;
}
</script>

<template>
  <div class="rounded-xl border border-slate-200 bg-white overflow-hidden">
    <p v-if="rows.length === 0" class="px-4 py-6 text-center text-sm text-slate-400">{{ empty }}</p>
    <table v-else class="w-full text-sm">
      <tbody>
        <tr v-for="r in rows" :key="r.membership_id" class="border-t first:border-t-0 hover:bg-slate-50">
          <td class="px-4 py-2 cursor-pointer" @click="router.push(`/members/${r.member_id}`)">
            <div class="font-medium text-slate-800">{{ r.member_name }}</div>
            <div class="text-xs text-slate-400">{{ r.plan_name }} · {{ r.phone }}</div>
          </td>
          <td class="px-4 py-2 text-slate-500">
            {{ showDays ? `${r.days_left} day(s) left` : r.end_date }}
          </td>
          <td class="px-4 py-2 text-right whitespace-nowrap">
            <template v-if="hideActions">
              <span v-if="r.last_reminded_at" class="text-xs text-emerald-600">contacted</span>
            </template>
            <template v-else>
              <a :href="`tel:${r.phone}`" class="text-slate-600 hover:text-slate-900 mr-3">Call</a>
              <a :href="wa(r.phone)" target="_blank" class="text-emerald-700 hover:text-emerald-800 mr-3">WhatsApp</a>
              <button class="text-xs text-slate-500 hover:text-slate-800" @click="emit('remind', r, 'whatsapp')">
                {{ r.last_reminded_at ? "✓ reminded" : "Log reminder" }}
              </button>
            </template>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
