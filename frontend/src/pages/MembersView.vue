<script setup lang="ts">
import { Download, Plus, Upload } from "@lucide/vue";
import { computed, reactive, ref, watch } from "vue";
import { useRouter } from "vue-router";

import MemberFormDialog from "@/components/MemberFormDialog.vue";
import MemberImportDialog from "@/components/MemberImportDialog.vue";
import Avatar from "@/components/ui/Avatar.vue";
import Button from "@/components/ui/Button.vue";
import {
  downloadMembersExport,
  useDeleteMember,
  useMembers,
  useRestoreMember,
} from "@/composables/useMembers";
import { inputClass, rowClass, tableWrap, theadClass, thClass } from "@/lib/ui";
import type { Member } from "@/lib/types";

const router = useRouter();

const filters = reactive({ search: "", gender: "", sort: "name", page: 1, page_size: 25 });
const searchInput = ref("");
let t: ReturnType<typeof setTimeout>;
watch(searchInput, (v) => {
  clearTimeout(t);
  t = setTimeout(() => { filters.search = v; filters.page = 1; }, 300);
});

const { data, isLoading, isError } = useMembers(() => ({ ...filters }));
const dense = ref(false);

const showForm = ref(false);
const editing = ref<Member | null>(null);
const showImport = ref(false);

const deleteMember = useDeleteMember();
const restoreMember = useRestoreMember();
const lastDeleted = ref<Member | null>(null);

function openAdd() { editing.value = null; showForm.value = true; }
function openEdit(m: Member) { editing.value = m; showForm.value = true; }
async function remove(m: Member) {
  if (!confirm(`Delete ${m.full_name}? You can undo this.`)) return;
  await deleteMember.mutateAsync(m.id);
  lastDeleted.value = m;
  setTimeout(() => { if (lastDeleted.value?.id === m.id) lastDeleted.value = null; }, 8000);
}
async function undo() {
  if (!lastDeleted.value) return;
  await restoreMember.mutateAsync(lastDeleted.value.id);
  lastDeleted.value = null;
}

const totalPages = computed(() => data.value?.num_pages ?? 1);
const rowPad = computed(() => (dense.value ? "py-1.5" : "py-3"));
</script>

<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <div class="flex flex-wrap items-center gap-2">
        <input v-model="searchInput" placeholder="Search name or phone…" :class="[inputClass, 'w-64']" />
        <select v-model="filters.gender" :class="[inputClass, 'w-auto']" @change="filters.page = 1">
          <option value="">All genders</option>
          <option value="male">Male</option><option value="female">Female</option>
          <option value="other">Other</option><option value="unspecified">Unspecified</option>
        </select>
        <select v-model="filters.sort" :class="[inputClass, 'w-auto']">
          <option value="name">Name A–Z</option><option value="-name">Name Z–A</option>
          <option value="-created">Newest</option><option value="created">Oldest</option>
        </select>
        <label class="flex items-center gap-1.5 text-sm text-muted-foreground">
          <input type="checkbox" v-model="dense" class="accent-primary" /> Dense
        </label>
      </div>
      <div class="flex gap-2">
        <Button variant="outline" size="sm" @click="showImport = true"><Upload class="h-4 w-4" /> Import</Button>
        <Button variant="outline" size="sm" @click="downloadMembersExport({ ...filters })"><Download class="h-4 w-4" /> Export</Button>
        <Button size="sm" @click="openAdd"><Plus class="h-4 w-4" /> Add member</Button>
      </div>
    </div>

    <div v-if="lastDeleted" class="flex items-center justify-between rounded-lg border border-warning/30 bg-warning/10 px-4 py-2 text-sm">
      <span>Deleted {{ lastDeleted.full_name }}.</span>
      <button class="font-medium text-warning underline" @click="undo">Undo</button>
    </div>

    <div :class="tableWrap">
      <table class="w-full text-sm">
        <thead :class="theadClass">
          <tr>
            <th :class="thClass">Member</th>
            <th :class="thClass">Phone</th>
            <th :class="thClass">Gender</th>
            <th :class="[thClass, 'w-28']"></th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="isLoading"><td colspan="4" class="px-4 py-10 text-center text-muted-foreground">Loading…</td></tr>
          <tr v-else-if="isError"><td colspan="4" class="px-4 py-10 text-center text-destructive">Failed to load members.</td></tr>
          <tr v-else-if="data && data.results.length === 0"><td colspan="4" class="px-4 py-10 text-center text-muted-foreground">No members found.</td></tr>
          <tr v-for="m in data?.results" :key="m.id" :class="[rowClass, 'cursor-pointer']" @click="router.push(`/members/${m.id}`)">
            <td class="px-4" :class="rowPad">
              <div class="flex items-center gap-3">
                <Avatar :name="m.full_name" size="sm" />
                <span class="font-medium">{{ m.full_name }}</span>
              </div>
            </td>
            <td class="px-4 text-muted-foreground" :class="rowPad">{{ m.phone }}</td>
            <td class="px-4 capitalize text-muted-foreground" :class="rowPad">{{ m.gender }}</td>
            <td class="px-4 text-right" :class="rowPad" @click.stop>
              <button class="mr-3 text-sm text-muted-foreground hover:text-foreground" @click="openEdit(m)">Edit</button>
              <button class="text-sm text-destructive hover:text-destructive/80" @click="remove(m)">Delete</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="data" class="flex items-center justify-between text-sm text-muted-foreground">
      <span>{{ data.count }} member(s)</span>
      <div class="flex items-center gap-2">
        <Button variant="outline" size="sm" :disabled="filters.page <= 1" @click="filters.page--">Prev</Button>
        <span>Page {{ filters.page }} / {{ totalPages }}</span>
        <Button variant="outline" size="sm" :disabled="filters.page >= totalPages" @click="filters.page++">Next</Button>
      </div>
    </div>

    <MemberFormDialog v-if="showForm" :member="editing" @close="showForm = false" @saved="showForm = false" />
    <MemberImportDialog v-if="showImport" @close="showImport = false" @imported="showImport = false" />
  </div>
</template>
