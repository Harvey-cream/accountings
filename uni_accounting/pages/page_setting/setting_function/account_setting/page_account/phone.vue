<template>
  <view class="container" :class="currentThemeClass">
    <!-- 导航栏 -->
    <view class="nav-bar">
      <view class="nav-left" @click="goBack">
        <van-icon name="arrow-left" size="20" color="#1e293b" />
        <text class="nav-title">返回</text>
      </view>
      <text class="page-title">{{ isBind ? '修改手机号' : '绑定手机号' }}</text>
      <view class="nav-right"></view>
    </view>

    <view class="content-body">
      <!-- 选项列表 -->
      <view class="settings-group first-group">
        <view class="settings-item" @click="showCountryPopup = true">
          <text class="item-title">国家/地区</text>
          <view class="item-right">
            <text class="value-text">{{ selectedCountry.name }} (+{{ selectedCountry.code }})</text>
            <van-icon name="arrow" color="#cbd5e1" size="16" />
          </view>
        </view>
        <view class="settings-item" @click="showPhonePopup = true">
          <text class="item-title">手机号</text>
          <view class="item-right">
            <text class="value-text">{{ phone || '未填写' }}</text>
            <van-icon name="arrow" color="#cbd5e1" size="16" />
          </view>
        </view>
      </view>

      <view class="tips-section" v-if="isBind">
        <van-icon name="info-o" size="14" color="#64748b" />
        <text class="tips-text">修改手机号后，下次登录请使用新手机号。</text>
      </view>

      <view class="action-btn-fixed" @click="handleConfirm">
        <text>确定{{ isBind ? '修改' : '绑定' }}</text>
      </view>
    </view>

    <!-- 国家/地区选择弹窗 -->
    <van-popup
      v-model:show="showCountryPopup"
      position="bottom"
      round
      :style="{ height: '50%' }"
    >
      <view class="popup-content">
        <view class="popup-header">
          <text class="popup-title">选择国家/地区</text>
          <van-icon name="cross" size="20" color="#94a3b8" @click="showCountryPopup = false" />
        </view>
        <scroll-view scroll-y class="popup-body">
          <view 
            v-for="item in countries" 
            :key="item.code" 
            class="country-item"
            :class="{ active: selectedCountry.code === item.code }"
            @click="selectCountry(item)"
          >
            <text class="country-name">{{ item.name }}</text>
            <text class="country-code">+{{ item.code }}</text>
            <van-icon v-if="selectedCountry.code === item.code" name="success" color="#ffd541" size="18" />
          </view>
        </scroll-view>
      </view>
    </van-popup>

    <!-- 手机号/验证码输入弹窗 -->
    <van-popup
      v-model:show="showPhonePopup"
      position="bottom"
      round
      :style="{ height: '85%' }"
      @closed="resetDrafts"
    >
      <view class="popup-content full-height">
        <view class="popup-header">
          <text class="popup-title">{{ isBind ? '修改手机号' : '绑定手机号' }}</text>
          <van-icon name="cross" size="20" color="#94a3b8" @click="showPhonePopup = false" />
        </view>
        
        <view class="popup-body padding-20">
          <view class="input-group">
            <view class="input-label">新手机号</view>
            <view class="input-wrapper">
              <text class="area-code">+{{ selectedCountry.code }}</text>
              <input 
                class="popup-input" 
                v-model="phoneDraft" 
                type="number" 
                placeholder="请输入手机号" 
                maxlength="11"
              />
            </view>
          </view>

          <view class="input-group">
            <view class="input-label">验证码</view>
            <view class="verify-row">
              <input 
                class="popup-input flex-1" 
                v-model="verifyCodeDraft" 
                type="number" 
                placeholder="请输入验证码" 
                maxlength="6" 
              />
              <view class="verify-btn" :class="{ disabled: isCounting }" @click="getVerifyCode">
                {{ isCounting ? `${countDown}s后重试` : '获取验证码' }}
              </view>
            </view>
          </view>

          <view class="popup-tips">
            验证码将发送至您的手机，请注意查收。
          </view>
        </view>

        <view class="popup-footer">
          <view class="confirm-btn" @click="confirmPhoneEdit">确定</view>
        </view>
      </view>
    </van-popup>
  </view>
</template>

<script setup>
import { ref } from 'vue';
import { onLoad } from '@dcloudio/uni-app';

const phone = ref('');
const isBind = ref(false);

const showCountryPopup = ref(false);
const showPhonePopup = ref(false);

const countries = [
  { name: '中国', code: '86' },
  { name: '中国香港', code: '852' },
  { name: '中国澳门', code: '853' },
  { name: '中国台湾', code: '886' },
  { name: '美国', code: '1' },
  { name: '日本', code: '81' },
  { name: '韩国', code: '82' },
  { name: '英国', code: '44' }
];

const selectedCountry = ref(countries[0]);
const phoneDraft = ref('');
const verifyCodeDraft = ref('');

const isCounting = ref(false);
const countDown = ref(60);

onLoad((options) => {
  if (options.phone && options.phone !== 'undefined' && options.phone !== '') {
    isBind.value = true;
    phone.value = options.phone;
    phoneDraft.value = options.phone;
  }
});

const goBack = () => {
  uni.navigateTo({
    url: '/pages/page_setting/setting_function/account_setting/account'
  });
};

const selectCountry = (item) => {
  selectedCountry.value = item;
  showCountryPopup.value = false;
};

const resetDrafts = () => {
  if (!showPhonePopup.value) {
    phoneDraft.value = phone.value;
    verifyCodeDraft.value = '';
  }
};

const getVerifyCode = () => {
  if (isCounting.value) return;
  if (!/^1[3-9]\d{9}$/.test(phoneDraft.value)) {
    uni.showToast({ title: '请输入有效的手机号', icon: 'none' });
    return;
  }
  
  uni.showLoading({ title: '发送中...' });
  setTimeout(() => {
    uni.hideLoading();
    uni.showToast({ title: '验证码已发送', icon: 'success' });
    isCounting.value = true;
    const timer = setInterval(() => {
      countDown.value--;
      if (countDown.value <= 0) {
        clearInterval(timer);
        isCounting.value = false;
        countDown.value = 60;
      }
    }, 1000);
  }, 1000);
};

const confirmPhoneEdit = () => {
  if (!/^1[3-9]\d{9}$/.test(phoneDraft.value)) {
    uni.showToast({ title: '请输入有效的手机号', icon: 'none' });
    return;
  }
  if (!verifyCodeDraft.value.trim()) {
    uni.showToast({ title: '请输入验证码', icon: 'none' });
    return;
  }

  phone.value = phoneDraft.value;
  showPhonePopup.value = false;
  uni.showToast({ title: '设置成功', icon: 'success' });
};

const handleConfirm = () => {
  if (!phone.value) {
    uni.showToast({ title: '请先填写手机号', icon: 'none' });
    return;
  }
  // 模拟提交
  uni.showToast({ title: isBind.value ? '修改成功' : '绑定成功', icon: 'success' });
  setTimeout(() => {
    goBack();
  }, 1500);
};
</script>

<style scoped>
.container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: #f8fafc;
}

/* 导航栏样式已移至全局 common.css */

.content-body {
  flex: 1;
  padding: 5px;
}

/* 列表样式 */
.settings-group {
  background-color: #ffffff;
  border-radius: 12px;
  overflow: hidden;
  margin-bottom: 16px;
}

.settings-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  border-bottom: 1px solid #f1f5f9;
}

.settings-item:last-child {
  border-bottom: none;
}

.settings-item:active {
  background-color: #f8fafc;
}

.item-title {
  font-size: 16px;
  color: #1e293b;
}

.item-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.value-text {
  font-size: 15px;
  color: #64748b;
}

.tips-section {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 0 4px;
  margin-top: 12px;
}

.tips-text {
  font-size: 12px;
  color: #64748b;
}

/* 底部固定按钮 */
.action-btn-fixed {
  position: fixed;
  bottom: 40px;
  left: 16px;
  right: 16px;
  height: 50px;
  background-color: #ffd541;
  border-radius: 25px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  font-weight: 700;
  color: #1e293b;
  box-shadow: 0 4px 12px rgba(255, 213, 65, 0.3);
}

/* 弹窗样式 */
.popup-content {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.full-height {
  height: 100%;
}

.popup-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px;
  border-bottom: 1px solid #f1f5f9;
}

.popup-title {
  font-size: 18px;
  font-weight: 700;
  color: #1e293b;
}

.popup-body {
  flex: 1;
  overflow-y: auto;
}

.padding-20 {
  padding: 20px;
}

/* 国家列表项 */
.country-item {
  display: flex;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #f8fafc;
}

.country-item:active {
  background-color: #f8fafc;
}

.country-item.active {
  background-color: #fffbeb;
}

.country-name {
  flex: 1;
  font-size: 16px;
  color: #1e293b;
}

.country-code {
  font-size: 14px;
  color: #64748b;
  margin-right: 12px;
}

/* 输入框样式 */
.input-group {
  margin-bottom: 24px;
}

.input-label {
  font-size: 14px;
  color: #64748b;
  margin-bottom: 12px;
}

.input-wrapper {
  display: flex;
  align-items: center;
  height: 52px;
  background-color: #f8fafc;
  border-radius: 12px;
  padding: 0 16px;
}

.area-code {
  font-size: 16px;
  color: #1e293b;
  font-weight: 500;
  margin-right: 12px;
  padding-right: 12px;
  border-right: 1px solid #e2e8f0;
}

.popup-input {
  flex: 1;
  height: 100%;
  font-size: 16px;
  color: #1e293b;
}

.verify-row {
  display: flex;
  gap: 12px;
}

.verify-btn {
  min-width: 100px;
  height: 52px;
  background-color: #fff;
  border: 1px solid #ffd541;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  color: #b45309;
  font-weight: 500;
  padding: 0 12px;
}

.verify-btn.disabled {
  border-color: #e2e8f0;
  color: #94a3b8;
  background-color: #f8fafc;
}

.popup-tips {
  font-size: 12px;
  color: #94a3b8;
  margin-top: 12px;
}

.popup-footer {
  padding: 20px;
  padding-bottom: calc(20px + env(safe-area-inset-bottom));
}

.confirm-btn {
  height: 50px;
  background-color: #ffd541;
  border-radius: 25px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  font-weight: 700;
  color: #1e293b;
}

.confirm-btn:active {
  opacity: 0.9;
}

/* 隐藏滚动条 */
::-webkit-scrollbar {
  display: none;
  width: 0;
  height: 0;
  color: transparent;
}
</style>