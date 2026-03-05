import { defineStore } from 'pinia';

export const useUserStore = defineStore('user', {
	state: () => ({
		userInfo: uni.getStorageSync('session')?.user_info || null,
		tokenInfo: uni.getStorageSync('session')?.token_info || null,
	}),
	
	getters: {
		isLoggedIn: (state) => !!state.tokenInfo?.token,
		getToken: (state) => state.tokenInfo?.token || '',
	},
	
	actions: {
		setLoginInfo(data) {
			this.tokenInfo = data.token_info;
			this.userInfo = data.user_info;
			
			// 统一存储到 session 缓存中
			uni.setStorageSync('session', {
				token_info: data.token_info,
				user_info: data.user_info
			});
		},
		logout() {
			this.tokenInfo = null;
			this.userInfo = null;
			
			// 清除统一的 session 缓存
			uni.removeStorageSync('session');
			
			uni.showToast({
				title: '已退出登录',
				icon: 'success'
			});
			
			setTimeout(() => {
				uni.reLaunch({
					url: '/pages/login/login'
				});
			}, 800);
		}
	}
});
