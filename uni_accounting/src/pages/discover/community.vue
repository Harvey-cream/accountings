<template>
  <view class="community-container" :class="currentThemeClass" @click="closeDropdown">
    <view class="header-section">
      <view class="nav-header">
        <view class="header-left" @click.stop="toggleDropdown">
          <van-icon :name="showCustomDropdown ? 'arrow-down' : 'arrow'" size="18" color="#0f172a" />
          
          <!-- 自定义下拉框 -->
          <view v-if="showCustomDropdown" class="custom-dropdown">
            <view 
              v-for="(item, index) in period" 
              :key="index" 
              class="dropdown-item" 
              :class="{ active: currentPeriod === index }"
              @click.stop="selectPeriod(index)"
            >
              <view class="item-text-box">
                <text>{{ item }}</text>
              </view>
              <view class="item-icon-box" v-if="currentPeriod === index">
                <van-icon name="success" size="14" color="#ffd541" />
              </view>
            </view>
          </view>
        </view>
        
        <view class="dropdown-wrapper">
          <text class="segment-title">{{ period[currentPeriod] }}</text>
        </view>

        <view class="header-right">
          <van-icon name="plus" size="20" color="#0f172a" @click="goToPublish" />
        </view>
      </view>
    </view>

    <!-- 内容区：卡片 + 信息流 -->
    <view class="content-body">
      <view class="feed">
        <view v-for="post in filteredPosts" :key="post.postId" :id="'post-' + post.postId" :class="['post-card', { 'highlight-post': post.isHighlighted }]">
          <view class="post-left" @click="goToProfile(post.userId)">
            <view class="avatar">
              <image v-if="post.avatar" :src="post.avatar" mode="aspectFill" class="avatar-img" />
            </view>
          </view>

          <view class="post-right">
            <view class="post-head">
              <view class="post-meta" @click="goToProfile(post.userId)">
                <text class="post-name">{{ post.name }}</text>
                <view class="post-time-box">
                  <text class="post-time">{{ post.time }}</text>
                  <text v-if="post.location" class="post-location"> · {{ post.location }}</text>
                </view>
              </view>
              <view class="head-actions">
                <view class="action post-comment" @click="showReplyInput(post.postId)">
                  <van-icon name="chat-o" size="18" color="#64748b" />
                </view>

                <view class="action post-like" @click="toggleLike(post)">
                  <van-icon :name="post.isLiked ? 'good-job' : 'good-job-o'" size="18" :color="post.isLiked ? '#ff0000' : '#64748b'" />
                  <text class="action-text" :class="{ 'liked-text': post.isLiked }">{{ post.likes }}</text>
                </view>
              </view>
            </view>

            <text class="post-text">{{ post.text }}</text>

            <view v-if="post.hasImages" class="post-images">
              <view v-for="(image, index) in post.images" :key="index" class="img-outer" @click="previewImage(post.images, index)">
                <image :src="image" class="img-inner"></image>
              </view>
            </view>

            <!-- 评论区 -->
            <view class="post-comments">
              <!-- 评论列表 -->
              <view class="comment-list">
                <!-- 显示评论（最多3条，或全部） -->
                <view v-for="(comment, index) in (post.showAllComments ? post.realComments : post.realComments.slice(0, 2))" :key="index" class="comment-item" @click="showReplyInput(post.postId, comment)">
                  <view class="comment-header">
                    <view class="comment-avatar">
                      <image v-if="comment.avatar" :src="comment.avatar" mode="aspectFill" class="avatar-img" />
                    </view>
                    <view class="comment-main">
                      <view class="comment-meta">
                        <text class="comment-author">{{ comment.author }}</text>
                        <text class="comment-time">{{ comment.time }}</text>
                      </view>
                      <text class="comment-content">{{ comment.content }}</text>
                    </view>
                  </view>
                </view>
              </view>
              <view v-if="post.realComments.length > 2" class="toggle-comments" @click="post.showAllComments = !post.showAllComments">
                <text>{{ post.showAllComments ? '收起' : `查看全部 ${post.realComments.length} 条评论` }}</text>
              </view>
            </view>
          </view>
        </view>
      </view>
    </view>

    <custom-tabbar />

    <!-- 聊天室悬浮入口 -->
    <view class="floating-chat-entry" @click="goToChatroom">
      <van-icon name="chat-o" size="20" color="#333" />
      <view class="unread-dot">9</view>
    </view>

    <!-- 浮动回复输入框 -->
    <view v-if="replyPost !== null" class="floating-reply-container">
      <input
        v-model="replyContent"
        class="floating-reply-input"
        :placeholder="replyComment ? `回复 @${replyComment.author}...` : '写下你的回复...'"
        @confirm="submitReply(replyPost)"
        auto-focus
      />
      <view class="floating-reply-send" @click="submitReply(replyPost)">
        <van-icon name="guide-o" size="20" color="#333" />
      </view>
      <view class="floating-reply-close" @click="hideReplyInput">
        <van-icon name="cross" size="20" color="#64748b" />
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, computed, nextTick } from 'vue';
import { onShow, onLoad } from '@dcloudio/uni-app';
import CustomTabbar from '@/components/Tabbar/Tabbar.vue';
import { getPostList } from '@/api/api.js';

onShow(() => {
	uni.$emit('updateTabbar');
  fetchPosts();
});

const posts = ref([]);

const fetchPosts = async () => {
  try {
    const res = await getPostList({ type: currentPeriod.value });
    if (res.code === 0) {
      posts.value = res.data;
    }
  } catch (e) {
    console.error('获取动态列表失败:', e);
  }
};

onLoad((options) => {
  if (options.postId) {
    nextTick(() => {
      setTimeout(() => {
        uni.pageScrollTo({
          selector: `#post-${options.postId}`,
          duration: 300
        });
        
        // 可选：高亮一下对应的帖子
         const post = posts.value.find(p => p.postId == options.postId);
         if (post) {
           post.isHighlighted = true;
           setTimeout(() => {
             post.isHighlighted = false;
           }, 2000);
         }
       }, 500); // 稍微延迟确保渲染完成
     });
   }
});

const previewImage = (images, index) => {
  uni.previewImage({
    urls: images,
    current: index
  });
};

const replyPost = ref(null);
const replyComment = ref(null);
const replyContent = ref('');

const showReplyInput = (postId, comment = null) => {
  replyPost.value = postId;
  replyComment.value = comment;
  replyContent.value = '';
};

const hideReplyInput = () => {
  replyPost.value = null;
  replyComment.value = null;
  replyContent.value = '';
};

const goToChatroom = () => {
  uni.navigateTo({
    url: '/pages/discover/page_chatroom/chatroom'
  });
};

const goToProfile = (userId) => {
  uni.navigateTo({
    url: `/pages/page_social/social_profile/profile?userId=${userId}`
  });
};

const submitReply = (postId) => {
  if (!replyContent.value.trim()) return;

  if (replyComment.value) {
    // 回复特定评论
    console.log('回复评论:', replyComment.value.author, '内容:', replyContent.value);
  } else {
    // 回复帖子
    console.log('回复帖子:', replyContent.value);
  }

  hideReplyInput();
};

// 跳转到发布动态页面
const goToPublish = () => {
  uni.navigateTo({
    url: '/pages/discover/page_publish/publish'
  });
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

const period = ['热门推荐', '最新发布', '我的关注'];
const currentPeriod = ref(0);
const showCustomDropdown = ref(false);

const toggleDropdown = () => {
  showCustomDropdown.value = !showCustomDropdown.value;
};

const closeDropdown = () => {
  showCustomDropdown.value = false;
};

const selectPeriod = (index) => {
  currentPeriod.value = index;
  showCustomDropdown.value = false;
  fetchPosts();
};

const tips = [
  { id: 1, title: '超市扫货', sub: '省钱攻略', icon: 'cart-o', bg: 'bg-blue' },
  { id: 2, title: '特价机票', sub: '预订技巧', icon: 'guide-o', bg: 'bg-green' },
  { id: 3, title: '居家小常识', sub: '省钱日常', icon: 'wap-home-o', bg: 'bg-orange' }
];

const filteredPosts = computed(() => {
  return posts.value;
});
</script>

<style scoped>
.community-container {
  background-color: #ffffff;  
  min-height: 100vh;
  padding-bottom: 70px;
}
.header-section {
  background-color: #ffd541;
  padding: 10px 20px 10px;
}

.nav-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  position: relative;
}



.dropdown-wrapper {
  flex: 1;
  display: flex;
  justify-content: center;
}

.segment-title {
  font-size: 16px;
  font-weight: 500;
  color: #0f172a;
}

/* 自定义下拉菜单 */
.custom-dropdown {
  position: absolute;
  top: 35px;
  left: -18px;
  width: 120px;
  background-color: #ffffff;
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
  z-index: 1000;
  overflow: hidden;
  padding: 4px 0;
}

.dropdown-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  font-size: 14px;
  color: #334155;
  transition: background-color 0.2s;
}

.item-text-box {
  margin-right: 10px;
}

.item-icon-box {
  display: flex;
  align-items: center;
}

:deep(.van-dropdown-menu__title) {
  padding: 0 !important;
  line-height: 1 !important;
}


/* 内容区 */
.content-body {
    padding: 0 16px 0px;
}

.section-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin: 12px 4px 12px;
}

.section-title {
  font-size: 16px;
  font-weight: 800;
  color: #0f172a;
}

.section-more {
  font-size: 12px;
  color: #64748b;
}

.tips-row {
  display: flex;
  gap: 12px;
}

.tip-card {
  flex: 1;
  border-radius: 16px;
  padding: 14px 14px 12px;
  color: #fff;
  min-height: 88px;
}

.tip-icon {
  width: 28px;
  height: 28px;
  border-radius: 10px;
  background-color: rgba(255, 255, 255, 0.22);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 10px;
}

.tip-name {
  font-size: 13px;
  font-weight: 800;
  display: block;
}

.tip-sub {
  font-size: 11px;
  opacity: 0.9;
  display: block;
  margin-top: 2px;
}

.bg-blue { background-color: #3b82f6; }
.bg-green { background-color: #10b981; }
.bg-orange { background-color: #f97316; }

.feed {
  margin-top: 6px;
}

.post-card {
  padding: 10px 0px;
  margin-bottom: 10px;
  display: flex;
  gap: 4px;
  transition: background-color 0.5s ease;
}

.highlight-post {
  background-color: #fff9db !important;
}

.post-left {
  flex-shrink: 0;
}

.post-right {
  flex: 1;
  min-width: 0;
}

.post-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.post-info {
  display: flex;
  align-items: center;
}

.head-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.post-like, .post-comment {
  display: flex;
  align-items: center;
  gap: 4px;
}

.post-like .action-text, .post-comment .action-text {
  font-size: 12px;
  color: #64748b;
}

.liked-text {
  color: #ff0000 !important;
}

.avatar {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  background: linear-gradient(135deg, #e2e8f0, #cbd5e1);
  overflow: hidden;
}

.avatar-img {
  width: 100%;
  height: 100%;
}

.post-meta {
  display: flex;
  flex-direction: column;
}

.post-name {
  font-size: 13px;
  font-weight: 800;
  color: #0f172a;
}

.post-time-box {
  display: flex;
  align-items: center;
  margin-top: 2px;
}

.post-time {
  font-size: 11px;
  color: #94a3b8;
}

.post-location {
  font-size: 11px;
  color: #64748b;
  margin-left: 4px;
}

.post-text {
  margin-top: 10px;
  font-size: 13px;
  color: #334155;
  line-height: 18px;
}

.post-images {
    display: flex;
    flex-wrap: wrap;
    gap: 2px;
    margin-top: 5px;
  }

  .img-outer {
    width: calc((100% - 16px) / 3);
    aspect-ratio: 1 / 1;
    border-radius: 10px;
    padding: 2px;
    box-sizing: border-box;
  }

  .img-inner {
    width: 100%;
    height: 100%;
    border-radius: 8px; 
    border: 1px solid #f1f5f9; 
    background: linear-gradient(135deg, #f8fafc, #f1f5f9); 
    object-fit: cover;
  }


.comment-list {
  margin-top: 8px;
}

.toggle-comments {
  text-align: center;
}

.toggle-comments text {
  font-size: 12px;
  color: #64748b;
}

.comment-item {
  margin-bottom: 12px;
}

.comment-header {
  display: flex;
  align-items: flex-start;
  gap: 8px;
}

.comment-avatar {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  background: linear-gradient(135deg, #e2e8f0, #cbd5e1);
  flex-shrink: 0;
}

.comment-main {
  flex: 1;
}

.comment-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}

.comment-author {
  font-size: 12px;
  font-weight: 700;
  color: #0f172a;
}

.comment-time {
  font-size: 10px;
  color: #94a3b8;
}

.comment-content {
  font-size: 12px;
  color: #334155;
}

.post-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  border-top: 1px solid #f1f5f9;
}

.action {
  display: flex;
  align-items: center;
  gap: 6px;
}

/* 浮动回复输入框样式 */
.floating-reply-container {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: #fff;
  border-top: 1px solid #e2e8f0;
  padding: 10px;
  display: flex;
  align-items: center;
  gap: 8px;
  z-index: 999;
}

.floating-reply-input {
  flex: 1;
  padding: 10px;
  border: 1px solid #e2e8f0;
  border-radius: 20px;
  outline: none;
  font-size: 14px;
}

.floating-reply-send {
  width: 36px;
  height: 36px;
  background-color: #ffd541;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.floating-reply-close {
  padding: 5px;
  cursor: pointer;
}

.reply-to-info {
  position: absolute;
  top: -20px;
  left: 10px;
  font-size: 12px;
  color: #64748b;
}

/* 聊天室悬浮入口样式 */
.floating-chat-entry {
  position: fixed;
  bottom: 90px;
  right: 16px;
  width: 42px;
  height: 42px;
  background-color: #ffd541;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 16px rgba(255, 213, 65, 0.5);
  z-index: 98;
  transition: transform 0.2s;
}

.floating-chat-entry:active {
  transform: scale(0.95);
}

.unread-dot {
  position: absolute;
  top: -2px;
  right: -2px;
  background-color: #ef4444;
  color: #fff;
  font-size: 11px;
  font-weight: 600;
  min-width: 18px;
  height: 18px;
  border-radius: 9px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px solid #fff;
  padding: 0 4px;
  box-sizing: border-box;
}
</style>
