<script setup lang="ts">
import { computed, reactive, ref } from "vue";

import BaseModal from "@/components/BaseModal.vue";
import { useAddOns, usePlans } from "@/composables/useCatalogue";
import { useEnroll, useRenew } from "@/composables/useMemberships";
import { formatPaise, rupeesToPaise } from "@/lib/money";
import type { Membership } from "@/lib/types";

const props = defineProps<{ memberId: number; renewOf?: Membership | null }>();
const emit = defineEmits<{ close: []; done: [] }>();

const isRenew = computed(() => !!props.renewOf);
const { data: plans } = usePlans();
const { data: addons } = useAddOns();
const enroll = useEnroll();
const renew = useRenew();

const form = reactive({
  plan_id: props.renewOf?.plan ?? 0,
  addon_ids: [] as number[],
  discount_rupees: 0,
  method: "cash",
  start_mode: "from_previous_end" as "from_today" | "from_previous_end" | "custom",
  custom_start_date: "",
});
const error = ref("");

const selectedPlan = computed(() => plans.value?.results.find((p) => p.id === form.plan_id) ?? null);
const total = computed(() => {
  const planPrice = selectedPlan.value?.price_paise ?? 0;
  const addonSum = (addons.value?.results ?? [])
    .filter((a) => form.addon_ids.includes(a.id))
    .reduce((s, a) => s + a.price_paise, 0);
  return Math.max(planPrice + addonSum - rupeesToPaise(form.discount_rupees), 0);
});

async function submit() {
  error.value = "";
  if (!form.plan_id) {
    error.value = "Select a plan.";
    return;
  }
  try {
    const common = {
      plan_id: form.plan_id,
      addon_ids: form.addon_ids,
      discount_paise: rupeesToPaise(form.discount_rupees),
      method: form.method,
    };
    if (isRenew.value && props.renewOf) {
      await renew.mutateAsync({
        id: props.renewOf.id,
        payload: {
          ...common,
          start_mode: form.start_mode,
          custom_start_date: form.start_mode === "custom" ? form.custom_start_date : null,
        },
      });
    } else {
      await enroll.mutateAsync({ member_id: props.memberId, ...common });
    }
    emit("done");
  } catch (e: any) {
    error.value = e?.response?.data?.error ?? (e instanceof Error ? e.message : "Failed");
  }
}

const input = "w-full rounded border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-400";
const pending = computed(() => enroll.isPending.value || renew.isPending.value);
</script>

<template>
  <BaseModal :title="isRenew ? 'Renew membership' : 'Enroll in a plan'" @close="emit('close')">
    <form class="space-y-3" @submit.prevent="submit">
      <div>
        <label class="text-sm text-slate-600">Plan</label>
        <select v-model.number="form.plan_id" :class="input">
          <option :value="0" disabled>Select a plan…</option>
          <option v-for="p in plans?.results.filter((x) => x.is_active)" :key="p.id" :value="p.id">
            {{ p.name }} — {{ formatPaise(p.price_paise) }} / {{ p.duration_days }}d
          </option>
        </select>
      </div>

      <div v-if="addons && addons.results.length">
        <label class="text-sm text-slate-600">Add-ons</label>
        <div class="mt-1 space-y-1">
          <label v-for="a in addons.results.filter((x) => x.is_active)" :key="a.id" class="flex items-center gap-2 text-sm">
            <input type="checkbox" :value="a.id" v-model="form.addon_ids" />
            {{ a.name }} — {{ formatPaise(a.price_paise) }}
            <span v-if="a.auto_apply_on_first_enrollment" class="text-xs text-slate-400">(auto on 1st enroll)</span>
          </label>
        </div>
      </div>

      <div v-if="isRenew">
        <label class="text-sm text-slate-600">Start</label>
        <select v-model="form.start_mode" :class="input">
          <option value="from_previous_end">From previous end date</option>
          <option value="from_today">From today</option>
          <option value="custom">Custom date</option>
        </select>
        <input v-if="form.start_mode === 'custom'" v-model="form.custom_start_date" type="date" :class="[input, 'mt-2']" />
      </div>

      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="text-sm text-slate-600">Discount (₹)</label>
          <input v-model.number="form.discount_rupees" type="number" min="0" step="0.01" :class="input" />
        </div>
        <div>
          <label class="text-sm text-slate-600">Method</label>
          <select v-model="form.method" :class="input">
            <option value="cash">Cash</option>
            <option value="card">Card</option>
            <option value="upi">UPI</option>
            <option value="bank">Bank transfer</option>
            <option value="other">Other</option>
          </select>
        </div>
      </div>

      <div class="rounded bg-slate-50 px-3 py-2 text-sm flex items-center justify-between">
        <span class="text-slate-500">Total payable</span>
        <span class="font-semibold">{{ formatPaise(total) }}</span>
      </div>
      <p v-if="!isRenew" class="text-xs text-slate-400">
        Auto-applied fees (e.g. joining) are added by the server on a member's first enrollment.
      </p>

      <p v-if="error" class="text-sm text-red-600">{{ error }}</p>

      <div class="flex justify-end gap-2 pt-1">
        <button type="button" class="rounded px-3 py-2 text-sm text-slate-600 hover:bg-slate-100" @click="emit('close')">Cancel</button>
        <button type="submit" :disabled="pending" class="rounded bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-60">
          {{ pending ? "Saving…" : isRenew ? "Renew" : "Enroll & collect" }}
        </button>
      </div>
    </form>
  </BaseModal>
</template>
