<script setup lang="ts">
import type { BaziReading } from './chart'

defineProps<{ reading: BaziReading }>()
</script>

<template>
  <section class="panel stack">
    <h2>四柱明细</h2>
    <div class="data-table">
      <table>
        <thead>
          <tr>
            <th>柱位</th>
            <th>干支</th>
            <th>五行</th>
            <th>藏干</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="pillar in reading.pillars" :key="pillar.label">
            <th scope="row">{{ pillar.label }}</th>
            <td class="letter-value">{{ pillar.text }}</td>
            <td>{{ pillar.elements }}</td>
            <td>{{ pillar.hidden }}</td>
          </tr>
        </tbody>
      </table>
    </div>
    <p class="status-label">
      {{ reading.calendar }} · 公历 {{ reading.solarDate }} ·
      {{ reading.lateZi ? '晚子时按次日换日' : '以零点换日' }}
    </p>
  </section>
</template>

<style scoped>
.data-table {
  overflow-x: auto;
}
table {
  width: 100%;
  border-collapse: collapse;
}
th,
td {
  border-bottom: 1px solid var(--line);
  padding: 10px 8px;
  text-align: left;
}
tbody tr:last-child td {
  border-bottom: 0;
}
td.letter-value {
  color: var(--gold);
  font: 600 clamp(1.1rem, 3vw, 1.6rem) / 1.2 var(--serif);
}
</style>
