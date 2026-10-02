<script setup lang="ts">
import { ref } from "vue";

import BaseModal from "@/components/BaseModal.vue";
import { useCancelMembership } from "@/composables/useMemberships";
import type { Membership } from "@/lib/types";

const props = defineProps<{ membership: Membership }>();
const emit = defineEmits<{ close: []; done: [] }>();

const effectiveDate = ref(new Date().toISOString().slice(0, 10));
const prorated = ref(false);
const reason = ref("");
const error = ref("");
const cancel = useCancelMembership();

async function submit() {
  error.value = "";
  try {
    await cancel.mutateAsync({
      id: props.membership.id,
      effective_date: effectiveDate.value,
      prorated_refund: prorated.value,
      reason: reason.value,
    });
    emit("done");
  } catch (e: any) {
    error.value = e?.response?.data?.error ?? "Cancel failed";
  }
}
const input = "w-full rounded border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-400";
</script>

<template>
  <BaseModal title="Cancel membership" @close="emit('close')">
    <form class="space-y-3" @submit.prevent="submit">
      <div>
        <label class="text-sm text-slate-600">Effective date</label>
        <input v-model="effectiveDate" type="date" :class="input" />
      </div>
      <label class="flex items-center gap-2 text-sm text-slate-600">
        <input type="checkbox" v-model="prorated" /> Issue prorated refund for the unused period
      </label>
      <div>
        <label class="text-sm text-slate-600">Reason</label>
        <input v-model="reason" :class="input" />
      </div>
      <p v-if="error" class="text-sm text-red-600">{{ error }}</p>
      <div class="flex justify-end gap-2 pt-1">
        <button type="button" class="rounded px-3 py-2 text-sm text-slate-600 hover:bg-slate-100" @click="emit('close')">Keep</button>
        <button type="submit" :disabled="cancel.isPending.value" class="rounded bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 disabled:opacity-60">
          {{ cancel.isPending.value ? "Cancelling…" : "Cancel membership" }}
        </button>
      </div>
    </form>
  </BaseModal>
</template>
