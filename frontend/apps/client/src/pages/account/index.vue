<script setup lang="ts">
import { ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import AccountPage from './AccountPage.vue'
import { destination, go, type Query } from '../../shared/navigation'

const query = ref<Query>()
onLoad((value) => {
  if (value?.view === 'login') {
    const { view: _view, bind, ...redirect } = value
    query.value = {}
    go(bind === 'email' ? destination('security', 'email') : destination('login', undefined, redirect), 'replace')
    return
  }
  query.value = value || {}
})
</script>

<template>
  <AccountPage v-if="query" :query="query" />
</template>
