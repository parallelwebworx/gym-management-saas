<script setup lang="ts">
import { ref } from "vue";

import BaseModal from "@/components/BaseModal.vue";
import { api } from "@/lib/api";
import { useImportMembers } from "@/composables/useMembers";
import type { ImportResult } from "@/lib/types";

const emit = defineEmits<{ close: []; imported: [] }>();

const file = ref<File | null>(null);
const preview = ref<ImportResult | null>(null);
const error = ref("");
const importMembers = useImportMembers();

function onFile(e: Event) {
  const f = (e.target as HTMLInputElement).files?.[0] ?? null;
  file.value = f;
  preview.value = null;
  error.value = "";
}

async function runPreview() {
  if (!file.value) return;
  error.value = "";
  try {
    preview.value = await importMembers.mutateAsync({ file: file.value, commit: false });
  } catch (e: any) {
    error.value = e?.response?.data?.error ?? "Could not read the CSV.";
  }
}

async function runCommit() {
  if (!file.value) return;
  try {
    const res = await importMembers.mutateAsync({ file: file.value, commit: true });
    preview.value = res;
    emit("imported");
  } catch (e: any) {
    error.value = e?.response?.data?.error ?? "Import failed.";
  }
}

async function downloadTemplate() {
  const resp = await api.get("/members/import-template/", { responseType: "blob" });
  const url = URL.createObjectURL(resp.data as Blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "members_import_template.csv";
  a.click();
  URL.revokeObjectURL(url);
}

const badge: Record<string, string> = {
  ok: "bg-emerald-100 text-emerald-700",
  error: "bg-red-100 text-red-700",
  duplicate_in_file: "bg-amber-100 text-amber-700",
  duplicate_existing: "bg-amber-100 text-amber-700",
};
</script>

<template>
  <BaseModal title="Import members (CSV)" wide @close="emit('close')">
    <div class="space-y-4">
      <div class="flex items-center justify-between">
        <input type="file" accept=".csv" @change="onFile" class="text-sm" />
        <button class="text-sm text-muted-foreground underline" @click="downloadTemplate">
          Download template
        </button>
      </div>

      <div class="flex gap-2">
        <button
          class="rounded border border-input px-3 py-2 text-sm hover:bg-muted/40 disabled:opacity-50"
          :disabled="!file || importMembers.isPending.value"
          @click="runPreview"
        >
          Preview
        </button>
        <button
          class="rounded bg-primary px-3 py-2 text-sm text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
          :disabled="!preview || preview.summary.valid === 0 || preview.committed"
          @click="runCommit"
        >
          Import {{ preview ? preview.summary.valid : "" }} valid row(s)
        </button>
      </div>

      <p v-if="error" class="text-sm text-red-600">{{ error }}</p>

      <div v-if="preview" class="space-y-2">
        <div class="flex gap-4 text-sm">
          <span>Total: <b>{{ preview.summary.total }}</b></span>
          <span class="text-emerald-700">Valid: <b>{{ preview.summary.valid }}</b></span>
          <span class="text-red-700">Errors: <b>{{ preview.summary.errors }}</b></span>
          <span class="text-amber-700">Duplicates: <b>{{ preview.summary.duplicates }}</b></span>
          <span v-if="preview.committed" class="text-emerald-700">
            ✓ Inserted {{ preview.inserted }}
          </span>
        </div>
        <div class="max-h-64 overflow-auto rounded border border-border">
          <table class="w-full text-sm">
            <thead class="bg-muted/40 text-left text-muted-foreground">
              <tr>
                <th class="px-3 py-2">Row</th>
                <th class="px-3 py-2">Name</th>
                <th class="px-3 py-2">Phone</th>
                <th class="px-3 py-2">Status</th>
                <th class="px-3 py-2">Issues</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="r in preview.rows" :key="r.row" class="border-t">
                <td class="px-3 py-1.5">{{ r.row }}</td>
                <td class="px-3 py-1.5">{{ r.full_name }}</td>
                <td class="px-3 py-1.5">{{ r.phone }}</td>
                <td class="px-3 py-1.5">
                  <span class="rounded px-2 py-0.5 text-xs" :class="badge[r.status]">{{ r.status }}</span>
                </td>
                <td class="px-3 py-1.5 text-xs text-muted-foreground">{{ r.errors.join("; ") }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </BaseModal>
</template>
