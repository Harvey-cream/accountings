<template>
  <view class="message-container" :class="currentThemeClass">
    <!-- Header -->
    <view class="nav-header">
      <view class="nav-left" @click="goBack">
        <van-icon name="arrow-left" size="20" color="#333" />
        <text class="nav-back-text">返回</text>
      </view>
      <text class="nav-title">消息</text>
      <view class="nav-right"></view>
    </view>

    <!-- Message List -->
    <view class="message-list">
      <view v-for="(msg, index) in messages" :key="index" class="message-item">
        <view class="avatar-section">
          <view class="system-avatar">
            <van-icon name="gold-coin" size="24" color="#333" />
          </view>
        </view>
        <view class="content-section">
          <view class="msg-header">
            <text class="sender-name">小龙记账</text>
            <text class="msg-time">{{ msg.time }}</text>
          </view>
          <view class="msg-body">
            <text>{{ msg.text }}</text>
            <text v-if="msg.linkText" class="link-text" @click="handleLink(msg)">{{ msg.linkText }}</text>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue';

const messages = ref([
  {
    time: '01-03 14:18',
    text: '2025年账单来啦，',
    linkText: '快来看看吧>>'
  },
  {
    time: '2025-12-31 11:17',
    text: '参与小龙记账小调研即可获得50积分，',
    linkText: '猛戳参与>>'
  },
   {
    time: '2025-12-25 09:00',
    text: '圣诞快乐！送您一张记账VIP体验卡，',
    linkText: '点击领取>>'
  }
]);

const goBack = () => {
  uni.navigateBack();
};

const handleLink = (msg) => {
  uni.showToast({
    title: '点击了链接',
    icon: 'none'
  });
};
</script>

<style scoped>
.message-container {
  min-height: 100vh;
  background-color: #ffffff;
}

.nav-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 16px 12px; 
  background-color: #fff;
  border-bottom: 1px solid #f1f5f9;
  position: sticky;
  top: 0;
  z-index: 100;
}

.nav-left {
  display: flex;
  align-items: center;
  gap: 4px;
}

.nav-back-text {
  font-size: 16px;
  color: #333;
}

.nav-title {
  font-size: 17px;
  font-weight: 600;
  color: #333;
}

.nav-right {
  width: 60px; /* Balance left side */
}

.message-list {
  padding: 0 16px;
}

.message-item {
  display: flex;
  padding: 20px 0;
  border-bottom: 1px solid #f1f5f9;
}

.avatar-section {
  margin-right: 12px;
}

.system-avatar {
  width: 44px;
  height: 44px;
  background-color: #ffd541;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.content-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.msg-header {
  display: flex;
  flex-direction: column;
  margin-bottom: 6px;
}

.sender-name {
  font-size: 15px;
  font-weight: 600;
  color: #333;
  margin-bottom: 2px;
}

.msg-time {
  font-size: 12px;
  color: #94a3b8;
}

.msg-body {
  font-size: 15px;
  color: #333;
  line-height: 1.5;
}

.link-text {
  color: #3b82f6;
  margin-left: 4px;
}
</style>
