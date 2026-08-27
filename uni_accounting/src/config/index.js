export const APP_TITLE = "小龙社交记账"
// export const APPID = "wxddde2ee84641ac77" // 
export const ACCOUNT = "168168"

// 接口地址配置
const FORCE_DEV = (typeof import.meta !== 'undefined' && import.meta.env && import.meta.env.VITE_FORCE_DEV) === 'true'
const IS_DEVELOPMENT = (typeof import.meta !== 'undefined' && import.meta.env && import.meta.env.DEV) === true
// 是否使用国内 IP 服务器环境 (47.107.238.136)
const IS_CN_SERVER = (typeof import.meta !== 'undefined' && import.meta.env && import.meta.env.VITE_CN_SERVER) === 'true'

// 统一 API 地址
// 开发环境走 Vite 同源代理（见 vite.config.js）；生产按标记连国内 IP 或域名
export const API_URL = (FORCE_DEV || IS_DEVELOPMENT)
	? ""
	: (IS_CN_SERVER ? "http://47.107.238.136:8011" : "https://draccounting.xin")

// 如果未来需要 WebSocket，也可以在这里预留
export const WS_URL = (FORCE_DEV || IS_DEVELOPMENT) 
	? "http://127.0.0.1:8030" 
	: (IS_CN_SERVER ? "ws://47.107.238.136:8011" : "wss://draccounting.xin")
