const API_URL = 'http://127.0.0.1:8030';

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

// 普通请求接口 (带拦截/Token)
export const sendRequest = async (url, method = 'GET', data = {}) => {
	let defaultHeaders = {
		'content-type': 'application/json'
	}
	
	// 拦截逻辑：检查登录状态
	const userId = uni.getStorageSync('userId');
	if (!userId) {
		uni.navigateTo({ url: '/pages/login/login' });
		return Promise.reject('未登录');
	}
	
	defaultHeaders['X-User-ID'] = userId;

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
					uni.navigateTo({ url: '/pages/login/login' });
					reject('登录失效');
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
