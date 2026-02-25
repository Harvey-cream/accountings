import { ref, onMounted, onUnmounted } from 'vue';

// 全局响应式变量，所有引用此 store 的组件将共用此状态
const currentThemeClass = ref('theme-yellow');

export const useTheme = () => {
  const updateTheme = () => {
    const savedTheme = uni.getStorageSync('theme') || 'yellow';
    currentThemeClass.value = 'theme-' + savedTheme;
  };

  const selectTheme = (themeId, themeClass) => {
    currentThemeClass.value = themeClass;
    uni.setStorageSync('theme', themeId);
    // 同时通过全局事件通知其他已挂载的组件（可选，因为 currentThemeClass 已经是全局响应式的）
    uni.$emit('themeChange', themeClass);
  };

  const initTheme = () => {
    updateTheme();
    // 监听全局事件，用于非 store 引用的组件同步（如果存在的话）
    uni.$on('themeChange', (themeClass) => {
      currentThemeClass.value = themeClass;
    });
  };

  const cleanupTheme = () => {
    uni.$off('themeChange');
  };

  return {
    currentThemeClass,
    updateTheme,
    selectTheme,
    initTheme,
    cleanupTheme
  };
};

// 导出全局混入配置
export const themeMixin = {
  computed: {
    currentThemeClass() {
      // 访问全局 ref
      return currentThemeClass.value;
    }
  },
  onShow() {
    // 每次页面显示时更新一次主题（确保从缓存同步）
    const savedTheme = uni.getStorageSync('theme') || 'yellow';
    currentThemeClass.value = 'theme-' + savedTheme;
  }
};
