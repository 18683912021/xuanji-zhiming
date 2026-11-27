<script setup lang="ts">
import { onLaunch } from '@dcloudio/uni-app'
import { restoreIdentity } from './shared/api'
import { refreshReadings } from './features/divination/records'
import { refreshPersonal } from './features/account/state'
import { refreshZodiac } from './features/catalog/remote'
import { refreshReports } from './features/ai/reports'
import { refreshConversations } from './features/ai/remote'

onLaunch(async () => {
  void refreshZodiac().catch(() => undefined)
  await restoreIdentity()
  await Promise.allSettled([refreshReadings(), refreshPersonal()])
  void Promise.allSettled([refreshConversations(), refreshReports()])
})
</script>

<style>
@import '@xuanji/theme/tokens.css';
@import './styles/base.css';
</style>
