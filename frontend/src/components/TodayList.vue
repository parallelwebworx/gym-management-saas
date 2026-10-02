<script setup lang="ts">
import { Phone } from "@lucide/vue";
import { useRouter } from "vue-router";

import Avatar from "@/components/ui/Avatar.vue";
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
  <div class="rounded-xl border border-border bg-card shadow-card overflow-hidden">
    <p v-if="rows.length === 0" class="px-4 py-8 text-center text-sm text-muted-foreground">{{ empty }}</p>
    <ul v-else class="divide-y divide-border">
      <li v-for="r in rows" :key="r.membership_id" class="flex items-center gap-3 px-4 py-3 transition-colors hover:bg-muted/40">
        <Avatar :name="r.member_name" size="sm" />
        <div class="min-w-0 flex-1 cursor-pointer" @click="router.push(`/members/${r.member_id}`)">
          <div class="truncate font-medium text-foreground">{{ r.member_name }}</div>
          <div class="truncate text-xs text-muted-foreground">{{ r.plan_name }} · {{ r.phone }}</div>
        </div>
        <div class="shrink-0 text-xs text-muted-foreground">
          {{ showDays ? `${r.days_left}d left` : r.end_date }}
        </div>
        <div v-if="!hideActions" class="flex shrink-0 items-center gap-1">
          <a :href="`tel:${r.phone}`" class="rounded-md p-1.5 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground" title="Call">
            <Phone class="h-4 w-4" />
          </a>
          <a :href="wa(r.phone)" target="_blank" class="rounded-md px-2 py-1 text-xs font-medium text-success transition-colors hover:bg-success/10" title="WhatsApp">WhatsApp</a>
          <button
            class="rounded-md px-2 py-1 text-xs font-medium transition-colors"
            :class="r.last_reminded_at ? 'text-success' : 'text-muted-foreground hover:bg-muted hover:text-foreground'"
            @click="emit('remind', r, 'whatsapp')"
          >
            {{ r.last_reminded_at ? "✓ reminded" : "Remind" }}
          </button>
        </div>
        <span v-else-if="r.last_reminded_at" class="shrink-0 text-xs text-success">contacted</span>
      </li>
    </ul>
  </div>
</template>
