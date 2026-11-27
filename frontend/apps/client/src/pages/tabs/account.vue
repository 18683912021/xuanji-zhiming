<script setup lang="ts">
import AccountPage from '../account/AccountPage.vue'
import { usePageMotion } from '../../shared/pageMotion'

const entering = usePageMotion()
</script>

<template>
  <AccountPage :entering="entering" />
</template>
