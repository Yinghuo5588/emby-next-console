import { ref, watch, type Ref } from 'vue'

export function useCountUp(target: Ref<number | undefined>, duration = 600) {
  const display = ref(0)

  function easeOutCubic(t: number): number {
    return 1 - Math.pow(1 - t, 3)
  }

  watch(target, (to) => {
    if (to === undefined || to === null) return
    const start = display.value
    const diff = to - start
    if (diff === 0) return

    const startTime = performance.now()

    function tick(now: number) {
      const elapsed = now - startTime
      const progress = Math.min(elapsed / duration, 1)
      display.value = Math.round(start + diff * easeOutCubic(progress))
      if (progress < 1) requestAnimationFrame(tick)
    }

    requestAnimationFrame(tick)
  }, { immediate: true })

  return display
}
