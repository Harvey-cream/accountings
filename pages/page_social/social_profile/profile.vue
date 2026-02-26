<template>
  <view class="profile-container">
    <!-- 个人信息头部 -->
    <view class="profile-header-card" :style="{ paddingTop: (statusBarHeight + 10) + 'px' }">
      <view class="header-main">
        <view class="header-info-left">
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
        
        <!-- 头像行右上角的胶囊按钮 -->
        <view class="header-action-area">
          <CapsuleButton />
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
                <view class="action-item" @click.stop="openCommentDetail(post)">
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

    <!-- 评论详情弹窗 -->
    <van-popup
      v-model:show="showCommentPopup"
      position="bottom"
      round
      class="comment-popup"
      :style="{ height: '75%' }"
      @close="selectedPost = null"
    >
      <view class="popup-header">
        <text class="popup-title">评论详情</text>
        <van-icon name="cross" class="close-icon" @click="showCommentPopup = false" />
      </view>
      
      <scroll-view scroll-y class="popup-content">
        <view class="popup-scroll-inner">
          <!-- 主评论内容 -->
          <view class="main-comment" v-if="selectedPost">
            <view class="comment-user-row">
              <image class="comment-avatar" :src="user.avatar" mode="aspectFill"></image>
              <view class="comment-user-info">
                <text class="comment-user-name">{{ user.name }}</text>
                <text class="comment-time">{{ selectedPost.time }}</text>
              </view>
            </view>
            <text class="comment-content">{{ selectedPost.text }}</text>
          </view>

          <!-- 分割线 -->
          <view class="comment-divider">全部回复 ({{ mockReplies.length }})</view>

          <!-- 回复列表 -->
          <view class="replies-list">
            <view v-for="(reply, index) in mockReplies" :key="index" class="reply-item">
              <image class="reply-avatar" :src="reply.avatar" mode="aspectFill"></image>
              <view class="reply-body">
                <view class="reply-header">
                  <text class="reply-user">{{ reply.name }}</text>
                  <text class="reply-time">{{ reply.time }}</text>
                </view>
                <text class="reply-text">{{ reply.text }}</text>
              </view>
            </view>
          </view>
        </view>
      </scroll-view>
    </van-popup>
  </view>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import { onLoad } from '@dcloudio/uni-app';
import CapsuleButton from '@/components/CapsuleButton/CapsuleButton.vue';

const statusBarHeight = ref(0);
const isSelf = ref(true);
const currentTab = ref(0);
const showCommentPopup = ref(false);
const selectedPost = ref(null);

const tabs = [
  { name: '帖子' },
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

const mockReplies = ref([
  {
    name: '路人甲',
    avatar: '/static/1.jpg',
    time: '2小时前',
    text: '确实，这种方法坚持下来很有成就感！🙌'
  },
  {
    name: '理财小能手',
    avatar: '/static/2.jpg',
    time: '1小时前',
    text: '我每个月能省下500多呢，加油！'
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

const openCommentDetail = (post) => {
  selectedPost.value = post;
  showCommentPopup.value = true;
};

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
  background-color: #ffffff;
  min-height: 100vh;
}

/* 导航栏样式已移除 */
.nav-right {
  display: flex;
  align-items: center;
  gap: 15px;
}

.nav-icon {
  margin-left: 5px;
}

.edit-btn-pill {
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
  padding: 10px 16px 10px;
}

.header-main {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 20px;
}

.header-info-left {
  display: flex;
  align-items: center;
  gap: 15px;
}

.header-action-area {
  padding-top: 4px; /* 微调胶囊按钮高度，使其与头像顶部视觉对齐 */
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
  padding: 16px 0;
  border-bottom: 1px solid #f1f5f9;
}

/* 评论详情弹窗 */
.comment-popup {
  border-radius: 20px 20px 0 0;
  overflow-x: hidden;
}

.popup-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  border-bottom: 1px solid #f8fafc;
  width: 100%;
  box-sizing: border-box;
}

.popup-title {
  font-size: 16px;
  font-weight: 700;
  color: #0f172a;
}

.close-icon {
  font-size: 20px;
  color: #94a3b8;
  padding: 4px;
}

.popup-content {
  width: 100%;
  height: calc(100% - 54px); /* 减去 header 高度 */
  box-sizing: border-box;
}

.popup-scroll-inner {
  padding: 16px;
  width: 100%;
  box-sizing: border-box;
  overflow-x: hidden;
}

.main-comment {
  margin-bottom: 20px;
  width: 100%;
}

.comment-user-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 10px;
}

.comment-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
}

.comment-user-info {
  display: flex;
  flex-direction: column;
}

.comment-user-name {
  font-size: 14px;
  font-weight: 600;
  color: #0f172a;
}

.comment-time {
  font-size: 12px;
  color: #94a3b8;
}

.comment-content {
  font-size: 15px;
  color: #1e293b;
  line-height: 1.6;
  word-break: break-all;
  white-space: pre-wrap;
}

.comment-divider {
  font-size: 13px;
  font-weight: 600;
  color: #64748b;
  margin: 20px 0 15px;
}

.reply-item {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.reply-avatar {
  width: 30px;
  height: 30px;
  border-radius: 50%;
}

.reply-body {
  flex: 1;
}

.reply-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.reply-user {
  font-size: 13px;
  font-weight: 600;
  color: #475569;
}

.reply-time {
  font-size: 11px;
  color: #94a3b8;
}

.reply-text {
  font-size: 14px;
  color: #334155;
  line-height: 1.5;
  word-break: break-all;
  white-space: pre-wrap;
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