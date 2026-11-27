import { onHide, onShow } from '@dcloudio/uni-app'
import { ref } from 'vue'

export function usePageMotion() {
  const entering = ref(true)
  onHide(() => { entering.value = false })
  onShow(() => { entering.value = true })
  return entering
}
