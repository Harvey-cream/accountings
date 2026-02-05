<template>
  <view class="community-container">
    <view class="header-section">
      <view class = "nav-header">
        <van-icon name="arrow-left" size="20" color="#0f172a" />
        <view class ="segment-control">
              <text v-for="(item,index) in period" :key="index" :class="['segment-item', { active: currentPeriod === index }]" @click="currentPeriod = index">{{ item }}</text>
        </view>
        <van-icon name="plus" size="20" color="#0f172a" @click="goToPublish" />
      </view>
    </view>

    <!-- 内容区：卡片 + 信息流 -->
    <view class="content-body">
      <view class="section-head">
        <text class="section-title">省钱妙招</text>
        <text class="section-more">查看更多</text>
      </view>

      <view class="tips-row">
        <view v-for="tip in tips" :key="tip.id" :class="['tip-card', tip.bg]">
          <view class="tip-icon">
            <van-icon :name="tip.icon" size="18" color="#fff" />
          </view>
          <text class="tip-name">{{ tip.title }}</text>
          <text class="tip-sub">{{ tip.sub }}</text>
        </view>
      </view>

      <view class="feed">
        <view v-for="post in filteredPosts" :key="post.id" class="post-card">
          <view class="post-head">
            <view class="post-info">
              <view class="avatar"></view>
              <view class="post-meta">
                <text class="post-name">{{ post.name }}</text>
                <text class="post-time">{{ post.time }}</text>
              </view>
            </view>
           <view class="head-actions">
            <view class="action post-comment" @click="showReplyInput(post.id)">
                <van-icon name="chat-o" size="18" color="#64748b" />
              </view>

              <view class="action post-like">
                <van-icon name="good-job-o" size="18" color="#64748b" />
                <text class="action-text">{{ post.likes }}</text>
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
              <view v-for="(comment, index) in (post.showAllComments ? post.realComments : post.realComments.slice(0, 2))" :key="index" class="comment-item" @click="showReplyInput(post.id, comment)">
                <view class="comment-header">
                  <view class="comment-avatar"></view>
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
          
          <!-- 分享按钮 -->
          <view class="post-actions">
            <view class="action">
              <van-icon name="share-o" size="18" color="#64748b" />
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
import { ref, computed } from 'vue';
import CustomTabbar from '@/components/Tabbar/Tabbar.vue';

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
    url: '/pages/page_discover/page_chatroom/chatroom'
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
    url: '/pages/page_discover/page_publish/publish'
  });
};

const period = ['热门推荐', '最新发布'];
const currentPeriod = ref(0);

const tips = [
  { id: 1, title: '超市扫货', sub: '省钱攻略', icon: 'cart-o', bg: 'bg-blue' },
  { id: 2, title: '特价机票', sub: '预订技巧', icon: 'guide-o', bg: 'bg-green' },
  { id: 3, title: '居家小常识', sub: '省钱日常', icon: 'wap-home-o', bg: 'bg-orange' }
];

const posts = ref([
    {
      id: 1,
      type: 0,
      name: '蒜打细算的小王',
      time: '2小时前',
      text: '今天在静安区发现一家超划算的咖啡折扣店！很多单品只要会员日1-3折。要买了这一堆才花了不到50块钱，感觉省了一个亿！',
      hasImages: true,
      images: ['/static/4.jpg', '/static/4.jpg', '/static/4.jpg'],
      likes: 128,
      comments: 24,
      showAllComments: false,
      realComments: [
        { author: '咖啡爱好者', time: '1小时前', content: '这家店具体在哪里啊？' },
        { author: '省钱小能手', time: '45分钟前', content: '周末也有折扣吗？' },
        { author: '住在附近', time: '30分钟前', content: '我也去过，确实很划算！' },
        { author: '小王回复住在附近', time: '20分钟前', content: '是的是的，老板人也很好' }
      ]
    },
    {
      id: 2,
      type: 1,
      name: '极简生活理财',
      time: '5小时前',
      text: '关于“薅羊毛”的一点心得：每天一杯30元的咖啡，一个月就是900元。坚持自己带咖啡豆手冲，不仅更有仪式感，一年能省下一张出国旅游的机票。',
      hasImages: false,
      likes: 86,
      comments: 12,
      showAllComments: false,
      realComments: [
        { author: '咖啡控', time: '4小时前', content: '我也想尝试手冲咖啡' },
        { author: '理财新手', time: '3小时前', content: '这个方法不错，值得借鉴' }
      ]
    }
  ]);

const filteredPosts = computed(() => {
  const list = posts.value;
  return currentPeriod.value === 1 ? [...list].reverse() : list;
});
</script>

<style scoped>
.community-container {
  background-color: #f5f5f5;
  min-height: 100vh;
  padding-bottom: 70px;
}
.header-section {
  background-color: #ffd541;
  padding: 10px 20px 20px;
}

.nav-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

/* 分段按钮 */
.segment-control {
  background-color: rgba(255, 255, 255, 0.3);
  border-radius: 20px;
  padding: 4px;
  display: flex;
}

.segment-item {
  padding: 6px 20px;
  border-radius: 16px;
  font-size: 13px;
  color: #0f172a;
  font-weight: 600;
}

.segment-item.active {
  background-color: #ffffff;
}

/* 内容区 */
.content-body {
    padding: 0 16px 16px;
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
  margin-top: 14px;
}

.post-card {
  background-color: #fff;
  border-radius: 18px;
  padding: 14px;
  margin-bottom: 14px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
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

.avatar {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  background: linear-gradient(135deg, #e2e8f0, #cbd5e1);
}

.post-meta {
  margin-left: 10px;
  display: flex;
  flex-direction: column;
}

.post-name {
  font-size: 13px;
  font-weight: 800;
  color: #0f172a;
}

.post-time {
  font-size: 11px;
  color: #94a3b8;
  margin-top: 2px;
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
    margin-top: 12px;
  }

  .img-outer {
    width: calc((100% - 16px) / 3);
    aspect-ratio: 1 / 1;
    border-radius: 10px;
    padding: 6px;
    box-sizing: border-box;
  }

  .img-inner {
    width: 100%;
    height: 100%;
    border-radius: 10px;
    border: 2px solid #e2e8f0;
    background: linear-gradient(135deg, #e5e7eb, #cbd5e1);
    object-fit: cover;
  }

.post-comments {
  margin-top: 12px;
  border-top: 1px solid #f1f5f9;
  padding-top: 12px;
}

.comment-list {
  margin-top: 8px;
}

.toggle-comments {
  text-align: center;
  margin: 8px 0;
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
  margin-bottom: 4px;
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
  line-height: 16px;
}

.post-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  margin-top: 8px;
  padding-top: 8px;
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
