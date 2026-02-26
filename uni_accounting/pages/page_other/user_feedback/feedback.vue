<template>
  <view class="feedback-container" :class="currentThemeClass">
    <!-- 导航栏 -->
    <view class="header-section">
      <view class="nav-header">
        <van-icon name="arrow-left" size="20" color="#0f172a" @click="goBack" />
        <view class="page-title">意见反馈</view>
        <view class="nav-placeholder"></view>
      </view>
    </view>

    <!-- 聊天内容区 -->
    <scroll-view 
      scroll-y 
      class="chat-body" 
      :scroll-into-view="lastMessageId"
      scroll-with-animation
    >
      <view class="message-list">
        <view 
          v-for="(msg, index) in messages" 
          :key="index" 
          :id="'msg-' + index"
          :class="['message-item', msg.type]"
        >
          <view class="message-content">
            <text>{{ msg.text }}</text>
          </view>
        </view>
      </view>
    </scroll-view>

    <!-- 底部输入框 -->
    <view class="input-section">
      <view class="input-bar">
        <input 
          type="text" 
          v-model="inputText" 
          placeholder="请输入您的反馈意见..." 
          class="feedback-input"
          @confirm="sendMessage"
          confirm-type="send"
        />
        <view class="send-btn" @click="sendMessage">
          <van-icon name="guide-o" size="20" color="#0f172a" />
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, nextTick } from 'vue';

const inputText = ref('');
const messages = ref([
  { type: 'system', text: '您好！我是小龙记账的开发者。有什么建议或问题都可以直接告诉我哦。' }
]);
const lastMessageId = ref('');

const goBack = () => {
  uni.navigateBack();
};

const sendMessage = () => {
  const text = inputText.value.trim();
  if (!text) return;

  // 添加用户消息
  messages.value.push({ type: 'user', text });
  inputText.value = '';

  // 自动回复
  setTimeout(() => {
    messages.value.push({ 
      type: 'system', 
      text: '收到您的反馈！为了能更及时地解决您的问题，请添加我的微信：XiaoLongDev（备注：记账反馈），我会第一时间回复您。' 
    });
    scrollToBottom();
  }, 800);

  scrollToBottom();
};

const scrollToBottom = () => {
  nextTick(() => {
    lastMessageId.value = 'msg-' + (messages.value.length - 1);
  });
};
</script>

<style scoped>
.feedback-container {
  background-color: #f8fafc;
  width: 100%;
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow-x: hidden;
  box-sizing: border-box;
}

.feedback-container * {
  box-sizing: border-box;
}

.header-section {
  background-color: var(--main-color);
  padding: calc(var(--status-bar-height) + 10px) 16px 15px;
}

.nav-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.page-title {
  font-size: 18px;
  font-weight: 700;
  color: #0f172a;
}

.nav-placeholder {
  width: 20px;
}

/* 聊天区域 */
.chat-body {
  flex: 1;
  padding: 20px 16px;
  overflow-y: auto;
}

.message-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.message-item {
  display: flex;
  max-width: 85%;
}

.message-item.system {
  align-self: flex-start;
}

.message-item.user {
  align-self: flex-end;
  margin-right: 8px; /* 增加右边距，让气泡往左出来一点 */
}

.message-content {
  padding: 12px 16px;
  border-radius: 16px;
  font-size: 15px;
  line-height: 1.5;
  word-break: break-all;
}

.system .message-content {
  background-color: #ffffff;
  color: #1e293b;
  border-bottom-left-radius: 4px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.user .message-content {
  background-color: var(--main-color);
  color: #0f172a;
  border-bottom-right-radius: 4px;
}

/* 输入区域 */
.input-section {
  background-color: #ffffff;
  padding: 10px 16px calc(10px + env(safe-area-inset-bottom));
  border-top: 1px solid #f1f5f9;
}

.input-bar {
  display: flex;
  align-items: center;
  background-color: #f8fafc;
  border-radius: 24px;
  padding: 4px 4px 4px 16px;
  gap: 10px;
}

.feedback-input {
  flex: 1;
  height: 40px;
  font-size: 15px;
}

.send-btn {
  width: 40px;
  height: 40px;
  background-color: var(--main-color);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.send-btn:active {
  opacity: 0.8;
}
</style>