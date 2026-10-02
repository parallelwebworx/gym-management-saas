<script setup lang="ts">
import { computed, ref } from "vue";
import { useRoute, useRouter } from "vue-router";

import CancelDialog from "@/components/CancelDialog.vue";
import CorrectDialog from "@/components/CorrectDialog.vue";
import EditPaymentDialog from "@/components/EditPaymentDialog.vue";
import EnrollDialog from "@/components/EnrollDialog.vue";
import FreezeDialog from "@/components/FreezeDialog.vue";
import RefundDialog from "@/components/RefundDialog.vue";
import { useMember } from "@/composables/useMembers";
import { useMemberMemberships } from "@/composables/useMemberships";
import { useNotifications, useResendNotification } from "@/composables/useNotifications";
import { openInvoicePdf, usePayments } from "@/composables/usePayments";
import { formatPaise } from "@/lib/money";
import type { Membership, Payment } from "@/lib/types";
import { useAuthStore } from "@/stores/auth";

const route = useRoute();
const router = useRouter();
const auth = useAuthStore();
const id = computed(() => Number(route.params.id));
const isOwner = computed(() => auth.role === "owner");

const { data: member, isLoading, isError } = useMember(id);
const { data: memberships } = useMemberMemberships(id);
const { data: payments } = usePayments(() => ({ member: id.value }));
const { data: notifications } = useNotifications(() => ({ member: id.value }));
const resendNotification = useResendNotification();

const current = computed<Membership | null>(() => memberships.value?.results[0] ?? null);
const hasActive = computed(() => current.value?.status === "active");

const showEnroll = ref(false);
const renewOf = ref<Membership | null>(null);
const showCancel = ref<Membership | null>(null);
const showCorrect = ref<Membership | null>(null);
const freezeDialog = ref<{ membership: Membership; mode: "freeze" | "unfreeze" } | null>(null);
const refundOf = ref<Payment | null>(null);
const editOf = ref<Payment | null>(null);

function openEnroll() {
  renewOf.value = null;
  showEnroll.value = true;
}
function openRenew(m: Membership) {
  renewOf.value = m;
  showEnroll.value = true;
}
function closeEnroll() {
  showEnroll.value = false;
  renewOf.value = null;
}

const waLink = computed(() => (member.value ? `https://wa.me/${member.value.phone.replace(/\D/g, "")}` : "#"));
const telLink = computed(() => (member.value ? `tel:${member.value.phone}` : "#"));

const statusClass: Record<string, string> = {
  active: "bg-emerald-100 text-emerald-700",
  expired: "bg-muted text-muted-foreground",
  cancelled: "bg-red-100 text-red-700",
  frozen: "bg-sky-100 text-sky-700",
};
const kindClass: Record<string, string> = {
  refund: "text-red-600",
  enrollment: "text-foreground",
  renewal: "text-foreground",
  adjustment: "text-foreground",
};
</script>

<template>
  <div class="space-y-4">
    <button class="text-sm text-muted-foreground hover:text-foreground" @click="router.push('/members')">← Back to members</button>

    <div v-if="isLoading" class="text-muted-foreground">Loading…</div>
    <div v-else-if="isError" class="text-red-500">Member not found.</div>

    <template v-else-if="member">
      <!-- Profile -->
      <div class="rounded-xl border border-border bg-card p-6">
        <div class="flex items-start justify-between">
          <div>
            <h1 class="text-xl font-semibold text-foreground">{{ member.full_name }}</h1>
            <p class="text-muted-foreground">{{ member.phone }}</p>
          </div>
          <div class="flex gap-2">
            <a :href="telLink" class="rounded border border-input px-3 py-1.5 text-sm hover:bg-muted/40">Call</a>
            <a :href="waLink" target="_blank" class="rounded bg-emerald-600 px-3 py-1.5 text-sm text-primary-foreground hover:bg-emerald-700">WhatsApp</a>
          </div>
        </div>
      </div>

      <!-- Current membership -->
      <div class="rounded-xl border border-border bg-card p-6 space-y-3">
        <div class="flex items-center justify-between">
          <h2 class="font-medium text-foreground">Membership</h2>
          <button v-if="!hasActive" class="rounded bg-primary px-3 py-1.5 text-sm text-primary-foreground hover:bg-primary/90" @click="openEnroll">
            + Enroll
          </button>
        </div>

        <div v-if="current" class="space-y-2">
          <div class="flex items-center gap-3">
            <span class="font-medium">{{ current.plan_name }}</span>
            <span class="rounded px-2 py-0.5 text-xs capitalize" :class="statusClass[current.status]">{{ current.status }}</span>
            <span v-if="current.correction_count" class="text-xs text-muted-foreground">corrected ×{{ current.correction_count }}</span>
          </div>
          <div class="text-sm text-muted-foreground">
            {{ current.start_date }} → {{ current.end_date }}
            <span v-if="current.end_date !== current.original_end_date">(original {{ current.original_end_date }})</span>
          </div>
          <div class="text-sm text-muted-foreground">
            Net paid: {{ formatPaise(current.net_paid_paise) }}
            <span v-if="current.total_days_added" class="ml-2">· +{{ current.total_days_added }} frozen day(s)</span>
          </div>
          <div class="flex flex-wrap gap-2 pt-1">
            <button class="rounded border border-input px-3 py-1.5 text-sm hover:bg-muted/40" @click="openRenew(current)">Renew</button>
            <button class="rounded border border-input px-3 py-1.5 text-sm hover:bg-muted/40" @click="showCorrect = current">Correct</button>
            <button
              v-if="current.status === 'active'"
              class="rounded border border-sky-200 px-3 py-1.5 text-sm text-sky-700 hover:bg-sky-50"
              @click="freezeDialog = { membership: current, mode: 'freeze' }"
            >
              Freeze
            </button>
            <button
              v-if="current.status === 'frozen'"
              class="rounded border border-sky-200 px-3 py-1.5 text-sm text-sky-700 hover:bg-sky-50"
              @click="freezeDialog = { membership: current, mode: 'unfreeze' }"
            >
              Unfreeze
            </button>
            <button v-if="isOwner && current.status !== 'cancelled'" class="rounded border border-red-200 px-3 py-1.5 text-sm text-red-600 hover:bg-red-50" @click="showCancel = current">
              Cancel
            </button>
          </div>
          <div v-if="current.freezes.length" class="pt-2 text-xs text-muted-foreground">
            Freeze history:
            <span v-for="f in current.freezes" :key="f.id" class="mr-2">
              {{ f.freeze_start_date }}→{{ f.freeze_end_date || 'open' }}{{ f.days_added ? ` (+${f.days_added}d)` : '' }}
            </span>
          </div>
        </div>
        <p v-else class="text-sm text-muted-foreground">No membership yet.</p>
      </div>

      <!-- Payments ledger -->
      <div class="rounded-xl border border-border bg-card overflow-hidden">
        <h2 class="px-6 pt-4 font-medium text-foreground">Payments</h2>
        <table class="w-full text-sm mt-2">
          <thead class="bg-muted/40 text-left text-muted-foreground">
            <tr>
              <th class="px-6 py-2">Invoice</th><th class="px-4 py-2">Kind</th>
              <th class="px-4 py-2">Amount</th><th class="px-4 py-2">Method</th>
              <th class="px-4 py-2">Date</th><th class="px-4 py-2 w-28"></th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="payments && payments.results.length === 0"><td colspan="6" class="px-6 py-6 text-center text-muted-foreground">No payments yet.</td></tr>
            <tr v-for="p in payments?.results" :key="p.id" class="border-t">
              <td class="px-6 py-2">{{ p.invoice_number }}</td>
              <td class="px-4 py-2 capitalize">{{ p.kind }}</td>
              <td class="px-4 py-2" :class="kindClass[p.kind]">
                {{ formatPaise(p.amount_paise) }}
                <span v-if="p.edited" class="ml-1 text-xs text-amber-600">(edited)</span>
              </td>
              <td class="px-4 py-2 capitalize">{{ p.method }}</td>
              <td class="px-4 py-2 text-muted-foreground">{{ new Date(p.created_at).toLocaleDateString() }}</td>
              <td class="px-4 py-2 text-right whitespace-nowrap">
                <button class="text-muted-foreground hover:text-foreground mr-3" @click="openInvoicePdf(p.id)">Invoice</button>
                <template v-if="isOwner && p.kind !== 'refund'">
                  <button class="text-muted-foreground hover:text-foreground mr-3" @click="editOf = p">Edit</button>
                  <button class="text-red-500 hover:text-red-700" @click="refundOf = p">Refund</button>
                </template>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Notifications / messages -->
      <div class="rounded-xl border border-border bg-card overflow-hidden">
        <h2 class="px-6 pt-4 font-medium text-foreground">Messages</h2>
        <table class="w-full text-sm mt-2">
          <thead class="bg-muted/40 text-left text-muted-foreground">
            <tr>
              <th class="px-6 py-2">Event</th><th class="px-4 py-2">Channel</th>
              <th class="px-4 py-2">Status</th><th class="px-4 py-2">When</th>
              <th class="px-4 py-2 w-24"></th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="notifications && notifications.results.length === 0"><td colspan="5" class="px-6 py-6 text-center text-muted-foreground">No messages yet.</td></tr>
            <tr v-for="n in notifications?.results" :key="n.id" class="border-t">
              <td class="px-6 py-2 capitalize">{{ n.event }}</td>
              <td class="px-4 py-2 uppercase text-xs">{{ n.channel }}</td>
              <td class="px-4 py-2">
                <span class="rounded px-2 py-0.5 text-xs capitalize"
                      :class="n.status === 'sent' ? 'bg-emerald-100 text-emerald-700' : n.status === 'failed' ? 'bg-red-100 text-red-700' : 'bg-muted text-muted-foreground'">
                  {{ n.status }}
                </span>
              </td>
              <td class="px-4 py-2 text-muted-foreground">{{ n.sent_at ? new Date(n.sent_at).toLocaleString() : "—" }}</td>
              <td class="px-4 py-2 text-right">
                <button v-if="isOwner && n.status !== 'sent'" class="text-muted-foreground hover:text-foreground" @click="resendNotification.mutate(n.id)">Resend</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <EnrollDialog v-if="showEnroll" :member-id="member.id" :renew-of="renewOf" @close="closeEnroll" @done="closeEnroll" />
      <CancelDialog v-if="showCancel" :membership="showCancel" @close="showCancel = null" @done="showCancel = null" />
      <CorrectDialog v-if="showCorrect" :membership="showCorrect" @close="showCorrect = null" @done="showCorrect = null" />
      <FreezeDialog
        v-if="freezeDialog"
        :membership="freezeDialog.membership"
        :mode="freezeDialog.mode"
        @close="freezeDialog = null"
        @done="freezeDialog = null"
      />
      <RefundDialog v-if="refundOf" :payment="refundOf" @close="refundOf = null" @done="refundOf = null" />
      <EditPaymentDialog v-if="editOf" :payment="editOf" @close="editOf = null" @done="editOf = null" />
    </template>
  </div>
</template>
