<script setup lang="ts">
import { computed, reactive, ref, watch } from "vue";
import { useRouter } from "vue-router";

import MemberFormDialog from "@/components/MemberFormDialog.vue";
import MemberImportDialog from "@/components/MemberImportDialog.vue";
import {
  downloadMembersExport,
  useDeleteMember,
  useMembers,
  useRestoreMember,
} from "@/composables/useMembers";
import type { Member } from "@/lib/types";

const router = useRouter();

const filters = reactive({
  search: "",
  gender: "",
  sort: "name",
  page: 1,
  page_size: 25,
});

// Debounce search input into the query params.
const searchInput = ref("");
let t: ReturnType<typeof setTimeout>;
watch(searchInput, (v) => {
  clearTimeout(t);
  t = setTimeout(() => {
    filters.search = v;
    filters.page = 1;
  }, 300);
});

const { data, isLoading, isError } = useMembers(() => ({ ...filters }));
const dense = ref(false);

const showForm = ref(false);
const editing = ref<Member | null>(null);
const showImport = ref(false);

const deleteMember = useDeleteMember();
const restoreMember = useRestoreMember();
const lastDeleted = ref<Member | null>(null);

function openAdd() {
  editing.value = null;
  showForm.value = true;
}
function openEdit(m: Member) {
  editing.value = m;
  showForm.value = true;
}
function onSaved() {
  showForm.value = false;
}
async function remove(m: Member) {
  if (!confirm(`Delete ${m.full_name}? You can undo this.`)) return;
  await deleteMember.mutateAsync(m.id);
  lastDeleted.value = m;
  setTimeout(() => {
    if (lastDeleted.value?.id === m.id) lastDeleted.value = null;
  }, 8000);
}
async function undo() {
  if (!lastDeleted.value) return;
  await restoreMember.mutateAsync(lastDeleted.value.id);
  lastDeleted.value = null;
}

const totalPages = computed(() => data.value?.num_pages ?? 1);
const rowPad = computed(() => (dense.value ? "py-1" : "py-2.5"));
</script>

<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <h1 class="text-xl font-semibold text-slate-800">Members</h1>
      <div class="flex gap-2">
        <button class="rounded border border-slate-300 px-3 py-2 text-sm hover:bg-slate-50" @click="showImport = true">
          Import CSV
        </button>
        <button class="rounded border border-slate-300 px-3 py-2 text-sm hover:bg-slate-50" @click="downloadMembersExport({ ...filters })">
          Export Excel
        </button>
        <button class="rounded bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800" @click="openAdd">
          + Add member
        </button>
      </div>
    </div>

    <div class="flex flex-wrap items-center gap-2">
      <input
        v-model="searchInput"
        placeholder="Search name or phone…"
        class="w-64 rounded border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-400"
      />
      <select v-model="filters.gender" class="rounded border border-slate-300 px-2 py-2 text-sm" @change="filters.page = 1">
        <option value="">All genders</option>
        <option value="male">Male</option>
        <option value="female">Female</option>
        <option value="other">Other</option>
        <option value="unspecified">Unspecified</option>
      </select>
      <select v-model="filters.sort" class="rounded border border-slate-300 px-2 py-2 text-sm">
        <option value="name">Name A–Z</option>
        <option value="-name">Name Z–A</option>
        <option value="-created">Newest</option>
        <option value="created">Oldest</option>
      </select>
      <label class="ml-auto flex items-center gap-2 text-sm text-slate-600">
        <input type="checkbox" v-model="dense" /> Dense
      </label>
    </div>

    <div
      v-if="lastDeleted"
      class="flex items-center justify-between rounded bg-amber-50 border border-amber-200 px-4 py-2 text-sm"
    >
      <span>Deleted {{ lastDeleted.full_name }}.</span>
      <button class="font-medium text-amber-800 underline" @click="undo">Undo</button>
    </div>

    <div class="rounded-xl border border-slate-200 bg-white overflow-hidden">
      <table class="w-full text-sm">
        <thead class="bg-slate-50 text-left text-slate-500">
          <tr>
            <th class="px-4 py-2">Name</th>
            <th class="px-4 py-2">Phone</th>
            <th class="px-4 py-2">Gender</th>
            <th class="px-4 py-2 w-28"></th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="isLoading"><td colspan="4" class="px-4 py-8 text-center text-slate-400">Loading…</td></tr>
          <tr v-else-if="isError"><td colspan="4" class="px-4 py-8 text-center text-red-500">Failed to load members.</td></tr>
          <tr v-else-if="data && data.results.length === 0">
            <td colspan="4" class="px-4 py-8 text-center text-slate-400">No members found.</td>
          </tr>
          <tr
            v-for="m in data?.results"
            :key="m.id"
            class="border-t hover:bg-slate-50 cursor-pointer"
            @click="router.push(`/members/${m.id}`)"
          >
            <td class="px-4" :class="rowPad">{{ m.full_name }}</td>
            <td class="px-4" :class="rowPad">{{ m.phone }}</td>
            <td class="px-4 capitalize" :class="rowPad">{{ m.gender }}</td>
            <td class="px-4 text-right" :class="rowPad" @click.stop>
              <button class="text-slate-500 hover:text-slate-800 mr-3" @click="openEdit(m)">Edit</button>
              <button class="text-red-500 hover:text-red-700" @click="remove(m)">Delete</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="data" class="flex items-center justify-between text-sm text-slate-600">
      <span>{{ data.count }} member(s)</span>
      <div class="flex items-center gap-2">
        <button class="rounded border px-2 py-1 disabled:opacity-40" :disabled="filters.page <= 1" @click="filters.page--">Prev</button>
        <span>Page {{ filters.page }} / {{ totalPages }}</span>
        <button class="rounded border px-2 py-1 disabled:opacity-40" :disabled="filters.page >= totalPages" @click="filters.page++">Next</button>
      </div>
    </div>

    <MemberFormDialog v-if="showForm" :member="editing" @close="showForm = false" @saved="onSaved" />
    <MemberImportDialog v-if="showImport" @close="showImport = false" @imported="showImport = false" />
  </div>
</template>
