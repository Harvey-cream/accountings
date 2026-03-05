<template>
  <view class="container" :class="currentThemeClass">
    <!-- 导航栏 -->
    <view class="nav-bar">
      <view class="nav-left" @click="goBack">
        <van-icon name="arrow-left" size="20" color="#1e293b" />
        <text class="nav-title">返回</text>
      </view>
      <text class="page-title">应急联系方式</text>
      <view class="nav-right"></view>
    </view>

    <view class="content-body">
      <!-- 选项列表 -->
      <view class="settings-group">
        <view class="settings-item" @click="openPopup('phone')">
          <text class="item-title">应急手机号</text>
          <view class="item-right">
            <text class="value-text">{{ phone || '未设置' }}</text>
            <van-icon name="arrow" color="#cbd5e1" size="16" />
          </view>
        </view>
        <view class="settings-item" @click="openPopup('email')">
          <text class="item-title">应急邮箱</text>
          <view class="item-right">
            <text class="value-text">{{ email || '未设置' }}</text>
            <van-icon name="arrow" color="#cbd5e1" size="16" />
          </view>
        </view>
      </view>
      <view class="tips-card">
        <van-icon name="info-o" size="16" color="#f59e0b" />
        <text class="tips-text">当您无法登录账号时，可通过应急联系方式找回。建议同时设置手机号和邮箱。</text>
      </view>
      <view class="action-btn-fixed" @click="handleSave">
        <text>保存设置</text>
      </view>
    </view>

    <!-- 编辑弹窗 -->
    <van-popup
      v-model:show="showPopup"
      position="bottom"
      round
      :style="{ height: '85%' }"
      @closed="resetDraft"
    >
      <view class="popup-content full-height">
        <view class="popup-header">
          <text class="popup-title">{{ activeType === 'phone' ? '设置应急手机号' : '设置应急邮箱' }}</text>
          <van-icon name="cross" size="20" color="#94a3b8" @click="showPopup = false" />
        </view>
        
        <view class="popup-body padding-20">
          <view class="input-group">
            <view class="input-label">{{ activeType === 'phone' ? '手机号' : '邮箱地址' }}</view>
            <input 
              class="popup-input-bg" 
              v-model="draftValue" 
              :type="activeType === 'phone' ? 'number' : 'text'" 
              :placeholder="activeType === 'phone' ? '请输入应急手机号' : '请输入应急邮箱'" 
              :maxlength="activeType === 'phone' ? 11 : 50"
            />
          </view>

          <view class="popup-tips">
            {{ activeType === 'phone' ? '请确保该手机号真实有效，以便在紧急情况下联系。' : '请确保该邮箱能够正常接收邮件。' }}
          </view>
        </view>

        <view class="popup-footer">
          <view class="confirm-btn" @click="confirmDraft">确定</view>
        </view>
      </view>
    </van-popup>
  </view>
</template>

<script setup>
import { ref } from 'vue';
import { onLoad } from '@dcloudio/uni-app';

const phone = ref('');
const email = ref('');

const showPopup = ref(false);
const activeType = ref('phone'); // 'phone' | 'email'
const draftValue = ref('');

onLoad((options) => {
  if (options.contact) {
    const val = decodeURIComponent(options.contact);
    if (/^1\d{10}$/.test(val)) phone.value = val;
    if (/@/.test(val)) email.value = val;
  }
});

const goBack = () => {
  uni.navigateTo({
    url: '/pages/page_setting/setting_function/account_setting/account'
  });
};

const openPopup = (type) => {
  activeType.value = type;
  draftValue.value = type === 'phone' ? phone.value : email.value;
  showPopup.value = true;
};

const resetDraft = () => {
  draftValue.value = '';
};

const confirmDraft = () => {
  const val = draftValue.value.trim();
  if (activeType.value === 'phone') {
    if (val && !/^1[3-9]\d{9}$/.test(val)) {
      uni.showToast({ title: '请输入有效的手机号', icon: 'none' });
      return;
    }
    phone.value = val;
  } else {
    if (val && !/^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/.test(val)) {
      uni.showToast({ title: '请输入有效的邮箱', icon: 'none' });
      return;
    }
    email.value = val;
  }
  showPopup.value = false;
};

const handleSave = () => {
  if (!phone.value && !email.value) {
    uni.showToast({ title: '请至少设置一项', icon: 'none' });
    return;
  }
  // 模拟提交
  uni.showToast({ title: '保存成功', icon: 'success' });
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

.tips-card {
  background-color: #fffbeb;
  border-radius: 12px;
  padding: 16px;
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}

.tips-text {
  font-size: 13px;
  color: #b45309;
  line-height: 1.5;
  flex: 1;
}

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
}

.padding-20 {
  padding: 20px;
}

.input-group {
  margin-bottom: 24px;
}

.input-label {
  font-size: 14px;
  color: #64748b;
  margin-bottom: 12px;
}

.popup-input-bg {
  height: 52px;
  background-color: #f8fafc;
  border-radius: 12px;
  padding: 0 16px;
  font-size: 16px;
  color: #1e293b;
}

.popup-tips {
  font-size: 12px;
  color: #94a3b8;
  line-height: 1.6;
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
</style>