<template>
  <span class="brand-seal" aria-hidden="true">
    <span v-for="corner in 4" :key="corner"><i></i><b></b></span>
  </span>
</template>

<style scoped>
.brand-seal {
  position: relative;
  display: inline-grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 2px;
  flex: none;
  width: 42px;
  height: 42px;
  padding: 7px;
  border: 1.5px solid currentColor;
  border-radius: 50%;
}
.brand-seal > span {
  display: block;
  position: relative;
  border: 1px solid currentColor;
  border-radius: 8px 1px 1px 1px;
}
.brand-seal > span:nth-child(2) {
  transform: rotate(90deg);
}
.brand-seal > span:nth-child(3) {
  transform: rotate(-90deg);
}
.brand-seal > span:nth-child(4) {
  transform: rotate(180deg);
}
.brand-seal i,
.brand-seal b {
  display: block;
  position: absolute;
  left: 2px;
  right: 2px;
  height: 1px;
  background: currentColor;
}
.brand-seal i {
  top: 36%;
}
.brand-seal b {
  top: 65%;
}
@media (max-width: 700px) {
  .brand-seal {
    width: 29px;
    height: 29px;
    padding: 4px;
    gap: 1px;
  }
}
</style>
