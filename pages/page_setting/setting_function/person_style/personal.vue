<template>
  <view class="container" :class="currentThemeClass">
    <!-- 导航栏 -->
    <view class="nav-bar">
      <view class="nav-left" @click="goBack">
        <van-icon name="arrow-left" size="20" />
        <text class="nav-title">返回</text>
      </view>
      <text class="page-title">个性装扮</text>
      <view class="nav-right"></view>
    </view>

    <scroll-view scroll-y class="content-body">
      
      <view class="theme-grid">
        <view 
          v-for="theme in themes" 
          :key="theme.id" 
          class="theme-card"
          @click="selectTheme(theme)"
        >
          <view class="theme-preview" :style="{ background: theme.previewBackground }">
            <view v-if="currentTheme === theme.id" class="selected-badge">
              <van-icon name="success" color="#fff" size="12" />
            </view>
          </view>
          <view class="theme-info">
            <text class="theme-name">{{ theme.name }}</text>
          </view>
        </view>
      </view>
    </scroll-view>
  </view>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useTheme } from '@/pages/store/theme';

const { selectTheme: setTheme } = useTheme();

const themes = [
  { id: 'yellow', name: '默认', class: 'theme-yellow', previewBackground: '#ffd541' },
  { id: 'orange', name: '火焰橙', class: 'theme-orange', previewBackground: 'linear-gradient(135deg, #ff9a9e 0%, #fecfef 99%, #fecfef 100%)' },
  { id: 'green', name: '琉璃绿', class: 'theme-green', previewBackground: 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)' },
  { id: 'purple', name: '青莲紫', class: 'theme-purple', previewBackground: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' },
  { id: 'red', name: '樱绯红', class: 'theme-red', previewBackground: 'linear-gradient(135deg, #ff0844 0%, #ffb199 100%)' },
  { id: 'blue', name: '晴空蓝', class: 'theme-blue', previewBackground: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)' },
  { id: 'forest', name: '林间月', class: 'theme-green', previewBackground: 'linear-gradient(to top, #d299c2 0%, #fef9d7 100%)' },
  { id: 'desert', name: '黄昏沙丘', class: 'theme-orange', previewBackground: 'linear-gradient(to top, #fad0c4 0%, #ffd1ff 100%)' }
];

const currentTheme = ref('yellow');

onMounted(() => {
  const savedTheme = uni.getStorageSync('theme');
  if (savedTheme) {
    currentTheme.value = savedTheme;
  }
});

const goBack = () => {
  uni.navigateTo({
    url: '/pages/page_setting/setting'
  });
};

const selectTheme = (theme) => {
  currentTheme.value = theme.id;
  setTheme(theme.id, theme.class);
  uni.showToast({
    title: `已切换至${theme.name}`,
    icon: 'success'
  });
};
</script>

<style scoped>
.container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: #f8fafc;
}

.content-body {
  flex: 1;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 16px;
  padding-left: 4px;
}

.theme-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  padding: 10px;
}

.theme-card {
  background-color: #ffffff;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  transition: transform 0.2s;
}

.theme-card:active {
  transform: scale(0.98);
}

.theme-preview {
  height: 100px;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}

.selected-badge {
  position: absolute;
  top: 8px;
  right: 8px;
  width: 20px;
  height: 20px;
  background-color: #4cd964;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px solid #fff;
}

.theme-info {
  padding: 12px;
  text-align: center;
}

.theme-name {
  font-size: 14px;
  color: #334155;
  font-weight: 500;
}

/* 隐藏滚动条 */
::-webkit-scrollbar {
  display: none;
  width: 0;
  height: 0;
  color: transparent;
}
</style>