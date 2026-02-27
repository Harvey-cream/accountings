const API_URL = 'http://192.168.110.134:8030';
// 发送放行接口 (不拦截)
export const sendReleaseRequest = async (url, method = 'GET', data = {}) => {
	let defaultHeaders = {
		'content-type': 'application/json'
	}
	return new Promise((resolve, reject) => {
		uni.request({
			url: API_URL + url,
			method,
			data,
			header: defaultHeaders,
			success(res) {
				if (res.statusCode === 200) {
					resolve(res.data)
				} else {
					uni.showToast({ title: res.data.message || '请求失败', icon: 'none' });
					reject(res.data)
				}
			},
			fail(err) {
				uni.showToast({ title: '网络错误', icon: 'none' });
				reject(err)
			}
		})
	})
}

// 普通请求接口 (带拦截/Token/过期自动刷新)
export const sendRequest = async (url, method = 'GET', data = {}) => {
	let defaultHeaders = {
		'content-type': 'application/json'
	}
	
	// 1. 从统一的 session 对象中获取登录信息
	const session = uni.getStorageSync('session');
	let token = session?.token_info?.token;
	
	if (!token) {
		uni.showModal({
			title: '提示',
			content: '您尚未登录，请先登录后再进行操作',
			showCancel: false,
			confirmText: '去登录',
			success: (res) => {
				if (res.confirm) {
					uni.reLaunch({ url: '/pages/login/login' });
				}
			}
		});
		return Promise.reject('未登录');
	}

	// 2. Token 过期预检：如果距离过期不足 30 秒，直接先去刷新
	const expires = session?.token_info?.expires;
	const now = Date.now();
	
	if (expires && expires - now < 30000) { // 30秒 = 30000毫秒
		try {
			token = await refreshToken();
		} catch (err) {
			uni.reLaunch({ url: '/pages/login/login' });
			return Promise.reject('Token 刷新失败');
		}
	}
	
	// 3. 正常发起请求
	defaultHeaders['Authorization'] = 'Bearer ' + token;
	const userId = session?.user_info?.userId;
	if (userId) {
		defaultHeaders['X-User-ID'] = userId;
	}

	return new Promise((resolve, reject) => {
		uni.request({
			url: API_URL + url,
			method,
			data,
			header: defaultHeaders,
			success(res) {
				if (res.statusCode === 200) {
					resolve(res.data)
				} else if (res.statusCode === 401) {
					// 4. 如果还是返回 401，说明 Access Token 彻底失效，尝试刷新一次并重试
					refreshToken().then(newToken => {
						// 刷新成功，递归重试本次请求
						resolve(sendRequest(url, method, data));
					}).catch(() => {
						// 刷新也失败，只能去登录了
						uni.reLaunch({ url: '/pages/login/login' });
						reject('登录失效');
					});
				} else {
					uni.showToast({ title: res.data.message || '请求失败', icon: 'none' });
					reject(res.data)
				}
			},
			fail(err) {
				uni.showToast({ title: '网络错误', icon: 'none' });
				reject(err)
			}
		})
	})
}
// 刷新 Token 的具体逻辑
const refreshToken = () => {
	const session = uni.getStorageSync('session');
	const refresh = session?.token_info?.refresh;
	if (!refresh) return Promise.reject('无刷新令牌');
	
	return new Promise((resolve, reject) => {
		uni.request({
			url: API_URL + '/api/user/refresh_token/',
			method: 'POST',
			data: { refresh_token: refresh }, // 接口参数名保持不变
			success(res) {
				if (res.statusCode === 200 && res.data.code === 200) {
					// 更新 session 中的 token_info (后端返回的是完整的 token_info 对象)
					session.token_info = res.data.token_info;
					uni.setStorageSync('session', session);
					resolve(res.data.token_info.token);
				} else {
					// 刷新彻底失败，清除登录状态
					uni.removeStorageSync('session');
					reject(res.data.message || '刷新失败');
				}
			},
			fail(err) {
				reject(err);
			}
		});
	});
}
