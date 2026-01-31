<template>
  <view class="tabbar-container">
    <van-tabbar v-model="active" active-color="#DC5431" inactive-color="#94a3b8" @change="onChange" class="custom-tabbar" :border="false">
      <van-tabbar-item v-for="(item, index) in tabList" :key="index" :name="index" :class="{ 'fab-item': item.isFab }">
        <template #icon>
          <template v-if="item.isFab">
            <view class="fab-main">
              <van-icon name="plus" class="fab-icon" />
            </view>
          </template>
          <van-icon v-else :name="item.icon" />
        </template>
        <text :class="['nav-name', { 'fab-label': item.isFab }]">{{ item.text }}</text>
      </van-tabbar-item>
    </van-tabbar>
  </view>
</template>

<script setup>
import { ref, onMounted } from 'vue';

const tabList = ref(uni.getStorageSync('tabList') || []);

// 初始化当前页面索引的逻辑封装
const getActiveIndex = () => {
  const pages = getCurrentPages();
  if (pages.length > 0) {
    const currentPage = pages[pages.length - 1];
    const path = '/' + currentPage.route;
    const index = tabList.value.findIndex(item => item.path === path);
    return index !== -1 ? index : 0;
  }
  return 0;
};

// 直接初始化为正确索引，不再需要 -1 过渡
const active = ref(getActiveIndex()); 

const onChange = (index) => {
  active.value = index; // 立即改变本地状态，增强反馈感
  const target = tabList.value[index];
  if (target && target.path) {
    uni.switchTab({
      url: target.path,
      fail: (err) => {
        uni.navigateTo({
          url: target.path,
          fail: (err2) => {
            uni.reLaunch({ url: target.path });
          }
        });
      }
    });
  }
};

onMounted(() => {
  // 监听更新事件
  uni.$on('updateTabbar', () => {
    tabList.value = uni.getStorageSync('tabList') || [];
    active.value = getActiveIndex();
  });
});
</script>

<style scoped>
.tabbar-container {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 999;
}

.custom-tabbar {
  height: 60px;
  background-color: #fefbf2 !important;
}

.nav-name {
  font-size: 10px;
  margin-top: 4px;
}

/* FAB Styles */
.fab-item {
  position: relative;
}

.fab-main {
  width: 50px;
  height: 50px;
  background-color: #FFD541;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-top: -45px;
  box-shadow: 0 4px 10px rgba(255, 213, 65, 0.4);
  border: 4px solid #fefbf2;
}

.fab-icon {
  font-size: 24px;
  color: #0f172a;
}

.fab-label {
  margin-top: 15px;
  color: #94a3b8;
}

:deep(.van-tabbar-item--active) .fab-label {
  color: #DC5431;
}
</style>
