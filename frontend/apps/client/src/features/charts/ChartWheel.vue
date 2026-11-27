<script setup lang="ts">
import { signs } from '../catalog/zodiac'
import { chartFixture } from './fixtures'

defineProps<{
  data: ReturnType<typeof chartFixture>
  second?: ReturnType<typeof chartFixture>
  title: string
  cusps?: number[]
}>()
function point(degree: number, radius: number) {
  const angle = ((degree - 90) * Math.PI) / 180
  return { left: 50 + radius * Math.cos(angle) + '%', top: 50 + radius * Math.sin(angle) + '%' }
}
defineOptions({ options: { virtualHost: true } })
</script>

<template>
  <view class="wheel" :aria-label="cusps ? '本命星盘' : '星盘示例图'">
    <view class="ring rim"></view>
    <view class="ring middle"></view>
    <view class="ring inner"></view>
    <view
      v-for="tick in 36"
      :key="'tick-' + tick"
      class="rim-tick"
      :style="{ transform: 'rotate(' + tick * 10 + 'deg)' }"
    ></view>
    <view v-for="degree in (cusps || Array.from({ length: 12 }, (_, index) => index * 30))" :key="degree" class="spoke" :style="{ transform: 'rotate(' + degree + 'deg)' }"></view>
    <text v-for="(sign, index) in signs" :key="sign.id" class="wheel-sign" :style="point(index * 30 + 15, 44)">{{
      sign.glyph
    }}</text>
    <text
      v-for="planet in data.slice(0, 10)"
      :key="planet.planet"
      class="wheel-point"
      :style="point(planet.degree, 32)"
      >{{ planet.planet.slice(0, 1) }}</text
    >
    <text
      v-for="planet in second?.slice(0, 10)"
      :key="planet.planet"
      class="wheel-point second"
      :style="point(planet.degree, 23)"
      >{{ planet.planet.slice(0, 1) }}</text
    >
    <text class="wheel-title">{{ title }}</text>
  </view>
</template>

<style scoped>
.wheel {
  margin: 12px auto;
  position: relative;
  width: 100%;
  max-width: 365px;
  aspect-ratio: 1;
  border: 1px solid #bb956c;
  border-radius: 50%;
  background:
    radial-gradient(ellipse at 34% 24%, #69466e67, #21152f00 61%),
    radial-gradient(circle, #352247, #1e122b 75%);
  box-shadow:
    inset 0 0 22px #0e091d85,
    0 10px 26px #09051268;
  overflow: hidden;
}
.ring {
  position: absolute;
  border: 1px solid #68516f;
  border-radius: 50%;
}
.rim {
  inset: 2.4%;
  border-color: #caa56c82;
}
.middle {
  inset: 13%;
  border-color: #ad8b666d;
}
.rim-tick {
  position: absolute;
  left: 50%;
  top: 0;
  width: 1px;
  height: 50%;
  transform-origin: center bottom;
  background: linear-gradient(#d8ad795e 0 7%, transparent 7%);
  pointer-events: none;
}
.inner {
  inset: 25%;
}
.spoke {
  height: 50%;
  width: 1px;
  position: absolute;
  left: 50%;
  top: 0;
  background: linear-gradient(#caa56c66 25%, #886b6a82 48%, transparent 75%);
  transform-origin: center bottom;
}
.wheel-sign,
.wheel-point {
  position: absolute;
  transform: translate(-50%, -50%);
}
.wheel-sign {
  color: #d9b989;
  font-size: 20px;
}
.wheel-point {
  background: #2d1b39;
  border-radius: 50%;
  width: 21px;
  height: 21px;
  line-height: 21px;
  font-size: 10px;
  color: #f0d9a0;
  text-align: center;
  border: 1px solid #a38b61;
}
.wheel-point.second {
  color: #e3d7f1;
  border-color: #8c6fa5;
}
.wheel-title {
  position: absolute;
  left: 50%;
  top: 50%;
  width: 40%;
  transform: translate(-50%, -50%);
  color: var(--mist);
  text-align: center;
  font: 700 17px var(--serif);
}
</style>
