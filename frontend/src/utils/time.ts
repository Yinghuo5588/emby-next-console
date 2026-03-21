export function fromNow(iso: string): string {
 const diff = Date.now() - new Date(iso).getTime()
 const m = Math.floor(diff / 60000)
 if (m < 1) return '刚刚'
 if (m < 60) return `${m} 分钟前`
 const h = Math.floor(m / 60)
 if (h < 24) return `${h} 小时前`
 const d = Math.floor(h / 24)
 return `${d} 天前`
}

export function formatDate(iso: string): string {
 const d = new Date(iso)
 return d.toLocaleDateString('zh-CN', {
 year: 'numeric',
 month: '2-digit',
 day: '2-digit',
 })
}

export function formatDateTime(iso: string): string {
 return new Date(iso).toLocaleString('zh-CN', {
 month: '2-digit',
 day: '2-digit',
 hour: '2-digit',
 minute: '2-digit',
 })
}

export function formatDuration(sec: number): string {
 if (sec < 60) return `${sec}秒`
 const h = Math.floor(sec / 3600)
 const m = Math.floor((sec % 3600) / 60)
 return h > 0 ? `${h}小时 ${m}分钟` : `${m}分钟`
}

export function formatNumber(n: number): string {
 if (n >= 10000) {
 return (n / 10000).toFixed(1).replace(/\.0$/, '') + '万'
 }
 return String(n)
}

export function isExpiringSoon(expireAt: string | null | undefined): boolean {
 if (!expireAt) return false
 const ms = new Date(expireAt).getTime() - Date.now()
 return ms > 0 && ms < 30 * 24 * 60 * 60 * 1000 // 30天内到期
}