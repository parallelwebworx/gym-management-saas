<script setup lang="ts">
import { onMounted, onUnmounted } from "vue";

import { cn } from "@/lib/utils";

defineProps<{ title: string; wide?: boolean }>();
const emit = defineEmits<{ close: [] }>();

function onKey(e: KeyboardEvent) {
  if (e.key === "Escape") emit("close");
}
onMounted(() => window.addEventListener("keydown", onKey));
onUnmounted(() => window.removeEventListener("keydown", onKey));
</script>

<template>
  <div
    class="fixed inset-0 z-40 flex items-start justify-center overflow-y-auto bg-foreground/30 p-4 pt-20 backdrop-blur-sm"
    @click.self="emit('close')"
  >
    <div
      :class="cn(
        'w-full rounded-xl border border-border bg-card shadow-xl animate-in fade-in zoom-in-95 duration-200',
        wide ? 'max-w-3xl' : 'max-w-md',
      )"
    >
      <div class="flex items-center justify-between border-b border-border px-5 py-3.5">
        <h2 class="font-semibold text-foreground">{{ title }}</h2>
        <button
          class="rounded-md p-1 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
          @click="emit('close')"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18M6 6l12 12"/></svg>
        </button>
      </div>
      <div class="p-5">
        <slot />
      </div>
    </div>
  </div>
</template>
