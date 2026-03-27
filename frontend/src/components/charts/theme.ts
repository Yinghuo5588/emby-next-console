export const chartColors = ['#007AFF', '#34C759', '#FF9500', '#AF52DE', '#5AC8FA', '#FF2D55', '#FFD60A', '#64D2FF']

export function chartTextStyle(isDark: boolean) {
  return { color: isDark ? '#fff' : '#000', fontSize: 13, fontFamily: "-apple-system, BlinkMacSystemFont, 'SF Pro Text', 'PingFang SC', sans-serif" }
}

export function chartMutedStyle() {
  return { color: '#8e8e93', fontSize: 11 }
}

export function chartTooltipStyle(isDark: boolean) {
  return {
    backgroundColor: isDark ? 'rgba(44,44,46,0.95)' : 'rgba(255,255,255,0.95)',
    borderColor: isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.06)',
    textStyle: { ...chartTextStyle(isDark) },
  }
}

export function chartGridStyle() {
  return { left: 40, right: 12, top: 16, bottom: 8 }
}

export function chartSplitLineStyle(isDark: boolean) {
  return { color: isDark ? '#2c2c2e' : '#f2f2f7', type: 'dashed' as const }
}

export function chartAxisLineStyle(isDark: boolean) {
  return { color: isDark ? '#48484a' : '#e5e5ea' }
}
