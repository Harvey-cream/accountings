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
      <view v-for="(msg, index) in messages" :key="index" class="message-item" @click="handleItemClick(msg)">
        <view class="avatar-section">
          <van-badge :dot="!msg.is_read" position="top-right">
            <view class="system-avatar">
              <van-icon name="gold-coin" size="24" color="#333" />
            </view>
          </van-badge>
        </view>
        <view class="content-section">
          <view class="msg-header">
            <text class="sender-name">{{ msg.title }}</text>
            <text class="msg-time">{{ msg.time }}</text>
          </view>
          <view class="msg-body">
            <text>{{ msg.content }}</text>
            <text v-if="msg.link_text" class="link-text">{{ msg.link_text }}</text>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { getSystemMessages, markMessageRead } from '@/api/api.js';

const messages = ref([]);

const fetchMessages = async () => {
  try {
    const res = await getSystemMessages();
    if (res.code === 0) {
      messages.value = res.data;
    }
  } catch (e) {
    console.error('获取消息失败:', e);
  }
};

onMounted(() => {
  fetchMessages();
});

const goBack = () => {
  uni.navigateBack();
};

const handleItemClick = async (msg) => {
  // 如果未读，标记为已读
  if (!msg.is_read) {
    try {
      const res = await markMessageRead(msg.id);
      if (res.code === 0) {
        msg.is_read = true; // 前端立即反馈
      }
    } catch (e) {
      console.error('标记已读失败:', e);
    }
  }
  
  // 如果有跳转链接，进行跳转
  if (msg.link_url) {
    uni.navigateTo({
      url: msg.link_url,
      fail: () => {
        // 如果 navigateTo 失败（可能是非页面路径），尝试 switchTab
        uni.switchTab({
          url: msg.link_url
        });
      }
    });
  }
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
