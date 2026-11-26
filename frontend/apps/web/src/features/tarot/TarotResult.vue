<script setup lang="ts">
import { cards, type DrawnCard } from './tarot'

defineProps<{ reading: DrawnCard[] }>()
</script>

<template>
  <section class="panel cards-stage">
    <h2>本次牌阵</h2>
    <div class="reading-cards">
      <figure v-for="card in reading" :key="card.index" class="reading-card">
        <small>{{ card.position }}</small>
        <div class="reading-face" aria-hidden="true">
          <em :style="{ transform: card.reversed ? 'rotate(180deg)' : undefined }">✧</em>
        </div>
        <figcaption>
          <strong>{{ cards[card.index]?.[0] }}</strong
          ><small> · {{ card.reversed ? '逆位' : '正位' }}</small>
        </figcaption>
      </figure>
    </div>
  </section>
  <section class="panel">
    <h2>逐张看牌义</h2>
    <div class="stack">
      <div v-for="card in reading" :key="card.index">
        <h3>
          {{ card.position }} · {{ cards[card.index]?.[0] }}{{ card.reversed ? '逆位' : '正位' }}
        </h3>
        <p class="muted">{{ cards[card.index]?.[card.reversed ? 2 : 1] }}</p>
      </div>
      <p class="status-label">来源 · 玄机知命牌义图鉴</p>
    </div>
  </section>
</template>

<style scoped src="./tarot.css"></style>
