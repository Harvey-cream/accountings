<template>
  <view class="chatroom-container">
    <!-- 消息列表视图 -->
    <view v-if="currentView === 'list'" class="message-list-view">
      <!-- 顶部导航 -->
      <view class="nav-header">
        <view class="nav-left">
          <van-icon name="arrow-left" size="22" color="#0f172a" @click="backToList" />
        </view>
        <text class="nav-title">消息</text>
        <view class="nav-right">
           <van-icon name="search" size="22" color="#333" class="nav-icon" />
        </view>
      </view>

      <!-- 消息列表 -->
      <view class="message-list">
        <view v-for="chat in chatList" :key="chat.id" class="chat-item" @click="openChat(chat)">
          <view class="avatar-container">
            <image :src="chat.avatar" class="avatar-img" mode="aspectFill"></image>
            <view v-if="chat.unread > 0" class="unread-badge">{{ chat.unread }}</view>
          </view>
          <view class="chat-content">
            <view class="chat-top">
              <text class="chat-name">{{ chat.name }}</text>
              <text class="chat-time">{{ chat.time }}</text>
            </view>
            <text class="chat-msg">{{ chat.lastMessage }}</text>
          </view>
        </view>
      </view>
    </view>

    <!-- 聊天详情视图 -->
    <view v-else class="chat-detail-view">
      <!-- 顶部导航 -->
      <view class="chat-header">
        <van-icon name="arrow-left" size="22" color="#0f172a" @click="backToList" />
        <view class="header-center">
          <text class="header-name">{{ activeChat.name }}</text>
          <view class="online-status">
          </view>
        </view>
        <van-icon name="ellipsis" size="22" color="#0f172a" />
      </view>

      <!-- 消息记录 -->
      <scroll-view scroll-y class="message-area" :scroll-into-view="scrollTarget" scroll-with-animation>
        <view class="time-divider">下午 2:30</view>

        <view
          v-for="(msg, index) in currentMessages"
          :key="index"
          :class="['message-row', msg.isMe ? 'message-me' : 'message-other']"
          :id="'msg-' + index"
        >
          <image v-if="!msg.isMe" :src="activeChat.avatar" class="msg-avatar" mode="aspectFill"></image>

          <view class="msg-bubble-container">
            <!-- 文本消息 -->
            <view v-if="msg.type === 'text'" class="msg-bubble">
              <text class="bubble-text">{{ msg.content }}</text>
            </view>
            <!-- 图片消息 -->
            <image v-if="msg.type === 'image'" :src="msg.content" class="msg-image" mode="widthFix"></image>
            <!-- 地图卡片 -->
            <view v-if="msg.type === 'location'" class="location-card">
              <view class="map-placeholder">
                 <van-icon name="location" size="24" color="#ef4444" />
              </view>
              <view class="location-info">
                <text class="loc-name">{{ msg.content.name }}</text>
                <text class="loc-addr">{{ msg.content.address }}</text>
              </view>
            </view>
          </view>

          <image v-if="msg.isMe" src="https://api.dicebear.com/7.x/avataaars/svg?seed=Felix" class="msg-avatar" mode="aspectFill"></image>
        </view>
        <view id="bottom-anchor" style="height: 1px;"></view>
      </scroll-view>

      <!-- 底部输入框 -->
      <view class="chat-input-area">
        <van-icon name="volume-o" size="24" color="#333" class="input-icon" />
        <input
          class="chat-input"
          v-model="inputText"
          placeholder="发消息..."
          confirm-type="send"
          @confirm="sendMessage"
        />
        <van-icon name="smile-o" size="24" color="#333" class="input-icon" />
        <van-icon v-if="!inputText" name="add-o" size="24" color="#333" class="input-icon" />
        <view v-else class="send-btn" @click="sendMessage">
            <van-icon name="guide-o" size="20" color="#fff" />
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, computed, nextTick } from 'vue';

// 视图状态：'list' | 'chat'
const currentView = ref('list');
const activeChat = ref(null);
const inputText = ref('');
const scrollTarget = ref('');

// 虚拟数据 - 消息列表
const chatList = ref([
  {
    id: 1,
    name: 'TRAE',
    avatar: 'https://api.dicebear.com/7.x/bottts/svg?seed=TRAE',
    lastMessage: '[卡片]',
    time: '2025-12-05',
    unread: 0
  },
  {
    id: 2,
    name: '林小雨',
    avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=LXY',
    lastMessage: '没问题！我现在就过去。顺便把我的...',
    time: '2025-07-23',
    unread: 1
  },
  {
    id: 3,
    name: '深圳程序员 aben',
    avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Aben',
    lastMessage: '那不行啊，近两年都不招实习了',
    time: '2025-07-23',
    unread: 0
  },
  {
    id: 4,
    name: '小红薯 68749BF5',
    avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Potato',
    lastMessage: '对方账号异常，已被限制登录，消息无法送达',
    time: '2025-07-14',
    unread: 0
  },
  {
    id: 5,
    name: '阿桃今天没动',
    avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Peach',
    lastMessage: '加您啦',
    time: '2024-12-31',
    unread: 0
  },
  {
    id: 6,
    name: '谷主是个导演',
    avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Director',
    lastMessage: '不知道你说的是哪个？',
    time: '2024-12-12',
    unread: 0
  },
  {
    id: 7,
    name: '栗子画',
    avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Chestnut',
    lastMessage: '谢谢喜欢',
    time: '2024-12-12',
    unread: 0
  },
  {
    id: 8,
    name: '星视',
    avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Star',
    lastMessage: '请问你要用哪个视频呢',
    time: '2024-12-12',
    unread: 0
  },
  {
    id: 9,
    name: '新创视频工作室',
    avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Studio',
    lastMessage: '发给您 ae 源文件',
    time: '2024-12-11',
    unread: 0
  },
  {
    id: 10,
    name: 'Share嘉',
    avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Share',
    lastMessage: '您的图可以商用吗',
    time: '2024-12-11',
    unread: 1
  }
]);

// 虚拟数据 - 聊天记录
const messages = ref({
  2: [
    { type: 'text', content: '嘿！我看到你这周在餐饮上省了不少钱呢，是怎么做到的？我也想学习一下理财技巧。💰', isMe: false },
    { type: 'text', content: '哈哈，被你发现了！其实我最近在用那个“记账挑战”功能，每天给自己设定一个小目标。你要一起加入吗？', isMe: true },
    { type: 'text', content: '看起来不错！正好我在你附近的那个创意园区，我们可以见面聊聊吗？📍', isMe: false },
    { type: 'location', content: { name: '798 艺术区 - 咖啡厅', address: '距离你 500 米' }, isMe: false },
    { type: 'text', content: '没问题！我现在就过去。顺便把我的开支分析图表发你看看。📈', isMe: true }
  ]
});

// 当前聊天的消息列表
const currentMessages = computed(() => {
  if (!activeChat.value) return [];
  // 如果没有历史消息，给一条默认的打招呼
  if (!messages.value[activeChat.value.id]) {
    return [{ type: 'text', content: '你好呀！👋', isMe: false }];
  }
  return messages.value[activeChat.value.id];
});

// 打开聊天室
const openChat = (chat) => {
  activeChat.value = chat;
  currentView.value = 'chat';
  // 清除未读
  chat.unread = 0;
  scrollToBottom();
};

// 返回列表或上一级页面
const backToList = () => {
  if (currentView.value === 'chat') {
    // 如果当前是聊天详情，切换到消息列表
    currentView.value = 'list';
    activeChat.value = null;
  } else {
    // 如果当前是消息列表，返回上一级页面
    uni.navigateBack();
  }
};

// 发送消息
const sendMessage = () => {
  if (!inputText.value.trim() || !activeChat.value) return;

  if (!messages.value[activeChat.value.id]) {
    messages.value[activeChat.value.id] = [];
  }

  messages.value[activeChat.value.id].push({
    type: 'text',
    content: inputText.value,
    isMe: true
  });

  // 模拟对方回复
  setTimeout(() => {
    messages.value[activeChat.value.id].push({
      type: 'text',
      content: '收到啦！😄',
      isMe: false
    });
    scrollToBottom();
  }, 1000);

  inputText.value = '';
  scrollToBottom();
};

// 滚动到底部
const scrollToBottom = () => {
  nextTick(() => {
    scrollTarget.value = 'bottom-anchor';
    // 重置一下以确保下次变化能触发
    setTimeout(() => { scrollTarget.value = 'bottom-anchor'; }, 50);
  });
};
</script>

<style lang="scss" scoped >
@import './chat.scss';
</style>
