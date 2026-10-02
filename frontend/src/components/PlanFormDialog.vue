<script setup lang="ts">
import { reactive, ref } from "vue";

import BaseModal from "@/components/BaseModal.vue";
import { useSavePlan } from "@/composables/useCatalogue";
import { rupeesToPaise } from "@/lib/money";
import type { Plan } from "@/lib/types";

const props = defineProps<{ plan?: Plan | null }>();
const emit = defineEmits<{ close: []; saved: [] }>();

const form = reactive({
  name: props.plan?.name ?? "",
  plan_type: props.plan?.plan_type ?? "general",
  duration_days: props.plan?.duration_days ?? 30,
  price_rupees: props.plan ? props.plan.price_paise / 100 : 0,
  is_active: props.plan?.is_active ?? true,
});
const error = ref("");
const save = useSavePlan();

async function submit() {
  error.value = "";
  try {
    await save.mutateAsync({
      id: props.plan?.id,
      name: form.name,
      plan_type: form.plan_type as Plan["plan_type"],
      duration_days: Number(form.duration_days),
      price_paise: rupeesToPaise(form.price_rupees),
      is_active: form.is_active,
    });
    emit("saved");
  } catch (e: any) {
    error.value = e?.response?.data?.details?.name?.[0] ?? e?.response?.data?.error ?? "Save failed";
  }
}
const input = "w-full rounded border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-400";
</script>

<template>
  <BaseModal :title="plan ? 'Edit plan' : 'Add plan'" @close="emit('close')">
    <form class="space-y-3" @submit.prevent="submit">
      <div>
        <label class="text-sm text-slate-600">Name</label>
        <input v-model="form.name" required :class="input" />
      </div>
      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="text-sm text-slate-600">Type</label>
          <select v-model="form.plan_type" :class="input">
            <option value="general">General</option>
            <option value="cardio">Cardio</option>
            <option value="gym_cardio">Gym + Cardio</option>
            <option value="custom">Custom</option>
          </select>
        </div>
        <div>
          <label class="text-sm text-slate-600">Duration (days)</label>
          <input v-model.number="form.duration_days" type="number" min="1" required :class="input" />
        </div>
      </div>
      <div>
        <label class="text-sm text-slate-600">Price (₹)</label>
        <input v-model.number="form.price_rupees" type="number" min="0" step="0.01" required :class="input" />
      </div>
      <label class="flex items-center gap-2 text-sm text-slate-600">
        <input type="checkbox" v-model="form.is_active" /> Active
      </label>
      <p v-if="error" class="text-sm text-red-600">{{ error }}</p>
      <div class="flex justify-end gap-2 pt-2">
        <button type="button" class="rounded px-3 py-2 text-sm text-slate-600 hover:bg-slate-100" @click="emit('close')">Cancel</button>
        <button type="submit" :disabled="save.isPending.value" class="rounded bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-60">
          {{ save.isPending.value ? "Saving…" : "Save" }}
        </button>
      </div>
    </form>
  </BaseModal>
</template>
