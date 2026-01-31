<template>
  <view class="tabbar-container">
    <van-tabbar v-model="active" active-color="#DC5431" inactive-color="#94a3b8" @change="onChange" class="custom-tabbar" :border="false">
      <van-tabbar-item v-for="(item, index) in tabList" :key="index" :name="index" :class="{ 'fab-item': item.isFab }">
        <template #icon="props">
          <template v-if="item.isFab">
            <view class="fab-main">
              <van-icon name="plus" class="fab-icon" />
            </view>
          </template>
          <van-icon v-else :name="props.active ? item.selectedIcon : item.icon" />
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
  const target = tabList.value[index];
  
  // 特殊处理 Fab 按钮（记账）
  if (target.isFab) {
    // 1. 阻止选中状态变化：立即重置 active 为当前页面索引
    // 使用 nextTick 确保覆盖 Vant 的默认更新行为
    setTimeout(() => {
      active.value = getActiveIndex();
    }, 0);

    // 2. 执行跳转（通常是新页面，非 Tab 页）
    if (target.path) {
      uni.navigateTo({
        url: target.path,
        fail: (err) => {
          // 如果 navigateTo 失败（例如路径错误），尝试其他方式
          console.error('Navigation failed:', err);
          uni.switchTab({ url: target.path });
        }
      });
    }
    return;
  }

  // 普通 Tab 切换逻辑
  active.value = index; 
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
  transition: transform 0.15s cubic-bezier(0.34, 1.56, 0.64, 1); /* 弹性过渡效果 */
}

.fab-main:active {
  transform: scale(1.15); /* 点击时轻微放大 */
}

.fab-icon {
  font-size: 24px;
  color: #0f172a;
}

.fab-label {
  margin-top: 15px;
  color: #94a3b8;
}


</style>
