<script setup lang="ts">
import { ref, watch } from "vue";

import { useSendTestMessage } from "@/composables/useNotifications";
import {
  downloadDataExport,
  useBranchesAdmin,
  useChangePassword,
  useGymSettings,
  useSaveBranch,
  useSaveGymSettings,
  useSubscription,
} from "@/composables/useSettings";

const { data: gym } = useGymSettings();
const { data: subscription } = useSubscription();
const { data: branches } = useBranchesAdmin();
const saveGym = useSaveGymSettings();
const saveBranch = useSaveBranch();
const changePassword = useChangePassword();
const sendTest = useSendTestMessage();

// Gym profile form (kept in sync when data loads).
const form = ref({ name: "", gstin: "", invoice_prefix: "", notifications_enabled: true });
watch(gym, (g) => {
  if (g) form.value = { name: g.name, gstin: g.gstin, invoice_prefix: g.invoice_prefix, notifications_enabled: g.notifications_enabled };
}, { immediate: true });
const gymMsg = ref("");

async function saveProfile() {
  gymMsg.value = "";
  try {
    await saveGym.mutateAsync({ ...form.value });
    gymMsg.value = "Saved.";
  } catch (e: any) {
    gymMsg.value = e?.response?.data?.error ?? "Save failed";
  }
}

// Branch management.
const newBranch = ref("");
const branchMsg = ref("");
async function addBranch() {
  if (!newBranch.value.trim()) return;
  try {
    await saveBranch.mutateAsync({ name: newBranch.value.trim() });
    newBranch.value = "";
    branchMsg.value = "";
  } catch (e: any) {
    branchMsg.value = e?.response?.data?.error ?? "Failed";
  }
}
async function toggleBranch(b: { id: number; is_active: boolean }) {
  branchMsg.value = "";
  try {
    await saveBranch.mutateAsync({ id: b.id, is_active: !b.is_active });
  } catch (e: any) {
    branchMsg.value = e?.response?.data?.error ?? "Failed";
  }
}

// Notifications test.
const testPhone = ref("");
const testMsg = ref("");
async function runTest() {
  testMsg.value = "";
  try {
    const n = await sendTest.mutateAsync({ phone: testPhone.value });
    testMsg.value = `Test message ${n.status}.`;
  } catch (e: any) {
    testMsg.value = e?.response?.data?.error ?? "Failed";
  }
}

// Password.
const pw = ref({ current_password: "", new_password: "" });
const pwMsg = ref("");
async function updatePassword() {
  pwMsg.value = "";
  try {
    await changePassword.mutateAsync({ ...pw.value });
    pwMsg.value = "Password changed.";
    pw.value = { current_password: "", new_password: "" };
  } catch (e: any) {
    pwMsg.value = e?.response?.data?.error ?? "Failed";
  }
}

const input = "w-full rounded border border-input px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring/40";
const card = "rounded-xl border border-border bg-card p-6 space-y-3";
</script>

<template>
  <div class="space-y-6 max-w-3xl">
    <h1 class="text-xl font-semibold text-foreground">Settings</h1>

    <!-- Gym profile -->
    <section :class="card">
      <h2 class="font-medium text-foreground">Gym profile</h2>
      <div class="grid grid-cols-2 gap-3">
        <div><label class="text-sm text-muted-foreground">Name</label><input v-model="form.name" :class="input" /></div>
        <div><label class="text-sm text-muted-foreground">Invoice prefix</label><input v-model="form.invoice_prefix" :class="input" /></div>
        <div class="col-span-2"><label class="text-sm text-muted-foreground">GSTIN</label><input v-model="form.gstin" :class="input" placeholder="15-char GSTIN (optional)" /></div>
      </div>
      <label class="flex items-center gap-2 text-sm text-muted-foreground">
        <input type="checkbox" v-model="form.notifications_enabled" /> Send transactional notifications
      </label>
      <div class="flex items-center gap-3">
        <button class="rounded bg-primary px-4 py-2 text-sm text-primary-foreground hover:bg-primary/90" @click="saveProfile">Save</button>
        <span class="text-sm text-emerald-600">{{ gymMsg }}</span>
      </div>
    </section>

    <!-- Branches -->
    <section :class="card">
      <h2 class="font-medium text-foreground">Branches</h2>
      <div v-for="b in branches?.results" :key="b.id" class="flex items-center justify-between border-b py-2 text-sm last:border-0">
        <span>{{ b.name }} <span v-if="!b.is_active" class="ml-2 text-xs text-muted-foreground">(inactive)</span></span>
        <button class="text-muted-foreground hover:text-foreground" @click="toggleBranch(b)">
          {{ b.is_active ? "Deactivate" : "Activate" }}
        </button>
      </div>
      <div class="flex items-center gap-2">
        <input v-model="newBranch" placeholder="New branch name" :class="input" />
        <button class="rounded border border-input px-3 py-2 text-sm hover:bg-muted/40 whitespace-nowrap" @click="addBranch">Add</button>
      </div>
      <p v-if="branchMsg" class="text-sm text-red-600">{{ branchMsg }}</p>
    </section>

    <!-- Notifications -->
    <section :class="card">
      <h2 class="font-medium text-foreground">Notifications</h2>
      <p class="text-sm text-muted-foreground">Send a test message to verify your provider setup.</p>
      <div class="flex items-center gap-2">
        <input v-model="testPhone" placeholder="Phone (e.g. 9876543210)" :class="input" />
        <button class="rounded border border-input px-3 py-2 text-sm hover:bg-muted/40 whitespace-nowrap" @click="runTest">Send test</button>
      </div>
      <p v-if="testMsg" class="text-sm text-emerald-600">{{ testMsg }}</p>
    </section>

    <!-- Subscription -->
    <section :class="card">
      <h2 class="font-medium text-foreground">Subscription</h2>
      <p class="text-sm">
        Current plan: <span class="font-semibold uppercase">{{ subscription?.tier }}</span>
        <span v-if="!subscription?.whatsapp_enabled" class="ml-2 text-xs text-muted-foreground">(WhatsApp requires Pro)</span>
      </p>
    </section>

    <!-- Data export -->
    <section :class="card">
      <h2 class="font-medium text-foreground">Data export</h2>
      <p class="text-sm text-muted-foreground">Download all your data as a multi-sheet Excel workbook.</p>
      <button class="rounded border border-input px-4 py-2 text-sm hover:bg-muted/40" @click="downloadDataExport">Export all data (.xlsx)</button>
    </section>

    <!-- Account -->
    <section :class="card">
      <h2 class="font-medium text-foreground">Change password</h2>
      <div class="grid grid-cols-2 gap-3">
        <div><label class="text-sm text-muted-foreground">Current</label><input v-model="pw.current_password" type="password" :class="input" /></div>
        <div><label class="text-sm text-muted-foreground">New</label><input v-model="pw.new_password" type="password" :class="input" /></div>
      </div>
      <div class="flex items-center gap-3">
        <button class="rounded bg-primary px-4 py-2 text-sm text-primary-foreground hover:bg-primary/90" @click="updatePassword">Update password</button>
        <span class="text-sm" :class="pwMsg.includes('changed') ? 'text-emerald-600' : 'text-red-600'">{{ pwMsg }}</span>
      </div>
    </section>
  </div>
</template>
