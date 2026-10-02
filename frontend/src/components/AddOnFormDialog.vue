<script setup lang="ts">
import { reactive, ref } from "vue";

import BaseModal from "@/components/BaseModal.vue";
import { useSaveAddOn } from "@/composables/useCatalogue";
import { rupeesToPaise } from "@/lib/money";
import type { AddOn } from "@/lib/types";

const props = defineProps<{ addon?: AddOn | null }>();
const emit = defineEmits<{ close: []; saved: [] }>();

const form = reactive({
  name: props.addon?.name ?? "",
  addon_type: props.addon?.addon_type ?? "one_time",
  price_rupees: props.addon ? props.addon.price_paise / 100 : 0,
  auto_apply_on_first_enrollment: props.addon?.auto_apply_on_first_enrollment ?? false,
  is_active: props.addon?.is_active ?? true,
});
const error = ref("");
const save = useSaveAddOn();

async function submit() {
  error.value = "";
  try {
    await save.mutateAsync({
      id: props.addon?.id,
      name: form.name,
      addon_type: form.addon_type as AddOn["addon_type"],
      price_paise: rupeesToPaise(form.price_rupees),
      auto_apply_on_first_enrollment: form.auto_apply_on_first_enrollment,
      is_active: form.is_active,
    });
    emit("saved");
  } catch (e: any) {
    error.value = e?.response?.data?.details?.name?.[0] ?? e?.response?.data?.error ?? "Save failed";
  }
}
const input = "w-full rounded border border-input px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring/40";
</script>

<template>
  <BaseModal :title="addon ? 'Edit add-on' : 'Add add-on'" @close="emit('close')">
    <form class="space-y-3" @submit.prevent="submit">
      <div>
        <label class="text-sm text-muted-foreground">Name</label>
        <input v-model="form.name" required :class="input" />
      </div>
      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="text-sm text-muted-foreground">Type</label>
          <select v-model="form.addon_type" :class="input">
            <option value="one_time">One-time</option>
            <option value="recurring">Recurring</option>
          </select>
        </div>
        <div>
          <label class="text-sm text-muted-foreground">Price (₹)</label>
          <input v-model.number="form.price_rupees" type="number" min="0" step="0.01" required :class="input" />
        </div>
      </div>
      <label class="flex items-center gap-2 text-sm text-muted-foreground">
        <input type="checkbox" v-model="form.auto_apply_on_first_enrollment" /> Auto-apply on first enrollment
      </label>
      <label class="flex items-center gap-2 text-sm text-muted-foreground">
        <input type="checkbox" v-model="form.is_active" /> Active
      </label>
      <p v-if="error" class="text-sm text-red-600">{{ error }}</p>
      <div class="flex justify-end gap-2 pt-2">
        <button type="button" class="rounded px-3 py-2 text-sm text-muted-foreground hover:bg-muted" @click="emit('close')">Cancel</button>
        <button type="submit" :disabled="save.isPending.value" class="rounded bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-60">
          {{ save.isPending.value ? "Saving…" : "Save" }}
        </button>
      </div>
    </form>
  </BaseModal>
</template>
