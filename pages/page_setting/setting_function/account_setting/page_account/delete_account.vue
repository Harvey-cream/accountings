<template>
  <view class="delete-account-container" :class="currentThemeClass">
    <!-- 导航栏 -->
    <view class="nav-bar">
      <view class="nav-left" @click="goBack">
        <van-icon name="arrow-left" size="20" color="#1e293b" />
        <text class="nav-title">返回</text>
      </view>
      <text class="page-title">注销账号</text>
      <view class="nav-right"></view>
    </view>

    <!-- 内容区 -->
    <scroll-view scroll-y class="content-body">
      <view class="warning-section">
        <view class="warning-header">
          <text class="warning-title">注销账号前请确认</text>
          <text class="warning-subtitle">注销后您的所有数据将被永久删除且无法找回</text>
        </view>

        <view class="consequence-list">
          <view class="consequence-item">
            <text class="dot">•</text>
            <text class="consequence-text">所有记账明细、预算计划及资产数据将全部被清空。</text>
          </view>
          <view class="consequence-item">
            <text class="dot">•</text>
            <text class="consequence-text">如果您是 VIP 会员，剩余会员权益将自动作废且不支持退款。</text>
          </view>
          <view class="consequence-item">
            <text class="dot">•</text>
            <text class="consequence-text">您的账号 ID 将被回收，无法再次使用该 ID 登录。</text>
          </view>
          <view class="consequence-item">
            <text class="dot">•</text>
            <text class="consequence-text">与该账号绑定的手机号、微信等社交平台将自动解除绑定。</text>
          </view>
        </view>
      </view>

      <view class="agreement-section">
        <label class="checkbox-label" @click="isAgreed = !isAgreed">
          <view class="checkbox-box" :class="{ checked: isAgreed }">
            <van-icon v-if="isAgreed" name="success" size="12" color="#fff" />
          </view>
          <text class="agreement-text">我已阅读并知晓注销账号的所有后果</text>
        </label>
      </view>

      <view class="action-section">
        <view 
          class="delete-btn" :class="{ disabled: !isAgreed }" @click="handleConfirmDelete" >
          <text>确认注销账号</text>
        </view>
        <view class="cancel-btn" @click="goBack">
          <text>暂不注销</text>
        </view>
      </view>
    </scroll-view>
  </view>
</template>

<script setup>
import { ref } from 'vue';

const isAgreed = ref(false);

const goBack = () => {
  uni.navigateTo({
    url: '/pages/page_setting/setting_function/account_setting/account'
  });
};

const handleConfirmDelete = () => {
  if (!isAgreed.value) return;

  uni.showModal({
    title: '最终确认',
    content: '此操作不可撤销，确定要永久注销您的账号吗？',
    confirmText: '确定注销',
    confirmColor: '#ef4444',
    success: (res) => {
      if (res.confirm) {
        uni.showLoading({ title: '注销中...' });
        // 模拟注销逻辑
        setTimeout(() => {
          uni.hideLoading();
          uni.showToast({
            title: '账号已注销',
            icon: 'success',
            duration: 2000
          });
          // 注销后跳转到登录或个人中心
          setTimeout(() => {
            uni.reLaunch({
              url: '/pages/setting/center'
            });
          }, 2000);
        }, 1500);
      }
    }
  });
};
</script>

<style scoped>
.delete-account-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: #fff;
}

.content-body {
  flex: 1;
  align-items: center;
  justify-content: center;
}

.warning-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  margin-bottom: 32px;
}

.warning-title {
  font-size: 20px;
  font-weight: 700;
  color: #0f172a;
  margin-top: 16px;
}

.warning-subtitle {
  font-size: 14px;
  color: #64748b;
  margin-top: 8px;
}

.consequence-list {
  border-radius: 12px;
  padding: 10px 40px;
  margin-bottom: 32px;
}

.consequence-item {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}

.consequence-item:last-child {
  margin-bottom: 0;
}

.dot {
  color: #94a3b8;
  font-weight: bold;
}

.consequence-text {
  font-size: 14px;
  color: #334155;
  line-height: 1.6;
}

.agreement-section {
  display: flex;
  justify-content: center;
  margin-bottom: 40px;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
}

.checkbox-box {
  width: 18px;
  height: 18px;
  border: 1px solid #cbd5e1;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.checkbox-box.checked {
  background-color: #ef4444;
  border-color: #ef4444;
}

.agreement-text {
  font-size: 14px;
  color: #475569;
}

.action-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.delete-btn {
  width: 160px; 
  height: 40px;
  background-color: #ef4444;
  border-radius: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 13px;
  font-weight: 600;
  box-shadow: 0 4px 6px -1px rgba(239, 68, 68, 0.2);
}

.delete-btn.disabled {
  background-color: #fca5a5;
  box-shadow: none;
  opacity: 0.6;
}

.cancel-btn {
  width: 160px; 
  height: 40px;
  background-color: #f1f5f9;
  border-radius: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #64748b;
  font-size: 13px; 
  font-weight: 500;
}

.delete-btn:active:not(.disabled), .cancel-btn:active {
  opacity: 0.8;
}
</style>
