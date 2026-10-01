<script setup lang="ts">
defineProps<{ title: string; wide?: boolean }>();
const emit = defineEmits<{ close: [] }>();
</script>

<template>
  <div
    class="fixed inset-0 z-40 flex items-start justify-center bg-black/30 p-4 pt-20"
    @click.self="emit('close')"
  >
    <div
      class="w-full rounded-xl bg-white shadow-lg border border-slate-200"
      :class="wide ? 'max-w-3xl' : 'max-w-md'"
    >
      <div class="flex items-center justify-between border-b px-5 py-3">
        <h2 class="font-semibold text-slate-800">{{ title }}</h2>
        <button class="text-slate-400 hover:text-slate-700" @click="emit('close')">✕</button>
      </div>
      <div class="p-5">
        <slot />
      </div>
    </div>
  </div>
</template>
