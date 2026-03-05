<template>
  <view class="category-container" :class="currentThemeClass">
    <!-- 导航栏 -->
    <view class="nav-bar">
      <view class="nav-left" @click="goBack">
        <van-icon name="arrow-left" size="20" color="#1e293b" />
        <text class="nav-title">返回</text>
      </view>
      <text class="page-title">类别设置</text>
      <view class="nav-right"></view>
    </view>

    <!-- 支出/收入切换 -->
    <view class="tab-section">
      <view class="tab-group">
        <view 
          v-for="(item, index) in tabs" 
          :key="index"
          class="tab-item"
          :class="{ active: currentTab === index }"
          @click="currentTab = index"
        >
          {{ item }}
        </view>
      </view>
    </view>

    <!-- 类别列表 -->
    <scroll-view scroll-y class="content-body">
      <view class="category-list">
        <view v-for="(item, index) in currentCategories" :key="item.id" class="category-row">
          <view class="remove-btn" @click="removeCategory(index)">
            <van-icon name="clear" color="#ef4444" size="22" />
          </view>
          <view class="icon-box">
            <van-icon :name="item.icon" size="20" color="#64748b" />
          </view>
          <text class="category-name">{{ item.name }}</text>
          <view class="drag-handle">
            <van-icon name="wap-nav" color="#cbd5e1" size="20" />
          </view>
        </view>
      </view>
    </scroll-view>

    <!-- 底部添加按钮 -->
    <view class="footer-action" @click="openAddPopup">
      <van-icon name="plus" size="18" color="#64748b" />
      <text class="add-text">添加类别</text>
    </view>

    <!-- 添加类别弹窗 -->
    <van-popup
      v-model:show="showAddPopup"
      position="bottom"
      round
      :style="{ height: '85%' }"
      class="add-popup"
    >
      <view class="popup-content">
        <view class="popup-header">
          <text class="popup-title">新增{{ tabs[currentTab] }}类别</text>
          <van-icon name="cross" size="20" color="#94a3b8" @click="showAddPopup = false" />
        </view>

        <view class="input-section">
          <view class="selected-icon-box">
            <van-icon :name="newCategory.icon" size="24" color="#1e293b" />
          </view>
          <input 
            v-model="newCategory.name"
            class="name-input"
            placeholder="请输入类别名(最多4字)"
            maxlength="4"
          />
        </view>

        <view class="icon-selector">
          <text class="selector-label">选择图标</text>
          <scroll-view scroll-y class="icon-grid-scroll">
            <view class="icon-grid">
              <view 
                v-for="icon in filteredAvailableIcons" 
                :key="icon"
                class="icon-item"
                :class="{ active: newCategory.icon === icon }"
                @click="newCategory.icon = icon"
              >
                <van-icon :name="icon" size="24" />
              </view>
            </view>
          </scroll-view>
        </view>

        <view class="confirm-btn-container">
          <view class="confirm-btn" @click="confirmAdd">确定</view>
        </view>
      </view>
    </van-popup>
  </view>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { getAllIcons } from '@/api/api.js';

const tabs = ['支出', '收入'];
const currentTab = ref(0);
const showAddPopup = ref(false);

// 初始数据
const categories = ref({
  0: [ // 支出
    { id: 1, name: '餐饮', icon: 'shop-o' },
    { id: 2, name: '购物', icon: 'bag-o' },
    { id: 3, name: '日用', icon: 'brush-o' },
    { id: 4, name: '交通', icon: 'logistics' },
    { id: 5, name: '蔬菜', icon: 'flower-o' },
    { id: 6, name: '水果', icon: 'cluster-o' },
    { id: 7, name: '零食', icon: 'cake' }
  ],
  1: [ // 收入
    { id: 101, name: '工资', icon: 'gold-coin-o' },
    { id: 102, name: '理财', icon: 'chart-trending-o' },
    { id: 103, name: '兼职', icon: 'friends-o' }
  ]
});

const currentCategories = computed(() => categories.value[currentTab.value]);

const newCategory = ref({
  name: '',
  icon: 'apps-o'
});

// 预设图标库 (初始设为空，从后端获取)
const availableIcons = ref([]);

onMounted(async () => {
  try {
    const res = await getAllIcons();
    if (res.code === 0) {
      // 过滤出 group 为 custom 的图标编码
      availableIcons.value = res.data
        .filter(item => item.group === 'custom')
        .map(item => item.icon);
    }
  } catch (e) {
    // console.error('Failed to fetch icons:', e);
  }
});

// 过滤掉当前 Tab 已使用的图标
const filteredAvailableIcons = computed(() => {
  const usedIcons = categories.value[currentTab.value].map(item => item.icon);
  return availableIcons.value.filter(icon => !usedIcons.includes(icon));
});

const goBack = () => {
  uni.navigateTo({
    url: '/pages/page_setting/setting'
  });
};

const removeCategory = (index) => {
  uni.showModal({
    title: '提示',
    content: '确定要删除该类别吗？',
    success: (res) => {
      if (res.confirm) {
        categories.value[currentTab.value].splice(index, 1);
      }
    }
  });
};

const openAddPopup = () => {
  newCategory.value = {
    name: '',
    icon: 'apps-o'
  };
  showAddPopup.value = true;
};

const confirmAdd = () => {
  if (!newCategory.value.name.trim()) {
    uni.showToast({ title: '请输入类别名', icon: 'none' });
    return;
  }
  
  const newItem = {
    id: Date.now(),
    name: newCategory.value.name,
    icon: newCategory.value.icon
  };
  
  categories.value[currentTab.value].push(newItem);
  showAddPopup.value = false;
  uni.showToast({ title: '添加成功', icon: 'success' });
};
</script>

<style scoped>
.category-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: #f8fafc;
}

/* 标签切换 */
.tab-section {
  background-color: #ffd541;
  padding: 0 40px 12px;
}

.tab-group {
  display: flex;
  background-color: rgba(0, 0, 0, 0.05);
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid rgba(0, 0, 0, 0.1);
}

.tab-item {
  flex: 1;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  color: #1e293b;
  transition: all 0.3s;
}

.tab-item.active {
  background-color: #1e293b;
  color: #ffd541;
  font-weight: 600;
}

/* 列表内容 */
.content-body {
  flex: 1;
  overflow-y: auto;
}

.category-list {
  background-color: #fff;
  padding: 0 16px;
}

.category-row {
  display: flex;
  align-items: center;
  padding: 14px 0;
  border-bottom: 1px solid #f1f5f9;
}

.remove-btn {
  margin-right: 12px;
}

.icon-box {
  width: 36px;
  height: 36px;
  background-color: #f8fafc;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 12px;
}

.category-name {
  flex: 1;
  font-size: 15px;
  color: #334155;
}

.drag-handle {
  padding: 4px;
}

/* 底部操作 */
.footer-action {
  height: 56px;
  background-color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  border-top: 1px solid #f1f5f9;
  padding-bottom: env(safe-area-inset-bottom);
}

.add-text {
  font-size: 15px;
  color: #64748b;
  font-weight: 500;
}

/* 弹窗样式 */
.popup-content {
  padding: 20px;
  background-color: #fff;
  height: 100%;
  display: flex;
  flex-direction: column;
  box-sizing: border-box;
}

.popup-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  flex-shrink: 0;
}

.popup-title {
  font-size: 18px;
  font-weight: 700;
  color: #0f172a;
}

.input-section {
  display: flex;
  align-items: center;
  gap: 12px;
  background-color: #f8fafc;
  padding: 12px;
  border-radius: 12px;
  margin-bottom: 20px;
  flex-shrink: 0;
}

.selected-icon-box {
  width: 44px;
  height: 44px;
  background-color: #fff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

.name-input {
  flex: 1;
  font-size: 16px;
  color: #1e293b;
}

.icon-selector {
  margin-bottom: 24px;
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.selector-label {
  display: block;
  font-size: 14px;
  color: #64748b;
  margin-bottom: 12px;
  flex-shrink: 0;
}

.icon-grid-scroll {
  flex: 1;
  overflow-y: auto;
}

.icon-grid {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 12px;
}

.icon-item {
  aspect-ratio: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #f8fafc;
  border-radius: 8px;
  color: #64748b;
  transition: all 0.2s;
}

.icon-item.active {
  background-color: #ffd541;
  color: #1e293b;
}

.confirm-btn-container {
  flex-shrink: 0;
  padding-top: 10px;
}

.confirm-btn {
  height: 48px;
  background-color: #ffd541;
  border-radius: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  font-weight: 700;
  color: #1e293b;
}

.confirm-btn:active {
  opacity: 0.8;
}
</style>
