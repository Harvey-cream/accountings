<template>
  <view class="container">
    <!-- 顶部导航 -->
    <view class="nav-header">
      <view class="nav-left" @click="goBack">
        <van-icon name="arrow-left" size="24" color="#000" />
      </view>
      <view class="nav-tabs">
        <view 
          class="nav-tab" 
          :class="{ active: currentTab === 0 }" 
          @click="currentTab = 0"
        >
          <text>互动消息</text>
          <view v-if="currentTab === 0" class="tab-indicator"></view>
          <view v-if="unreadInteractions > 0" class="badge">{{ unreadInteractions }}</view>
        </view>
        <view 
          class="nav-tab" 
          :class="{ active: currentTab === 1 }" 
          @click="currentTab = 1"
        >
          <text>新关注我的</text>
          <view v-if="currentTab === 1" class="tab-indicator"></view>
          <view v-if="unreadFollows > 0" class="badge">{{ unreadFollows }}</view>
        </view>
      </view>
      <view class="nav-right"></view>
    </view>

    <!-- 列表内容 -->
    <scroll-view scroll-y class="content-area">
      
      <!-- 互动消息列表 -->
      <view v-if="currentTab === 0" class="list-container">
        <view v-for="(item, index) in interactionList" :key="index" class="message-item" @click="goToPost(item.postId)">
          <!-- 头像 -->
          <image class="avatar" :src="item.avatar" mode="aspectFill"></image>
          
          <!-- 中间内容 -->
          <view class="message-content">
            <view class="user-info">
              <text class="username">{{ item.username }}</text>
              <text class="time">{{ item.time }}</text>
            </view>
            
            <!-- 点赞类型 -->
            <view v-if="item.type === 'like_comment'" class="action-text">
              赞了你的评论
              <van-icon name="like" color="#ef4444" size="14" style="margin-left: 4px;" />
            </view>
            <view v-else-if="item.type === 'like_post'" class="action-text">
              赞了你的帖子
              <van-icon name="like" color="#ef4444" size="14" style="margin-left: 4px;" />
            </view>
            
            <!-- 评论/回复类型 -->
            <view v-else-if="item.type === 'reply'" class="action-text">
              回复：{{ item.content }}
            </view>
            <view v-else-if="item.type === 'comment'" class="action-text">
              评论：{{ item.content }}
            </view>
            
            <!-- 额外操作按钮 -->
            <view v-if="item.type === 'reply' || item.type === 'comment'" class="action-buttons">
              <view class="reply-btn">
                <van-icon name="chat-o" size="14" />
                <text>回复评论</text>
              </view>
            </view>
          </view>
          
          <!-- 右侧来源预览 -->
          <view class="source-preview">
            <image v-if="item.sourceImage" :src="item.sourceImage" mode="aspectFill" class="preview-image"></image>
            <view v-else class="preview-text">
              {{ item.sourceText }}
            </view>
          </view>
        </view>
        
        <!-- 空状态 -->
        <view v-if="interactionList.length === 0" class="empty-state">
          <van-icon name="comment-o" size="48" color="#cbd5e1" />
          <text>暂无互动消息</text>
        </view>
      </view>

      <!-- 新关注列表 -->
      <view v-if="currentTab === 1" class="list-container">
        <view v-for="(item, index) in followList" :key="index" class="follow-item">
          <image class="avatar" :src="item.avatar" mode="aspectFill"></image>
          <view class="follow-info">
            <text class="username">{{ item.username }}</text>
            <text class="follow-desc">关注了你 {{ item.time }}</text>
          </view>
          <view class="follow-btn" :class="{ followed: item.isFollowed }" @click="toggleFollow(index)">
            <text>{{ item.isFollowed ? '互相关注' : '回关' }}</text>
          </view>
        </view>
        
        <!-- 空状态 -->
        <view v-if="followList.length === 0" class="empty-state">
          <van-icon name="friends-o" size="48" color="#cbd5e1" />
          <text>暂无新关注</text>
        </view>
      </view>

    </scroll-view>
  </view>
</template>

<script setup>
import { ref } from 'vue';

const currentTab = ref(0);
const unreadInteractions = ref(3);
const unreadFollows = ref(1);

const goBack = () => {
  uni.navigateBack();
};

const goToPost = (postId) => {
  if (!postId) return;
  uni.navigateTo({
    url: `/pages/discover/community?postId=${postId}`
  });
};

// 模拟互动消息数据
const interactionList = ref([
  {
    type: 'like_comment',
    username: '阿洁西',
    avatar: '/static/4.jpg',
    time: '2小时前',
    sourceImage: '/static/3.jpg',
    postId: 1
  },
  {
    type: 'like_post',
    username: '漫春山',
    avatar: '/static/2.jpg',
    time: '3小时前',
    sourceImage: '/static/3.jpg',
    postId: 1
  },
  {
    type: 'reply',
    username: '大便超人 1113',
    avatar: '/static/1.jpg',
    time: '周四',
    content: '很开朗🤪',
    sourceText: '这里是原评论的内容...',
    postId: 2
  },
  {
    type: 'comment',
    username: 'wen.🐾',
    avatar: '/static/4.jpg',
    time: '周四',
    content: '改个造型 五官很帅的',
    sourceImage: '/static/1.jpg',
    postId: 2
  }
]);

// 模拟关注数据
const followList = ref([
  {
    username: '蛋挞',
    avatar: '/static/3.jpg',
    time: '2月15日',
    isFollowed: true
  },
  {
    username: '新用户9527',
    avatar: '/static/2.jpg',
    time: '刚刚',
    isFollowed: false
  }
]);

const toggleFollow = (index) => {
  followList.value[index].isFollowed = !followList.value[index].isFollowed;
};
</script>

<style scoped>
.container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: #fff;
}

.nav-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px 10px; /* 适配状态栏高度 */
  background-color: #fff;
  border-bottom: 1px solid #f1f5f9;
}

.nav-left, .nav-right {
  width: 40px;
  display: flex;
  align-items: center;
}

.nav-tabs {
  display: flex;
  gap: 24px;
}

.nav-tab {
  position: relative;
  font-size: 16px;
  color: #64748b;
  font-weight: 500;
  padding-bottom: 4px;
  transition: all 0.3s;
}

.nav-tab.active {
  color: #0f172a;
  font-weight: 700;
  font-size: 17px;
}

.tab-indicator {
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 20px;
  height: 3px;
  background-color: #facc15;
  border-radius: 2px;
}

.badge {
  position: absolute;
  top: -6px;
  right: -10px;
  background-color: #ef4444;
  color: #fff;
  font-size: 10px;
  padding: 0 4px;
  border-radius: 10px;
  min-width: 16px;
  text-align: center;
  line-height: 16px;
  border: 1px solid #fff;
}

.content-area {
  flex: 1;
  background-color: #fff;
}

.list-container {
  padding: 0 16px;
}

/* 消息列表项 */
.message-item {
  display: flex;
  padding: 16px 0;
  border-bottom: 1px solid #f8fafc;
}

.avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  margin-right: 12px;
  flex-shrink: 0;
  background-color: #f1f5f9;
}

.message-content {
  flex: 1;
  margin-right: 12px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.user-info {
  display: flex;
  align-items: center;
  margin-bottom: 4px;
}

.username {
  font-size: 15px;
  font-weight: 600;
  color: #334155;
  margin-right: 8px;
}

.time {
  font-size: 12px;
  color: #94a3b8;
}

.action-text {
  font-size: 14px;
  color: #0f172a;
  line-height: 1.4;
  margin-bottom: 6px;
}

.action-buttons {
  display: flex;
  gap: 12px;
}

.reply-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  background-color: #f8fafc;
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 12px;
  color: #64748b;
}

/* 来源预览 */
.source-preview {
  width: 64px;
  height: 64px;
  flex-shrink: 0;
  border-radius: 4px;
  overflow: hidden;
  background-color: #f8fafc;
  display: flex;
  align-items: center;
  justify-content: center;
}

.preview-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.preview-text {
  font-size: 12px;
  color: #64748b;
  padding: 4px;
  line-height: 1.3;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 3;
  overflow: hidden;
}

/* 关注列表项 */
.follow-item {
  display: flex;
  align-items: center;
  padding: 16px 0;
  border-bottom: 1px solid #f8fafc;
}

.follow-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.follow-desc {
  font-size: 13px;
  color: #64748b;
  margin-top: 2px;
}

.follow-btn {
  padding: 6px 16px;
  background-color: #facc15;
  color: #0f172a;
  font-size: 13px;
  font-weight: 600;
  border-radius: 18px;
  transition: all 0.2s;
}

.follow-btn.followed {
  background-color: #f1f5f9;
  color: #94a3b8;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding-top: 100px;
  gap: 16px;
}

.empty-state text {
  font-size: 14px;
  color: #94a3b8;
}
</style>