<script setup lang="ts">
import { onMounted } from "vue";

import { useAuthStore } from "@/stores/auth";

const auth = useAuthStore();

// Rehydrate the current user on a hard refresh if a token is present.
onMounted(() => {
  if (auth.isAuthenticated && !auth.user) {
    auth.fetchMe().catch(() => auth.logout());
  }
});
</script>

<template>
  <RouterView />
</template>
