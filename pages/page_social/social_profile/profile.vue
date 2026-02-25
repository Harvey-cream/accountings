<template>
  <view class="profile-container">
    <!-- 顶部导航栏 -->
    <view class="nav-header" :style="{ paddingTop: statusBarHeight + 'px' }">
      <view class="nav-left" @click="goBack">
        <van-icon name="wap-nav" v-if="isSelf" size="24" color="#0f172a" />
        <van-icon name="arrow-left" v-else size="22" color="#0f172a" />
      </view>
      <view class="nav-right">
        <view v-if="isSelf" class="edit-btn-pill" @click="editProfile">
          <van-icon name="edit" size="14" />
          <text class="edit-text">编辑主页</text>
        </view>
        <van-icon name="qr" size="22" color="#0f172a" class="nav-icon" />
        <van-icon name="share-o" size="22" color="#0f172a" class="nav-icon" />
      </view>
    </view>

    <!-- 个人信息头部 -->
    <view class="profile-header-card">
      <view class="header-main">
        <view class="avatar-wrapper">
          <image class="avatar" :src="user.avatar" mode="aspectFill"></image>
          <view v-if="isSelf" class="plus-badge">
            <van-icon name="plus" size="12" color="#000" />
          </view>
        </view>
        <view class="header-right">
          <text class="user-name">{{ user.name }}</text>
          <view class="user-id-row">
            <text class="user-id">小龙号: {{ user.id }}</text>
            <van-icon name="qr-invalid" size="12" color="#94a3b8" />
          </view>
        </view>
      </view>

      <!-- 数据统计 -->
      <view class="stats-row">
        <view class="stat-item" @click="goToFollowList('following')">
          <text class="stat-num">{{ user.following }}</text>
          <text class="stat-label">关注</text>
        </view>
        <view class="stat-item" @click="goToFollowList('followers')">
          <text class="stat-num">{{ user.followers }}</text>
          <text class="stat-label">粉丝</text>
        </view>
        <view class="stat-item">
          <text class="stat-num">{{ user.likesAndCollects || 0 }}</text>
          <text class="stat-label">获赞与收藏</text>
        </view>
      </view>

      <!-- 简介 -->
      <view class="bio-section">
        <text class="user-bio">{{ user.bio || '点击这里，填写简介' }}</text>
      </view>

      <view class="action-row" v-if="!isSelf">
        <button :class="['action-btn', user.isFollowed ? 'followed-btn' : 'follow-btn']" @click="toggleFollow">
          {{ user.isFollowed ? '已关注' : '关注' }}
        </button>
        <button class="action-btn msg-btn">私信</button>
      </view>
    </view>

    <!-- 内容区 -->
    <view class="content-tabs">
      <view 
        v-for="(tab, index) in tabs" 
        :key="index" 
        :class="['tab-item', { active: currentTab === index }]"
        @click="currentTab = index"
      >
        <view class="tab-label-box">
          <van-icon v-if="tab.icon" :name="tab.icon" size="14" class="tab-icon" />
          <text class="tab-text">{{ tab.name }}</text>
        </view>
        <view class="tab-line" v-if="currentTab === index"></view>
      </view>
    </view>

    <!-- 帖子列表 -->
    <view class="post-feed">
      <view v-if="userPosts.length > 0">
        <view v-for="post in userPosts" :key="post.postId" class="post-card">
          <view class="post-card-body">
            <text class="post-text">{{ post.text }}</text>
            <view v-if="post.hasImages" class="post-images">
              <view v-for="(image, index) in post.images" :key="index" class="img-wrapper" @click="previewImage(post.images, index)">
                <image :src="image" class="img-content" mode="aspectFill"></image>
              </view>
            </view>
            <view class="post-footer">
              <text class="post-time">{{ post.time }}</text>
              <view class="post-actions">
                <view class="action-item">
                  <van-icon name="comment-o" size="16" />
                  <text class="action-num">{{ post.comments }}</text>
                </view>
                <view class="action-item" @click.stop="toggleLike(post)">
                  <van-icon :name="post.isLiked ? 'good-job' : 'good-job-o'" size="16" :color="post.isLiked ? '#ff0000' : '#64748b'" />
                  <text class="action-num" :class="{ 'liked': post.isLiked }">{{ post.likes }}</text>
                </view>
              </view>
            </view>
          </view>
        </view>
      </view>
      <view v-else class="empty-state">
        <van-icon name="notes-o" size="48" color="#cbd5e1" />
        <text class="empty-text">暂时还没有发布过动态</text>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import { onLoad } from '@dcloudio/uni-app';

const statusBarHeight = ref(0);
const isSelf = ref(true);
const currentTab = ref(0);
const tabs = [
  { name: '贴子' },
  { name: '评论', icon: 'lock' },
  { name: '收藏' },
  { name: '赞过', icon: 'lock' }
];

const user = reactive({
  id: '888888',
  name: 'oxo',
  avatar: '/static/4.jpg',
  bio: '保持热爱，奔赴山海。✨',
  following: 128,
  followers: 1024,
  likesAndCollects: 256,
  postsCount: 12,
  isFollowed: false
});

const userPosts = ref([
  {
    postId: 101,
    time: '昨天 18:30',
    text: '今天的记账挑战完成！省下了30块钱，开心~ 💰',
    hasImages: true,
    images: ['/static/4.jpg'],
    likes: 45,
    isLiked: false,
    comments: 8
  },
  {
    postId: 102,
    time: '3天前',
    text: '分享一个超好用的存钱小技巧：每天把零钱存进小金库，一个月下来也是一笔不小的数目呢。',
    hasImages: false,
    likes: 89,
    isLiked: true,
    comments: 12
  }
]);

onLoad((options) => {
  // 获取状态栏高度
  const systemInfo = uni.getSystemInfoSync();
  statusBarHeight.value = systemInfo.statusBarHeight || 0;

  if (options.userId && options.userId !== 'self') {
    isSelf.value = false;
    // 模拟获取他人信息
    user.name = '省钱达人';
    user.id = options.userId;
    user.bio = '一个正在努力攒钱买房的打工人 🏠';
    user.following = 256;
    user.followers = 512;
    user.likesAndCollects = 1024;
    user.postsCount = 8;
  }
});

const goBack = () => {
  uni.navigateBack();
};

const toggleFollow = () => {
  user.isFollowed = !user.isFollowed;
  if (user.isFollowed) {
    user.followers++;
    uni.showToast({ title: '已关注', icon: 'none' });
  } else {
    user.followers--;
    uni.showToast({ title: '已取消关注', icon: 'none' });
  }
};

const toggleLike = (post) => {
  if (post.isLiked) {
    post.likes--;
    post.isLiked = false;
  } else {
    post.likes++;
    post.isLiked = true;
  }
};

const previewImage = (images, index) => {
  uni.previewImage({
    urls: images,
    current: index
  });
};

const editProfile = () => {
  uni.showToast({ title: '点击了编辑资料', icon: 'none' });
};

const goToFollowList = (type) => {
  console.log('Go to', type, 'list');
};
</script>

<style scoped>
.profile-container {
  background-color: #f8fafc;
  min-height: 100vh;
}

/* 导航栏 */
.nav-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 16px;
  background-color: #fff;
  position: sticky;
  top: 0;
  z-index: 100;
}

.nav-right {
  display: flex;
  align-items: center;
  gap: 15px;
}

.nav-icon {
  margin-left: 5px;
}

.edit-btn-pill {
  background-color: #f1f5f9;
  border: 1px solid #e2e8f0;
  padding: 4px 12px;
  border-radius: 20px;
  display: flex;
  align-items: center;
  gap: 4px;
  color: #0f172a;
  margin-right: 5px;
}

.edit-text {
  font-size: 12px;
  font-weight: 600;
}

/* 个人信息卡片 */
.profile-header-card {
  background-color: #fff;
  padding: 20px 16px;
  margin-bottom: 10px;
}

.header-main {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 20px;
}

.avatar-wrapper {
  position: relative;
}

.avatar {
  width: 76px;
  height: 76px;
  border-radius: 50%;
  border: 1px solid #f1f5f9;
}

.plus-badge {
  position: absolute;
  right: 0;
  bottom: 4px;
  background-color: #ffd541;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px solid #fff;
}

.header-right {
  display: flex;
  flex-direction: column;
}

.user-name {
  font-size: 20px;
  font-weight: 800;
  color: #0f172a;
}

.user-id-row {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 4px;
}

.user-id {
  font-size: 12px;
  color: #94a3b8;
}

/* 统计数据 */
.stats-row {
  display: flex;
  gap: 24px;
  margin-bottom: 15px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.stat-num {
  font-size: 16px;
  font-weight: 800;
  color: #0f172a;
}

.stat-label {
  font-size: 13px;
  color: #64748b;
}

/* 简介 */
.bio-section {
  margin-bottom: 20px;
}

.user-bio {
  font-size: 14px;
  color: #475569;
  line-height: 1.5;
}

.action-row {
  display: flex;
  gap: 10px;
}

.action-btn {
  flex: 1;
  height: 38px;
  border-radius: 19px;
  font-size: 14px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  transition: opacity 0.2s;
}

.action-btn:active {
  opacity: 0.8;
}

.edit-btn {
  background-color: #f1f5f9;
  color: #0f172a;
}

.follow-btn {
  background-color: #ffd541;
  color: #0f172a;
}

.followed-btn {
  background-color: #f1f5f9;
  color: #64748b;
}

.msg-btn {
  background-color: #f1f5f9;
  color: #0f172a;
}

.share-btn {
  flex: 0 0 38px;
  background-color: #f1f5f9;
  color: #0f172a;
  padding: 0;
}

/* 选项卡 */
.content-tabs {
  background-color: #fff;
  display: flex;
  padding: 0 16px;
  border-bottom: 1px solid #f1f5f9;
}

.tab-item {
  padding: 12px 20px;
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.tab-label-box {
  display: flex;
  align-items: center;
  gap: 2px;
}

.tab-icon {
  margin-bottom: 1px;
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

/* 帖子列表 */
.post-feed {
  padding: 10px 16px;
}

.post-card {
  background-color: #fff;
  border-radius: 16px;
  padding: 16px;
  margin-bottom: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.02);
}

.post-text {
  font-size: 14px;
  color: #1e293b;
  line-height: 1.6;
}

.post-images {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
}

.img-wrapper {
  width: calc((100% - 16px) / 3);
  aspect-ratio: 1;
}

.img-content {
  width: 100%;
  height: 100%;
  border-radius: 8px;
  background-color: #f8fafc;
}

.post-footer {
  margin-top: 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.post-time {
  font-size: 12px;
  color: #94a3b8;
}

.post-actions {
  display: flex;
  gap: 16px;
}

.action-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.action-num {
  font-size: 12px;
  color: #64748b;
}

.liked {
  color: #ff0000;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding-top: 60px;
}

.empty-text {
  margin-top: 12px;
  font-size: 14px;
  color: #94a3b8;
}
</style>