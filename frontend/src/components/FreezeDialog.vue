<script setup lang="ts">
import { ref } from "vue";

import BaseModal from "@/components/BaseModal.vue";
import { useFreezeMembership, useUnfreezeMembership } from "@/composables/useMemberships";
import type { Membership } from "@/lib/types";

const props = defineProps<{ membership: Membership; mode: "freeze" | "unfreeze" }>();
const emit = defineEmits<{ close: []; done: [] }>();

const today = new Date().toISOString().slice(0, 10);
const dateValue = ref(today);
const reason = ref("");
const error = ref("");
const freeze = useFreezeMembership();
const unfreeze = useUnfreezeMembership();

async function submit() {
  error.value = "";
  try {
    if (props.mode === "freeze") {
      await freeze.mutateAsync({ id: props.membership.id, start_date: dateValue.value, reason: reason.value });
    } else {
      await unfreeze.mutateAsync({ id: props.membership.id, end_date: dateValue.value, reason: reason.value });
    }
    emit("done");
  } catch (e: any) {
    error.value = e?.response?.data?.error ?? "Failed";
  }
}
const pending = () => freeze.isPending.value || unfreeze.isPending.value;
const input = "w-full rounded border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-400";
</script>

<template>
  <BaseModal :title="mode === 'freeze' ? 'Freeze membership' : 'Unfreeze membership'" @close="emit('close')">
    <form class="space-y-3" @submit.prevent="submit">
      <p class="text-xs text-slate-400">
        {{ mode === 'freeze'
          ? 'Pausing extends the end date by the frozen days on unfreeze.'
          : 'The end date will extend by the number of frozen days.' }}
      </p>
      <div>
        <label class="text-sm text-slate-600">{{ mode === 'freeze' ? 'Freeze from' : 'Unfreeze as of' }}</label>
        <input v-model="dateValue" type="date" :class="input" />
      </div>
      <div>
        <label class="text-sm text-slate-600">Reason</label>
        <input v-model="reason" :class="input" />
      </div>
      <p v-if="error" class="text-sm text-red-600">{{ error }}</p>
      <div class="flex justify-end gap-2 pt-1">
        <button type="button" class="rounded px-3 py-2 text-sm text-slate-600 hover:bg-slate-100" @click="emit('close')">Cancel</button>
        <button type="submit" :disabled="pending()" class="rounded bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-60">
          {{ mode === 'freeze' ? 'Freeze' : 'Unfreeze' }}
        </button>
      </div>
    </form>
  </BaseModal>
</template>
