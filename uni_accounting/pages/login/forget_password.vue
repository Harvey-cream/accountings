<template>
  <view class="login-container" :class="currentThemeClass">
    <!-- 顶部背景装饰 -->
    <view class="top-bg">
      <view class="welcome-box">  
      </view>
    </view>

    <!-- 找回密码卡片 -->
    <view class="login-card">

      <!-- 输入区域 -->
      <view class="input-group">
        <view class="input-item">
          <input type="number" v-model="phone" placeholder="请输入手机号" maxlength="11" />
        </view>
        
        <view class="input-item">
          <input type="number" v-model="code" placeholder="请输入验证码" maxlength="6" />
          <text class="get-code" :class="{ disabled: counting }" @click="getCode">
            {{ counting ? `${count}s后获取` : '获取验证码' }}
          </text>
        </view>

        <view class="input-item">
          <input :type="showPassword ? 'text' : 'password'" v-model="password" placeholder="设置新登录密码" />
          <van-icon :name="showPassword ? 'eye-o' : 'closed-eye'" size="20" color="#cbd5e1" @click="showPassword = !showPassword" />
        </view>
      </view>

      <!-- 确定按钮 -->
      <button class="login-btn" @click="handleReset">重置密码</button>

      <!-- 底部链接 -->
      <view class="bottom-links">
        <text class="link-item" @click="goBack">返回登录</text>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue';

const phone = ref('');
const code = ref('');
const password = ref('');
const showPassword = ref(false);
const counting = ref(false);
const count = ref(60);

const goBack = () => {
  uni.navigateBack();
};

const getCode = () => {
  if (counting.value || !phone.value) return;
  counting.value = true;
  uni.showToast({ title: '验证码已发送', icon: 'none' });
  const timer = setInterval(() => {
    count.value--;
    if (count.value <= 0) {
      clearInterval(timer);
      counting.value = false;
      count.value = 60;
    }
  }, 1000);
};

const handleReset = () => {
  if (!phone.value || !code.value || !password.value) {
    uni.showToast({ title: '请填写完整信息', icon: 'none' });
    return;
  }
  uni.showLoading({ title: '处理中...' });
  setTimeout(() => {
    uni.hideLoading();
    uni.showToast({ title: '密码重置成功', icon: 'success' });
    setTimeout(() => {
      uni.navigateBack();
    }, 1000);
  }, 1000);
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
  background: linear-gradient(180deg, rgba(255, 213, 65, 0.4) 0%, rgba(255, 255, 255, 0) 100%);
  padding: 60px 30px 0;
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

.get-code {
  font-size: 14px;
  color: var(--main-color);
  font-weight: bold;
  padding-left: 10px;
}

.get-code.disabled {
  color: #cbd5e1;
}

.login-btn {
  margin-top: 40px;
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
</style>