<script setup lang="ts">
defineProps<{ name: 'bazi' | 'dream' | 'tarot' | 'liuyao' }>()
</script>

<template>
  <span class="motif" :class="'motif--' + name" aria-hidden="true">
    <span v-if="name === 'bazi'" class="taiji"></span>
    <span v-else-if="name === 'dream'" class="moon"><i></i></span>
    <span v-else-if="name === 'tarot'" class="motif-cards"><i></i><b>✧</b></span>
    <span v-else class="motif-yao"
      ><i v-for="n in 6" :key="n" :class="{ broken: n === 2 || n === 5 }"></i
    ></span>
  </span>
</template>

<style scoped>
.motif {
  display: grid;
  place-items: center;
  width: 69px;
  height: 75px;
  color: var(--gold);
  flex: 0 0 auto;
}
.taiji {
  width: 53px;
  aspect-ratio: 1;
  border: 1.5px solid currentColor;
  border-radius: 50%;
  transform: rotate(-20deg);
  background:
    radial-gradient(circle at 50% 25%, currentColor 0 11%, var(--panel) 12% 25%, transparent 26%),
    radial-gradient(circle at 50% 75%, var(--panel) 0 11%, currentColor 12% 25%, transparent 26%),
    linear-gradient(90deg, var(--panel) 50%, currentColor 50%);
}
.moon {
  position: relative;
  width: 47px;
  aspect-ratio: 1;
  border: 1.5px solid currentColor;
  border-radius: 50%;
  border-right-color: transparent;
  border-top-color: transparent;
  transform: rotate(24deg);
  box-shadow: inset 5px -3px 0 -2px currentColor;
}
.moon::before {
  content: '✧';
  font-size: 17px;
  position: absolute;
  top: -5px;
  right: 0;
}
.moon::after {
  content: '✦';
  font-size: 9px;
  position: absolute;
  top: 8px;
  right: 12px;
}
.motif-cards {
  position: relative;
  width: 62px;
  height: 57px;
}
.motif-cards i,
.motif-cards b {
  position: absolute;
  display: grid;
  place-items: center;
  top: 4px;
  width: 35px;
  height: 49px;
  border: 1.5px solid currentColor;
  border-radius: 4px;
  background: var(--panel);
}
.motif-cards i {
  left: 19px;
  transform: rotate(16deg);
  opacity: 0.65;
}
.motif-cards b {
  left: 7px;
  transform: rotate(-12deg);
  font: 26px/1 var(--serif);
}
.motif-yao {
  display: grid;
  align-content: center;
  gap: 5px;
  width: 46px;
}
.motif-yao i {
  width: 100%;
  height: 2px;
  border-radius: 1px;
  background: currentColor;
}
.motif-yao .broken {
  background: linear-gradient(to right, currentColor 42%, transparent 42% 58%, currentColor 58%);
}
@media (max-width: 700px) {
  .motif {
    width: 43px;
    height: 49px;
  }
  .taiji {
    width: 36px;
  }
  .moon {
    width: 34px;
  }
  .motif-cards {
    transform: scale(0.72);
  }
  .motif-yao {
    width: 34px;
    gap: 4px;
  }
}
</style>
