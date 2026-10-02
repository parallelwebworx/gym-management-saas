<script setup lang="ts">
import { ref } from "vue";

import BaseModal from "@/components/BaseModal.vue";
import { useRefundPayment } from "@/composables/usePayments";
import { formatPaise, rupeesToPaise } from "@/lib/money";
import type { Payment } from "@/lib/types";

const props = defineProps<{ payment: Payment }>();
const emit = defineEmits<{ close: []; done: [] }>();

const amountRupees = ref(props.payment.amount_paise / 100);
const reason = ref("");
const error = ref("");
const refund = useRefundPayment();

async function submit() {
  error.value = "";
  try {
    await refund.mutateAsync({
      id: props.payment.id,
      amount_paise: rupeesToPaise(amountRupees.value),
      reason: reason.value,
    });
    emit("done");
  } catch (e: any) {
    error.value = e?.response?.data?.error ?? "Refund failed";
  }
}
const input = "w-full rounded border border-input px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring/40";
</script>

<template>
  <BaseModal title="Refund payment" @close="emit('close')">
    <form class="space-y-3" @submit.prevent="submit">
      <p class="text-sm text-muted-foreground">
        Invoice {{ payment.invoice_number }} — {{ formatPaise(payment.amount_paise) }}
      </p>
      <div>
        <label class="text-sm text-muted-foreground">Refund amount (₹)</label>
        <input v-model.number="amountRupees" type="number" min="0" step="0.01" :class="input" />
      </div>
      <div>
        <label class="text-sm text-muted-foreground">Reason</label>
        <input v-model="reason" :class="input" />
      </div>
      <p v-if="error" class="text-sm text-red-600">{{ error }}</p>
      <div class="flex justify-end gap-2 pt-1">
        <button type="button" class="rounded px-3 py-2 text-sm text-muted-foreground hover:bg-muted" @click="emit('close')">Cancel</button>
        <button type="submit" :disabled="refund.isPending.value" class="rounded bg-red-600 px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-red-700 disabled:opacity-60">
          {{ refund.isPending.value ? "Refunding…" : "Refund" }}
        </button>
      </div>
    </form>
  </BaseModal>
</template>
