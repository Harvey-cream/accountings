/**
 * 路由拦截工具 (Trigger A & Trigger B)
 */

// 无需登录的页面白名单
const ignore_urls = [
	'/pages/login/login',
	'/pages/login/register',
	'/pages/login/forget_password'
]

/**
 * 触发点 A：全局导航 Hook (针对 App 内跳转)
 * 劫持跳转方法，在“动作发生前”检查 sessionInfo
 */
const interceptor = {
	invoke(args) {
		const sessionInfo = uni.getStorageSync('session');
		const token = sessionInfo?.token_info?.token;
		
		// 提取路径部分
		const pathOnly = args.url.split('?')[0];
		
		// 命中白名单直接放行
		if (ignore_urls.includes(pathOnly)) {
			return args;
		}
		if (!token) {
			uni.showModal({
				title: '提示',
				content: '您尚未登录，请先登录后再进行操作',
				showCancel: false,
				confirmText: '去登录',
				success: (res) => {
					if (res.confirm) {
						uni.reLaunch({
							url: '/pages/login/login'
						});
					}
				}
			});
			return false; // 拦截并停止跳转
		}
		return args;
	}
};

/**
 * 初始化路由拦截器 (在 App.vue 调用)
 */
export const initRouterInterceptor = () => {
	const navMethods = ['navigateTo', 'redirectTo', 'reLaunch', 'switchTab'];
	navMethods.forEach(method => {
		uni.addInterceptor(method, interceptor);
	});
};

/**
 * 触发点 B：应用启动自检 (onLaunch) & 页面自检 (Mixin)
 * 针对直接输入 URL 或刷新网页的情况，在页面加载出的瞬间进行拦截
 */
export const checkInitialPath = (currentPath) => {
	const sessionInfo = uni.getStorageSync('session');
	const token = sessionInfo?.token_info?.token;
	
	// 统一处理路径格式
	let cleanPath = currentPath.split('?')[0];
	if (cleanPath.startsWith('#')) cleanPath = cleanPath.substring(1);
	if (!cleanPath.startsWith('/')) cleanPath = '/' + cleanPath;
	
	const isWhiteList = ignore_urls.some(path => cleanPath === path);
	
	if (!token && !isWhiteList) {
		console.log('--- Access Intercepted (Trigger B) ---', cleanPath);
		uni.showModal({
			title: '提示',
			content: '您尚未登录，请先登录后再进行操作',
			showCancel: false,
			confirmText: '去登录',
			success: (res) => {
				if (res.confirm) {
					uni.reLaunch({
						url: '/pages/login/login'
					});
				}
			}
		});
		return false;
	}
	return true;
};

export const authMixin = {
	onShow() {
		const pages = getCurrentPages();
		if (pages.length === 0) return;
		const route = pages[pages.length - 1].route;
		checkInitialPath('/' + route);
	}
};

export default {
	initRouterInterceptor,
	checkInitialPath,
	authMixin
}
