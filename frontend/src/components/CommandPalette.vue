<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch } from "vue";
import { useRouter } from "vue-router";

import { api, unwrap } from "@/lib/api";
import type { Member, Paginated } from "@/lib/types";

const router = useRouter();
const open = ref(false);
const query = ref("");
const results = ref<Member[]>([]);
const active = ref(0);

function onKey(e: KeyboardEvent) {
  if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
    e.preventDefault();
    open.value = !open.value;
  } else if (e.key === "Escape") {
    open.value = false;
  }
}

onMounted(() => window.addEventListener("keydown", onKey));
onUnmounted(() => window.removeEventListener("keydown", onKey));

let t: ReturnType<typeof setTimeout>;
watch(query, (q) => {
  clearTimeout(t);
  if (!q.trim()) {
    results.value = [];
    return;
  }
  t = setTimeout(async () => {
    try {
      const data = await unwrap<Paginated<Member>>(
        api.get("/members/", { params: { search: q, page_size: 8 } }),
      );
      results.value = data.results;
      active.value = 0;
    } catch {
      results.value = [];
    }
  }, 200);
});

watch(open, (v) => {
  if (!v) {
    query.value = "";
    results.value = [];
  }
});

function go(m: Member) {
  open.value = false;
  router.push(`/members/${m.id}`);
}

function onListKey(e: KeyboardEvent) {
  if (e.key === "ArrowDown") active.value = Math.min(active.value + 1, results.value.length - 1);
  else if (e.key === "ArrowUp") active.value = Math.max(active.value - 1, 0);
  else if (e.key === "Enter" && results.value[active.value]) go(results.value[active.value]);
}
</script>

<template>
  <div v-if="open" class="fixed inset-0 z-50 flex items-start justify-center bg-black/30 p-4 pt-24" @click.self="open = false">
    <div class="w-full max-w-lg rounded-xl bg-white shadow-xl border border-slate-200 overflow-hidden">
      <input
        v-model="query"
        autofocus
        placeholder="Search members…"
        class="w-full px-4 py-3 text-sm focus:outline-none border-b"
        @keydown="onListKey"
      />
      <ul v-if="results.length" class="max-h-72 overflow-auto">
        <li
          v-for="(m, i) in results"
          :key="m.id"
          class="flex items-center justify-between px-4 py-2 text-sm cursor-pointer"
          :class="i === active ? 'bg-slate-100' : 'hover:bg-slate-50'"
          @mouseenter="active = i"
          @click="go(m)"
        >
          <span>{{ m.full_name }}</span>
          <span class="text-slate-400">{{ m.phone }}</span>
        </li>
      </ul>
      <p v-else-if="query" class="px-4 py-6 text-center text-sm text-slate-400">No matches</p>
      <p v-else class="px-4 py-6 text-center text-sm text-slate-400">Type to search members</p>
    </div>
  </div>
</template>
