<script setup lang="ts">
import { onMounted, ref } from "vue";

import BaseModal from "@/components/BaseModal.vue";
import { usePlans } from "@/composables/useCatalogue";
import { fetchCanCorrect, useCorrectMembership } from "@/composables/useMemberships";
import type { Membership } from "@/lib/types";

const props = defineProps<{ membership: Membership }>();
const emit = defineEmits<{ close: []; done: [] }>();

const { data: plans } = usePlans();
const planId = ref<number>(props.membership.plan);
const startDate = ref<string>(props.membership.start_date);
const reason = ref("");
const error = ref("");
const gate = ref<{ allowed: boolean; reason: string } | null>(null);
const correct = useCorrectMembership();

onMounted(async () => {
  try {
    gate.value = await fetchCanCorrect(props.membership.id);
  } catch {
    gate.value = { allowed: false, reason: "Could not check permission." };
  }
});

async function submit() {
  error.value = "";
  try {
    await correct.mutateAsync({
      id: props.membership.id,
      plan_id: planId.value,
      start_date: startDate.value,
      reason: reason.value,
    });
    emit("done");
  } catch (e: any) {
    error.value = e?.response?.data?.error ?? "Correction failed";
  }
}
const input = "w-full rounded border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-400";
</script>

<template>
  <BaseModal title="Correct membership" @close="emit('close')">
    <div v-if="gate && !gate.allowed" class="space-y-3">
      <p class="text-sm text-amber-700">{{ gate.reason }}</p>
      <div class="flex justify-end">
        <button class="rounded px-3 py-2 text-sm text-slate-600 hover:bg-slate-100" @click="emit('close')">Close</button>
      </div>
    </div>
    <form v-else class="space-y-3" @submit.prevent="submit">
      <p class="text-xs text-slate-400">Corrections are logged and the original end date is preserved.</p>
      <div>
        <label class="text-sm text-slate-600">Plan</label>
        <select v-model.number="planId" :class="input">
          <option v-for="p in plans?.results" :key="p.id" :value="p.id">
            {{ p.name }} ({{ p.duration_days }}d)
          </option>
        </select>
      </div>
      <div>
        <label class="text-sm text-slate-600">Start date</label>
        <input v-model="startDate" type="date" :class="input" />
      </div>
      <div>
        <label class="text-sm text-slate-600">Reason</label>
        <input v-model="reason" :class="input" />
      </div>
      <p v-if="error" class="text-sm text-red-600">{{ error }}</p>
      <div class="flex justify-end gap-2 pt-1">
        <button type="button" class="rounded px-3 py-2 text-sm text-slate-600 hover:bg-slate-100" @click="emit('close')">Cancel</button>
        <button type="submit" :disabled="correct.isPending.value" class="rounded bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-60">
          {{ correct.isPending.value ? "Saving…" : "Apply correction" }}
        </button>
      </div>
    </form>
  </BaseModal>
</template>
