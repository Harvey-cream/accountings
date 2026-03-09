<template>
	<view class="login-container" :class="currentThemeClass">
		<!-- 顶部背景装饰 -->
		<view class="top-bg">
			<view class="welcome-box">
				<text class="title-hi">您好，</text>
				<text class="title-welcome">欢迎使用小龙社交记账</text>
			</view>
		</view>

		<!-- 登录卡片 -->
		<view class="login-card">
			<view class="login-type-hint">使用手机号密码登录</view>

			<!-- 输入区域 -->
			<view class="input-group">
				<view class="input-item">
					<input type="number" v-model="mobile" placeholder="请输入手机号" maxlength="11" />
				</view>

				<view class="input-item">
					<input :type="showPassword ? 'text' : 'password'" v-model="password" placeholder="请输入密码" />
					<van-icon :name="showPassword ? 'eye-o' : 'closed-eye'" size="20" color="#cbd5e1" @click="showPassword = !showPassword" />
				</view>
			</view>

			<!-- 协议勾选 -->
			<view class="agreement-row">
				<view class="check-box" @click="agreed = !agreed">
					<van-icon :name="agreed ? 'checked' : 'circle'" :color="agreed ? 'var(--main-color)' : '#cbd5e1'" size="18" />
				</view>
				<view class="agreement-text">
					已阅读并同意
					<text class="link">《用户协议》</text>
					和
					<text class="link">《隐私协议》</text>
				</view>
			</view>

			<!-- 登录按钮 -->
			<button class="login-btn" @click="handleLogin">登录</button>

			<!-- 底部链接 -->
			<view class="bottom-links">
				<text class="link-item" @click="goToForgetPassword">找回密码</text>
				<text class="divider">|</text>
				<text class="link-item" @click="goToRegister">注册账号</text>
			</view>

			<!-- 第三方登录 -->
			<view class="other-login-section">
				<view class="other-login-title">
					<view class="line"></view>
					<text>其它方式登录</text>
					<view class="line"></view>
				</view>
				<view class="other-login-icons">
					<view class="icon-btn">
						<van-icon name="wechat" color="#07c160" size="28" />
					</view>
					<view class="icon-btn">
						<van-icon name="alipay" color="#1677ff" size="28" />
					</view>
				</view>
			</view>
		</view>
	</view>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { onLoad } from '@dcloudio/uni-app';
import { login } from '../../api/api.js';
import { SM2Utils, BACK_PUBLIC_KEY } from '../../utils/sm2.js';
import { useUserStore } from '../../store/user.js';

const userStore = useUserStore();
const mobile = ref('');
const password = ref('');
const agreed = ref(true);
const showPassword = ref(false);
const referCode = ref('');

onLoad((options) => {
	if (options.refer_code) {
		referCode.value = options.refer_code;
		console.log('检测到推荐码:', referCode.value);
	}
});

onMounted(() => {
	// 如果已经登录且 session 有效，直接跳转首页
	const session = uni.getStorageSync('session');
	if (session && session.token_info && session.token_info.token) {
		uni.reLaunch({ url: '/pages/home/accounting_detail' });
	}
});

const goToRegister = () => {
	uni.navigateTo({
		url: `/pages/login/register${referCode.value ? '?refer_code=' + referCode.value : ''}`
	});
};

const goToForgetPassword = () => {
	uni.navigateTo({
		url: '/pages/login/forget_password'
	});
};

const handleLogin = async () => {
	if (!agreed.value) {
		uni.showToast({ title: '请先同意用户协议', icon: 'none' });
		return;
	}
	if (!mobile.value || !password.value) {
		uni.showToast({ title: '请输入手机号和密码', icon: 'none' });
		return;
	}
	if (!/^1[3-9]\d{9}$/.test(mobile.value)) {
		uni.showToast({ title: '请输入正确的手机号码', icon: 'none' });
		return;
	}
	
	uni.showLoading({ title: '登录中...', mask: true });
	try {
		const res = await login({
			mobile: mobile.value,
			password: SM2Utils.encrypt(password.value, BACK_PUBLIC_KEY)
		});
		
		uni.hideLoading();
		
		if (res.code === 0) {
			uni.showToast({ title: '登录成功', icon: 'success' });
			
			// 使用 store 统一管理登录信息(包括 token 和用户信息)
			userStore.setLoginInfo(res.data);
			
			setTimeout(() => {
				uni.reLaunch({ url: '/pages/home/accounting_detail' });
			}, 1000);
		} else {
			uni.showToast({ title: res.msg || '登录失败', icon: 'none' });
		}
	} catch (err) {
		uni.hideLoading();
		console.error('登录失败:', err);
	}
};
</script>

<style scoped>
.login-container {
	min-height: 100vh;
	background-color: #ffffff;
	display: flex;
	flex-direction: column;
}

.top-bg {
	height: 20vh;
	background: linear-gradient(180deg, rgba(255, 213, 65, 0.4) 0%, rgba(255, 255, 255, 0) 100%);
	padding: 20px 30px 0;
}

.welcome-box {
	display: flex;
	flex-direction: column;
	gap: 8px;
}

.title-hi {
	font-size: 32px;
	font-weight: bold;
	color: #1e293b;
}

.title-welcome {
	font-size: 18px;
	color: #64748b;
	font-weight: 500;
}

.login-card {
	padding: 0 30px 40px;
	flex: 1;
	display: flex;
	flex-direction: column;
}

.login-type-hint {
	font-size: 14px;
	color: #94a3b8;
	margin-bottom: 20px;
}

.input-group {
	display: flex;
	flex-direction: column;
	gap: 20px;
}

.input-item {
	background-color: #f8fafc;
	border-radius: 12px;
	height: 56px;
	display: flex;
	align-items: center;
	padding: 0 20px;
}

.input-item input {
	flex: 1;
	font-size: 15px;
	height: 100%;
}

.agreement-row {
	margin-top: 24px;
	display: flex;
	align-items: center;
	gap: 8px;
}

.agreement-text {
	font-size: 13px;
	color: #94a3b8;
}

.link {
	color: #94a3b8;
}

.login-btn {
	margin-top: 24px;
	width: 100%;
	height: 50px;
	background-color: var(--main-color);
	color: #1e293b;
	border-radius: 12px;
	font-size: 16px;
	font-weight: bold;
	display: flex;
	align-items: center;
	justify-content: center;
	border: none;
}

.login-btn:active {
	opacity: 0.9;
}

.bottom-links {
	margin-top: 24px;
	display: flex;
	justify-content: center;
	align-items: center;
	gap: 15px;
}

.link-item {
	font-size: 14px;
	color: #94a3b8;
}

.divider {
	color: #f1f5f9;
}

/* 第三方登录 */
.other-login-section {
	margin-top: auto;
}

.other-login-title {
	display: flex;
	align-items: center;
	justify-content: center;
	gap: 10px;
	margin-bottom: 20px;
}

.other-login-title text {
	font-size: 13px;
	color: #cbd5e1;
}

.other-login-title .line {
	flex: 1;
	height: 1px;
	background-color: #f1f5f9;
}

.other-login-icons {
	display: flex;
	justify-content: center;
	gap: 40px;
}

.icon-btn {
	width: 100px;
	height: 50px;
	border: 1px solid #f1f5f9;
	border-radius: 12px;
	display: flex;
	align-items: center;
	justify-content: center;
}
</style>
