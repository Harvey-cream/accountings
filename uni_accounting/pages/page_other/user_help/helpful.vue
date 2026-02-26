<template>
  <view class="help-container" :class="currentThemeClass">
    <!-- 导航栏 -->
    <view class="header-section">
      <view class="nav-header">
        <van-icon name="arrow-left" size="20" color="#0f172a" @click="goBack" />
        <view class="page-title">使用帮助</view>
        <view class="nav-placeholder"></view>
      </view>
    </view>

    <!-- 搜索栏 -->
    <view class="search-section">
      <view class="search-bar">
        <van-icon name="search" size="18" color="#94a3b8" />
        <input 
          type="text" 
          v-model="searchQuery" 
          placeholder="搜索您遇到的问题" 
          class="search-input"
        />
      </view>
    </view>

    <!-- 帮助列表 -->
    <scroll-view scroll-y class="content-body">
      <view class="help-list">
        <view 
          v-for="(item, index) in filteredHelpList" 
          :key="index" 
          class="help-item"
          @click="showDetail(item)"
        >
          <view class="item-main">
            <text class="item-number">{{ item.id }}</text>
            <text class="item-question">{{ item.question }}</text>
          </view>
          <van-icon name="arrow" size="16" color="#cbd5e1" />
        </view>
      </view>
      
      <!-- 无搜索结果提示 -->
      <view v-if="filteredHelpList.length === 0" class="empty-state">
        <van-icon name="info-o" size="48" color="#e2e8f0" />
        <text class="empty-text">未找到相关问题</text>
      </view>
    </scroll-view>

    <!-- 问题详情弹窗 -->
    <van-popup
      v-model:show="showPopup"
      position="bottom"
      round
      :style="{ height: '60%' }"
    >
      <view class="popup-content">
        <view class="popup-header">
          <text class="popup-title">问题详情</text>
          <van-icon name="cross" size="20" color="#94a3b8" @click="showPopup = false" />
        </view>
        <view class="popup-body">
          <view class="detail-question">{{ activeItem.question }}</view>
          <view class="detail-answer">{{ activeItem.answer }}</view>
        </view>
      </view>
    </van-popup>
  </view>
</template>

<script setup>
import { ref, computed } from 'vue';

const searchQuery = ref('');
const showPopup = ref(false);
const activeItem = ref({});

const helpList = ref([
  { id: '1.1', question: '忘记登录密码怎么办？', answer: '您可以在登录页面点击“忘记密码”，通过绑定的手机号或应急邮箱进行身份验证并重置密码。' },
  { id: '1.2', question: '忘记手势密码怎么办？', answer: '连续输入错误 5 次后，系统将提示您使用登录密码进行验证，验证成功后可重新设置手势密码。' },
  { id: '1.3', question: '小龙记账支持哪些登录方式？', answer: '目前支持手机验证码登录、账号密码登录以及微信授权一键登录。' },
  { id: '1.4', question: '如何提升自己的账号安全性？', answer: '建议您开启手势密码，并绑定应急手机号和邮箱，同时定期修改登录密码。' },
  { id: '1.5', question: '如何退出登录？', answer: '在“我的”页面点击右上角设置图标，拉到最底部即可看到“退出登录”按钮。' },
  { id: '1.6', question: '如何切换账号登录？', answer: '需先在设置页面退出当前账号，然后在登录页输入新账号信息进行登录。' },
  { id: '1.7', question: '可以在多个设备上登录同一账号吗？', answer: '支持。小龙记账提供云端同步功能，您可以在多台手机或平板上登录同一账号，数据会自动同步。' },
  { id: '1.8', question: '手机号/微信号绑定问题', answer: '您可以在“设置 -> 账号设置”中查看和修改当前绑定的手机号或微信号。' },
  { id: '1.9', question: '手机号无法接收验证码怎么办？', answer: '请检查网络信号是否正常，或查看是否被手机安全软件拦截。若多次尝试未果，请联系客服处理。' },
  { id: '1.10', question: '如何注销账号？', answer: '在“设置 -> 账号设置”最底部有“注销账号”入口，请在注销前确保备份好重要数据。' },
  { id: '2.1', question: '如何添加更多记账类别？', answer: '在“设置 -> 类别设置”中，您可以自定义添加、删除或排序支出和收入的分类图标。' },
  { id: '2.2', question: '如何设置预算？', answer: '在“首页”点击“预算”模块，或在“个人中心”进入“预算中心”，即可设置每月预算额度。' }
]);

const filteredHelpList = computed(() => {
  if (!searchQuery.value.trim()) return helpList.value;
  return helpList.value.filter(item => 
    item.question.includes(searchQuery.value) || 
    item.id.includes(searchQuery.value)
  );
});

const goBack = () => {
  uni.navigateBack();
};

const showDetail = (item) => {
  activeItem.value = item;
  showPopup.value = true;
};
</script>

<style scoped>
.help-container {
  background-color: #ffffff;
  width: 100%;
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow-x: hidden;
  box-sizing: border-box;
}

.help-container * {
  box-sizing: border-box;
}

.header-section {
  background-color: var(--main-color);
  padding: calc(var(--status-bar-height) + 10px) 16px 0px;
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

/* 搜索栏 */
.search-section {
  padding: 16px;
  background-color: var(--main-color);
}

.search-bar {
  display: flex;
  align-items: center;
  background-color: #ffffff;
  padding: 10px 16px;
  border-radius: 12px;
  gap: 10px;
}

.search-input {
  flex: 1;
  font-size: 14px;
  color: #1e293b;
}

/* 内容列表 */
.content-body {
  flex: 1;
  padding: 0 16px;
}

.help-list {
  margin-top: 10px;
}

.help-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 18px 0;
  border-bottom: 1px solid #f1f5f9;
}

.help-item:active {
  opacity: 0.7;
}

.item-main {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
  padding-right: 10px;
}

.item-number {
  font-size: 14px;
  color: #94a3b8;
  font-weight: 500;
  min-width: 32px;
}

.item-question {
  font-size: 15px;
  color: #334155;
}

/* 空状态 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding-top: 100px;
  gap: 16px;
}

.empty-text {
  font-size: 14px;
  color: #94a3b8;
}

/* 详情弹窗 */
.popup-content {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.popup-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px;
  border-bottom: 1px solid #f1f5f9;
}

.popup-title {
  font-size: 18px;
  font-weight: 700;
  color: #1e293b;
}

.popup-body {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
}

.detail-question {
  font-size: 18px;
  font-weight: 700;
  color: #1e293b;
  margin-bottom: 16px;
  line-height: 1.4;
}

.detail-answer {
  font-size: 15px;
  color: #64748b;
  line-height: 1.8;
}

/* 隐藏滚动条 */
::-webkit-scrollbar {
  display: none;
  width: 0;
  height: 0;
  color: transparent;
}
</style>