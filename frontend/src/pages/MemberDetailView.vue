<script setup lang="ts">
import { computed } from "vue";
import { useRoute, useRouter } from "vue-router";

import { useMember } from "@/composables/useMembers";

const route = useRoute();
const router = useRouter();
const id = computed(() => Number(route.params.id));
const { data: member, isLoading, isError } = useMember(id);

const waLink = computed(() =>
  member.value ? `https://wa.me/${member.value.phone.replace(/\D/g, "")}` : "#",
);
const telLink = computed(() => (member.value ? `tel:${member.value.phone}` : "#"));
</script>

<template>
  <div class="space-y-4">
    <button class="text-sm text-slate-500 hover:text-slate-800" @click="router.push('/members')">
      ← Back to members
    </button>

    <div v-if="isLoading" class="text-slate-400">Loading…</div>
    <div v-else-if="isError" class="text-red-500">Member not found.</div>

    <template v-else-if="member">
      <div class="rounded-xl border border-slate-200 bg-white p-6">
        <div class="flex items-start justify-between">
          <div>
            <h1 class="text-xl font-semibold text-slate-800">{{ member.full_name }}</h1>
            <p class="text-slate-500">{{ member.phone }}</p>
          </div>
          <div class="flex gap-2">
            <a :href="telLink" class="rounded border border-slate-300 px-3 py-1.5 text-sm hover:bg-slate-50">Call</a>
            <a :href="waLink" target="_blank" class="rounded bg-emerald-600 px-3 py-1.5 text-sm text-white hover:bg-emerald-700">WhatsApp</a>
          </div>
        </div>
        <dl class="mt-4 grid grid-cols-2 gap-x-8 gap-y-2 text-sm">
          <div><dt class="text-slate-400">Email</dt><dd>{{ member.email || "—" }}</dd></div>
          <div><dt class="text-slate-400">Gender</dt><dd class="capitalize">{{ member.gender }}</dd></div>
          <div><dt class="text-slate-400">Date of birth</dt><dd>{{ member.date_of_birth || "—" }}</dd></div>
          <div><dt class="text-slate-400">Address</dt><dd>{{ member.address || "—" }}</dd></div>
          <div class="col-span-2"><dt class="text-slate-400">Notes</dt><dd>{{ member.notes || "—" }}</dd></div>
        </dl>
      </div>

      <div class="rounded-xl border border-dashed border-slate-300 bg-slate-50 p-6 text-sm text-slate-500">
        Membership, payments, freeze history, and activity appear here once the revenue loop lands (Phase 2+).
      </div>
    </template>
  </div>
</template>
