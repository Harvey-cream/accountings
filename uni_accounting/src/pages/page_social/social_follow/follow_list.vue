<template>
  <view class="follow-list-container">
    <!-- 顶部标题栏 + 标签 -->
    <view class="header-section" :style="{ paddingTop: statusBarHeight + 'px' }">
      <view class="back-icon" @click="goBack">
        <van-icon name="arrow-left" size="22" color="#0f172a" />
      </view>
      <view class="tabs">
        <view 
          v-for="(tab, index) in tabs" 
          :key="index" 
          :class="['tab-item', { active: currentTab === tab.type }]"
          @click="switchTab(tab.type)"
        >
          <text class="tab-text">{{ tab.name }}</text>
          <view class="tab-line" v-if="currentTab === tab.type"></view>
        </view>
      </view>
      <!-- 右侧占位，保持中间对称 -->
      <view class="header-placeholder"></view>
    </view>

    <scroll-view 
      scroll-y 
      class="list-scroll" 
      :show-scrollbar="false"
      :enhanced="true"
      @scrolltolower="onReachBottom"
    >
      <view v-if="userList.length > 0" class="user-list">
        <view v-for="user in userList" :key="user.userId" class="user-item" @click="goToProfile(user.userId)">
          <image class="avatar" :src="user.avatar || '/static/default_avatar.png'" mode="aspectFill"></image>
          <view class="user-info">
            <text class="nickname">{{ user.nickname }}</text>
            <text class="signature">{{ user.signature || '暂无简介' }}</text>
          </view>
          <view class="action-area" @click.stop="handleFollowAction(user)">
            <button v-if="currentTab === 'following'" class="action-btn followed">已关注</button>
            <button v-else :class="['action-btn', user.isFollowing ? 'followed' : 'follow']">
              {{ user.isFollowing ? (user.isMutual ? '互相关注' : '已关注') : '回关' }}
            </button>
          </view>
        </view>
        
        <!-- 加载更多提示 -->
        <view class="loading-more" v-if="userList.length > 10">
          <text class="loading-text">没有更多数据了</text>
        </view>
      </view>
      <view v-else class="empty-state">
        <van-icon name="friends-o" size="48" color="#cbd5e1" />
        <text class="empty-text">暂无数据</text>
      </view>
    </scroll-view>
  </view>
</template>

<script setup>
import { ref, reactive } from 'vue';
import { onLoad } from '@dcloudio/uni-app';
import { getFollowList, toggleFollow } from '@/api/api.js';

const targetUserId = ref('');
const statusBarHeight = ref(0);
const currentTab = ref('following'); // 'following' or 'followers'
const userList = ref([]);
const tabs = [
  { name: '关注', type: 'following' },
  { name: '粉丝', type: 'followers' }
];

onLoad((options) => {
  // 获取状态栏高度
  const systemInfo = uni.getSystemInfoSync();
  statusBarHeight.value = systemInfo.statusBarHeight || 0;

  if (options.userId) {
    targetUserId.value = options.userId;
  }
  if (options.type) {
    currentTab.value = options.type;
  }
  fetchList();
});

const fetchList = async () => {
  try {
    const res = await getFollowList(targetUserId.value, currentTab.value);
    if (res.code === 0) {
      userList.value = res.data;
    }
  } catch (e) {
    console.error('获取列表失败:', e);
  }
};

const switchTab = (type) => {
  if (currentTab.value === type) return;
  currentTab.value = type;
  userList.value = [];
  fetchList();
};

const goBack = () => {
  uni.navigateBack();
};

const goToProfile = (userId) => {
  uni.navigateTo({
    url: `/pages/page_social/social_profile/profile?userId=${userId}`
  });
};

const onReachBottom = () => {
  console.log('触底加载更多');
  // TODO: 实现分页加载逻辑
};

// 关注/取消关注逻辑 (带防抖)
const timers = {};
const originalStates = {};

const handleFollowAction = (user) => {
  const userId = user.userId;
  const isCurrentlyFollowing = currentTab.value === 'following' ? true : user.isFollowing;
  const nextState = !isCurrentlyFollowing;

  // 1. 乐观更新
  if (currentTab.value === 'following') {
    // 在关注列表取消关注，直接移除或标记
    uni.showModal({
      title: '提示',
      content: '确定要取消关注吗？',
      success: async (res) => {
        if (res.confirm) {
          try {
            const apiRes = await toggleFollow(userId, false);
            if (apiRes.code === 0) {
              userList.value = userList.value.filter(item => item.userId !== userId);
              uni.showToast({ title: '已取消关注', icon: 'none' });
            }
          } catch (e) {
            console.error('取消关注失败:', e);
          }
        }
      }
    });
  } else {
    // 在粉丝列表回关
    user.isFollowing = nextState;
    
    if (originalStates[userId] === undefined) {
      originalStates[userId] = isCurrentlyFollowing;
    }

    if (timers[userId]) clearTimeout(timers[userId]);

    timers[userId] = setTimeout(async () => {
      if (user.isFollowing !== originalStates[userId]) {
        try {
          await toggleFollow(userId, user.isFollowing);
        } catch (e) {
          user.isFollowing = originalStates[userId];
          console.error('操作失败:', e);
        }
      }
      delete timers[userId];
      delete originalStates[userId];
    }, 1000);
  }
};
</script>

<style scoped>
.follow-list-container {
  background-color: #ffffff;
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.header-section {
  background-color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  flex-shrink: 0;
  z-index: 100;
  border-bottom: 1px solid #f1f5f9;
}

.back-icon {
  width: 40px;
  height: 44px;
  display: flex;
  align-items: center;
}

.header-placeholder {
  width: 40px;
}

.tabs {
  flex: 1;
  display: flex;
  justify-content: center;
}

.tab-item {
  padding: 12px 15px;
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.tab-text {
  font-size: 15px;
  color: #64748b;
  font-weight: 500;
}

.tab-item.active .tab-text {
  color: #0f172a;
  font-weight: 700;
}

.tab-line {
  position: absolute;
  bottom: 0;
  width: 20px;
  height: 3px;
  background-color: #ffd541;
  border-radius: 2px;
}

.list-scroll {
  flex: 1;
  height: 0;
}

/* 隐藏滚动条 */
.list-scroll ::-webkit-scrollbar {
  display: none;
  width: 0 !important;
  height: 0 !important;
  -webkit-appearance: none;
  background: transparent;
}

.user-list {
  background-color: #fff;
}

.user-item {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid #f8fafc;
}

.avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  margin-right: 12px;
}

.user-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.nickname {
  font-size: 15px;
  font-weight: 600;
  color: #1e293b;
}

.signature {
  font-size: 12px;
  color: #94a3b8;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 200px;
}

.action-btn {
  height: 28px;
  padding: 0 12px;
  border-radius: 14px;
  font-size: 12px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
}

.follow {
  background-color: #ffd541;
  color: #0f172a;
}

.followed {
  background-color: #f1f5f9;
  color: #64748b;
}

.loading-more {
  padding: 20px 0;
  display: flex;
  justify-content: center;
  align-items: center;
}

.loading-text {
  font-size: 12px;
  color: #94a3b8;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding-top: 100px;
}

.empty-text {
  margin-top: 12px;
  font-size: 14px;
  color: #94a3b8;
}
</style>
