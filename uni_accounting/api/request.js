// 环境判断逻辑
let API_URL = '';

if (process.env.NODE_ENV === 'development') {
    // 开发环境后端地址
    // API_URL = 'http://192.168.146.1:8030'; 
    API_URL = 'http://172.20.10.3:8030'; // 手机热点/局域网访问地址
} else {
    // 生产环境部署地址
    API_URL = 'http://47.107.238.136:8011'; 
}

// 请求锁：存储正在进行中的请求，防止重复点击
const pendingReqs = new Set()
// 忽略拦截的接口白名单 (比如获取某些不敏感数据)
const ignoreReqs = ['/api/public/some_data'] 

// 发送放行接口 (不拦截)
export const sendReleaseRequest = async (url, method = 'GET', data = {}) => {
	let defaultHeaders = {
		'content-type': 'application/json'
	}
	const requestKey = `release:${method}:${url}:${JSON.stringify(data)}`
	if (pendingReqs.has(requestKey)) {
		console.log("操作过快，请勿频繁操作：", url)
		return Promise.reject("操作过快，请勿频繁操作")
	}
	pendingReqs.add(requestKey)

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
					uni.showToast({
						title: res.data.msg || '请求失败',
						icon: 'none'
					});
					reject(res.data)
				}
			},
			fail(err) {
				uni.showToast({
					title: '网络错误',
					icon: 'none'
				});
				reject(err)
			},
			complete() {
				pendingReqs.delete(requestKey)
			}
		})
	})
}

// 普通请求接口 (带拦截/Token/过期自动刷新)
export const sendRequest = async (url, method = 'GET', data = {}) => {
	let defaultHeaders = {
		'content-type': 'application/json'
	}
	// 0. 请求锁：防止用户重复点击
	const requestKey = `req:${method}:${url}:${JSON.stringify(data)}`
	if (pendingReqs.has(requestKey) && !ignoreReqs.includes(url)) {
		console.log("操作过快，请勿频繁操作：", url)
		return Promise.reject("操作过快，请勿频繁操作")
	}
	pendingReqs.add(requestKey)

	// 1. 从统一的 session 对象中获取登录信息
	const sessionInfo = uni.getStorageSync('session');
	let token = sessionInfo?.token_info?.token;

	if (!token) {
		pendingReqs.delete(requestKey) 
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
		return Promise.reject('未登录');
	}

	// 2. Token 过期预检：如果距离过期不足 30 秒，直接先去刷新
	const expires = sessionInfo?.token_info?.expires;
	const now = Date.now();

	if (expires && expires - now < 30000) { // 30秒 = 30000毫秒
		try {
			token = await refreshToken();
		} catch (err) {
			pendingReqs.delete(requestKey)
			uni.reLaunch({
				url: '/pages/login/login'
			});
			return Promise.reject('Token 刷新失败');
		}
	}

	// 3. 正常发起请求
	defaultHeaders['Authorization'] = 'Bearer ' + token;
	const userId = sessionInfo?.user_info?.userId;
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
						// 注意：这里的重试由于是调用 sendRequest，内部会再次生成 key 并检查锁
						// 所以在递归调用前，必须先删除当前 key
						pendingReqs.delete(requestKey)
						resolve(sendRequest(url, method, data));
					}).catch(() => {
						// 刷新也失败，只能去登录了
						uni.reLaunch({
							url: '/pages/login/login'
						});
						reject('登录失效');
					});
				} else {
					uni.showToast({
						title: res.data.msg || '请求失败',
						icon: 'none'
					});
					reject(res.data)
				}
			},
			fail(err) {
				uni.showToast({
					title: '网络错误',
					icon: 'none'
				});
				reject(err)
			},
			complete() {
				pendingReqs.delete(requestKey)
			}
		})
	})
}
// 刷新 Token 的具体逻辑
const refreshToken = () => {
	const sessionInfo = uni.getStorageSync('session');
	const refresh = sessionInfo?.token_info?.refresh;
	if (!refresh) return Promise.reject('无刷新令牌');

	return new Promise((resolve, reject) => {
		uni.request({
			url: API_URL + '/api/user/refresh_token/',
			method: 'POST',
			data: {
				refresh_token: refresh
			}, // 接口参数名保持不变
			success(res) {
				if (res.statusCode === 200 && res.data.code === 0) {
					// 更新 session 中的 token_info (后端返回的是完整的 token_info 对象)
					sessionInfo.token_info = res.data.data;
					uni.setStorageSync('session', sessionInfo);
					resolve(res.data.data.token);
				} else {
					// 刷新彻底失败，清除登录状态
					uni.removeStorageSync('session');
					reject(res.data.msg || '刷新失败');
				}
			},
			fail(err) {
				reject(err);
			}
		});
	});
}