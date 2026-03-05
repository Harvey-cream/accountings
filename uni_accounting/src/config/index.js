export const APP_TITLE = "记账家"
// export const APPID = "wxddde2ee84641ac77" // 暂时沿用您的示例 ID
export const ACCOUNT = "168168"

// 接口地址配置
const FORCE_DEV = (typeof import.meta !== 'undefined' && import.meta.env && import.meta.env.VITE_FORCE_DEV) === 'true'
const IS_DEVELOPMENT = (typeof import.meta !== 'undefined' && import.meta.env && import.meta.env.DEV) === true

// 统一 API 地址
// 开发环境下连接本地局域网 IP，生产环境下连接云服务器 IP
export const API_URL = (FORCE_DEV || IS_DEVELOPMENT) 
	? "http://192.168.146.1:8030" 
	// ? "http://192.168.110.134:8030" 
	: "http://47.107.238.136:8011"

// 如果未来需要 WebSocket，也可以在这里预留
export const WS_URL = (FORCE_DEV || IS_DEVELOPMENT)
	? "ws://192.168.110.134:8030"
	: "ws://47.107.238.136:8011"
