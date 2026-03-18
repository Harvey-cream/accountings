<template>
  <view class="profile-container">
    <!-- 个人信息头部 -->
    <view class="profile-header-card" :style="{ paddingTop: (statusBarHeight + 10) + 'px' }">
      <view class="header-main">
        <view class="header-info-left">
          <view class="avatar-wrapper" @click="previewAvatar">
            <image class="avatar" :src="user.avatar" mode="aspectFill"></image>
            <view v-if="isSelf" class="plus-badge">
              <van-icon name="plus" size="12" color="#000" />
            </view>
          </view>
          <view class="header-right">
            <text class="user-name">{{ user.nickname || user.name }}</text>
            <view class="user-id-row">
              <text class="user-id">社交号: {{ user.accountId }}</text>
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
      <view class="bio-section" @click="handleBioClick">
        <text class="user-bio">{{ user.signature || '点击这里，填写简介' }}</text>
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
                <!-- 动态删除按钮 -->
                <view 
                  v-if="post.userId === loginUserId" 
                  class="action-item post-delete" 
                  @click.stop="handleDeletePost(post)"
                >
                  <van-icon name="delete-o" size="16" color="#94a3b8" />
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
          <!-- 主帖子内容 -->
          <view class="main-comment" v-if="selectedPost">
            <view class="comment-user-row">
              <image class="comment-avatar" :src="selectedPost.avatar || user.avatar" mode="aspectFill"></image>
              <view class="comment-user-info">
                <text class="comment-user-name">{{ selectedPost.name || user.nickname || user.name }}</text>
                <text class="comment-time">{{ selectedPost.time }}</text>
              </view>
            </view>
            <text class="comment-content">{{ selectedPost.text }}</text>
          </view>

          <!-- 分割线 -->
          <view class="comment-divider">全部评论 ({{ selectedPost?.comments || 0 }})</view>

          <!-- 真实评论列表 -->
          <view class="replies-list" v-if="selectedPost?.flattenedComments">
            <view v-for="(comment, index) in selectedPost.flattenedComments" :key="index" class="reply-item">
              <image class="reply-avatar" :src="comment.avatar || '/static/default_avatar.png'" mode="aspectFill"></image>
              <view class="reply-main">
                <view class="reply-header">
                  <view class="meta-left">
                    <text class="reply-user">{{ comment.author }}</text>
                    <block v-if="!comment.isRoot && comment.reply_to">
                      <text class="reply-text">></text>
                      <text class="reply-user">{{ comment.reply_to }}</text>
                    </block>
                  </view>
                  <!-- 删除按钮 -->
                  <view 
                    v-if="comment.authorId === loginUserId" 
                    class="delete-comment-btn"
                    @click.stop="handleDeleteComment(selectedPost, comment)"
                  >
                    <van-icon name="delete-o" size="14" color="#94a3b8" />
                  </view>
                </view>
                <text class="reply-content">{{ comment.content }}</text>
                <text class="reply-time">{{ comment.time }}</text>
              </view>
            </view>
          </view>
          
          <view v-else class="empty-replies">
            <text>暂无评论，快来抢沙发吧~</text>
          </view>
        </view>
      </scroll-view>
    </van-popup>
  </view>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import { onLoad, onShow } from '@dcloudio/uni-app';
import CapsuleButton from '@/components/CapsuleButton/CapsuleButton.vue';
import { getUserInfo, getPostList, publishComment, likePost, toggleFollow as toggleFollowApi, deleteComment, deletePost } from '@/api/api.js';

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
  accountId: '',
  name: '',
  nickname: '',
  avatar: '',
  signature: '',
  following: 0,
  followers: 0,
  likesAndCollects: 0,
  postsCount: 0,
  isFollowed: false
});

const userPosts = ref([]);

const currentUserId = ref('self');

const fetchUserPosts = async () => {
  try {
    const res = await getPostList({ userId: currentUserId.value });
    if (res.code === 0) {
      userPosts.value = res.data.map(post => {
        // 同样进行扁平化处理
        const allComments = [];
        post.realComments.forEach(root => {
          allComments.push({ ...root, isRoot: true });
          if (root.child_comments) {
            root.child_comments.forEach(child => {
              allComments.push({ ...child, isRoot: false, rootId: root.id });
            });
          }
        });
        return {
          ...post,
          flattenedComments: allComments,
          visibleCommentCount: 0
        };
      });
    }
  } catch (e) {
    console.error('获取帖子列表失败:', e);
  }
};

const fetchProfileData = async () => {
  try {
    const res = await getUserInfo(currentUserId.value);
    if (res.code === 0) {
      const data = res.data;
      currentUserId.value = data.userId; // 确保是真实的数字 ID
      user.accountId = data.accountId;
      user.name = data.username;
      user.nickname = data.nickname;
      user.avatar = data.avatarUrl || '/static/default_avatar.png';
      user.signature = data.signature || '';
      user.following = data.following || 0;
      user.followers = data.followers || 0;
      user.likesAndCollects = data.likesAndCollects || 0;
      user.isFollowed = data.isFollowed || false;
      isSelf.value = data.isSelf;

      fetchUserPosts();
    }
  } catch (e) {
    console.error('获取个人资料失败:', e);
  }
};

onShow(() => {
  fetchProfileData();
});

const loginUserId = ref(null);

onLoad((options) => {
  // 获取当前登录用户ID
  const session = uni.getStorageSync('session');
  if (session && session.user_info) {
    loginUserId.value = session.user_info.userId;
  }

  // 获取状态栏高度
  const systemInfo = uni.getSystemInfoSync();
  statusBarHeight.value = systemInfo.statusBarHeight || 0;

  if (options.userId) {
    currentUserId.value = options.userId;
  }
});

const openCommentDetail = (post) => {
  console.log('Open comment detail for post:', post.postId);
  selectedPost.value = post;
  showCommentPopup.value = true;
};

// 删除评论逻辑
const handleDeleteComment = (post, comment) => {
  uni.showModal({
    title: '提示',
    content: '确定要删除这条评论吗？',
    success: async (res) => {
      if (res.confirm) {
        try {
          const apiRes = await deleteComment(comment.id);
          if (apiRes.code === 0) {
            uni.showToast({ title: '删除成功', icon: 'none' });
            // 本地移除
            post.flattenedComments = post.flattenedComments.filter(c => c.id !== comment.id);
            post.comments--; // 评论数减1
          } else {
            uni.showToast({ title: apiRes.msg || '删除失败', icon: 'none' });
          }
        } catch (e) {
          console.error('删除评论失败:', e);
        }
      }
    }
  });
};

// 展开更多评论，每次展开5条
const expandComments = (post) => {
  post.visibleCommentCount += 5;
};

const openReplyInput = (post, comment = null) => {
  // 这里可以复用 community.vue 的回复逻辑，或者简单提示
  uni.showToast({ title: '暂不支持在此回复', icon: 'none' });
};

// 删除动态逻辑
const handleDeletePost = (post) => {
  uni.showModal({
    title: '提示',
    content: '确定要删除这条动态吗？',
    success: async (res) => {
      if (res.confirm) {
        try {
          const apiRes = await deletePost(post.postId);
          if (apiRes.code === 0) {
            uni.showToast({ title: '已删除', icon: 'none' });
            userPosts.value = userPosts.value.filter(p => p.postId !== post.postId);
          } else {
            uni.showToast({ title: apiRes.msg || '删除失败', icon: 'none' });
          }
        } catch (e) {
          console.error('删除动态失败:', e);
        }
      }
    }
  });
};

const goBack = () => {
  uni.navigateBack();
};

const handleBioClick = () => {
  if (isSelf.value && (!user.signature || user.signature.trim() === '')) {
    uni.navigateTo({
      url: '/pages/page_setting/setting_function/account_setting/account'
    });
  }
};

const toggleFollow = async () => {
  // 检查登录状态
  const session = uni.getStorageSync('session');
  if (!session || !session.user_info) {
    uni.showToast({ title: '请先登录', icon: 'none' });
    return;
  }
  
  const isFollow = !user.isFollowed;
  
  // 1. 立即更新 UI (乐观更新)
  user.isFollowed = isFollow;
  if (isFollow) {
    user.followers++;
    uni.showToast({ title: '已关注', icon: 'none' });
  } else {
    user.followers = Math.max(0, user.followers - 1);
    uni.showToast({ title: '已取消关注', icon: 'none' });
  }

  // 2. 记录初始状态 
  if (originalFollowState.value === undefined) {
    // 取反
    originalFollowState.value = !isFollow; 
  }

  // 3. 防抖处理
  if (followTimer) {
    clearTimeout(followTimer);
  }

  followTimer = setTimeout(async () => {
    const finalState = user.isFollowed;
    const initialState = originalFollowState.value;

    // 只有最终状态和最初状态不一致时，才发送请求
    if (finalState !== initialState) {
      try {
        const res = await toggleFollowApi(currentUserId.value, finalState);
        if (res.code !== 0) {
          // 失败回滚
          user.isFollowed = initialState;
          if (initialState) {
            user.followers++;
          } else {
            user.followers = Math.max(0, user.followers - 1);
          }
          uni.showToast({ title: res.msg || '操作失败', icon: 'none' });
        } else {
          // 同步最新的粉丝数
          if (res.data && res.data.followersCount !== undefined) {
            user.followers = res.data.followersCount;
          }
          // console.log(`同步关注状态成功: userId=${currentUserId.value}, isFollowed=${finalState}`);
        }
      } catch (e) {
        console.error('关注操作失败:', e);
        // 失败回滚
        user.isFollowed = initialState;
        if (initialState) {
          user.followers++;
        } else {
          user.followers = Math.max(0, user.followers - 1);
        }
      }
    } else {
      console.log(`状态无变化，无需同步: userId=${currentUserId.value}`);
    }

    // 清理记录的状态和定时器
    followTimer = null;
    originalFollowState.value = undefined;
  }, 1000); // 1秒防抖时间
};

let followTimer = null;
const originalFollowState = ref(undefined);

const likeTimers = {}; // 用于存储每个帖子的防抖定时器
const originalLikeState = {}; // 存储点击前的初始状态，用于对比是否需要发送请求

const toggleLike = (post) => {
  const postId = post.postId;
  
  // 1. 立即更新 UI (乐观更新)
  if (post.isLiked) {
    post.likes--;
    post.isLiked = false;
  } else {
    post.likes++;
    post.isLiked = true;
  }

  // 2. 记录初始状态
  if (originalLikeState[postId] === undefined) {
    // 取反
    originalLikeState[postId] = !post.isLiked; 
  }

  // 3. 防抖
  if (likeTimers[postId]) {
    clearTimeout(likeTimers[postId]);
  }

  likeTimers[postId] = setTimeout(async () => {
    const finalState = post.isLiked;
    const initialState = originalLikeState[postId];
    // 只有最终状态和最初点击时的状态不一致时，才发送请求
    if (finalState !== initialState) {
      try {
        await likePost(postId, finalState);
        console.log(`同步点赞状态成功: postId=${postId}, isLiked=${finalState}`);
      } catch (e) {
        console.error('同步点赞状态失败:', e);
      }
    } else {
      console.log(`状态无变化，无需同步: postId=${postId}`);
    }

    // 清理记录的状态和定时器
    delete likeTimers[postId];
    delete originalLikeState[postId];
  }, 1000); // 1秒防抖时间
};

const previewAvatar = () => {
  if (user.avatar && !user.avatar.includes('default_avatar')) {
    uni.previewImage({
      urls: [user.avatar],
      current: 0
    });
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
  uni.navigateTo({
    url: `/pages/page_social/social_follow/follow_list?userId=${currentUserId.value}&type=${type}`
  });
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

.comment-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1px;
}
.meta-left {
  display: flex;
  align-items: center;
  gap: 6px;
}
.delete-comment-btn {
  padding: 2px 4px;
}
.delete-comment-btn:active {
  opacity: 0.6;
}
.comment-author {
  font-size: 12px;
  font-weight: 700;
  color: #1e293b;
}
.reply-text {
  font-size: 11px;
  color: #94a3b8;
  font-weight: normal;
}
.comment-time {
  font-size: 10px;
  color: #94a3b8;
  margin-left: 4px;
}
.comment-content {
  font-size: 13px;
  color: #334155;
  line-height: 1.3;
}

.expand-comments-btn, .toggle-comments {
  margin-top: 8px;
  display: inline-block;
}

.expand-comments-btn text, .toggle-comments text {
  font-size: 13px;
  color: #64748b;
  font-weight: 500;
  background-color: #f8fafc;
  padding: 4px 10px;
  border-radius: 14px;
}

.expand-comments-btn:active text, .toggle-comments:active text {
  background-color: #f1f5f9;
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