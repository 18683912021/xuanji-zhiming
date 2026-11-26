<script setup lang="ts">
defineProps<{ headings: string[]; rows: (string | number)[][] }>()
defineOptions({ options: { virtualHost: true } })
</script>
<template>
  <scroll-view class="table-scroll" scroll-x>
    <view class="table-row table-header"
      ><text v-for="(column, index) in headings" :key="index" class="table-cell gold">{{
        column
      }}</text></view
    >
    <view v-for="(row, index) in rows" :key="index" class="table-row"
      ><text v-for="(cell, column) in row" :key="column" class="table-cell">{{ cell }}</text></view
    >
  </scroll-view>
</template>
