<template>
  <view class="publish-container">
    <!-- 顶部导航栏 -->
    <view class="nav-header">
      <text class="cancel-text" @click="onCancel">取消</text>
      <text class="page-title">发布动态</text>
      <van-button type="primary" color="#ffd541" size="small" custom-class="publish-btn" round  @click="onPublish" >
        发布
      </van-button>
    </view>

    <!-- 内容输入区域 -->
    <view class="content-body">
      <textarea
        v-model="content"
        class="post-input"
        placeholder="分享你的省钱妙招或今日心情..."
        placeholder-style="color: #94a3b8; font-size: 15px;"
      ></textarea>

      <!-- 图片上传区域 -->
      <view class="image-uploader">
        <!-- 已选图片预览 -->
        <view
          v-for="(img, index) in fileList"
          :key="index"
          class="preview-item"
        >
          <image :src="img" mode="aspectFill" class="preview-image" />
          <view class="delete-btn" @click.stop="deleteImage(index)">
            <van-icon name="cross" size="12" color="#fff" />
          </view>
        </view>

        <!-- 添加图片按钮 -->
        <view class="add-btn" @click="chooseImage" v-if="fileList.length < 9">
          <van-icon name="plus" size="24" color="#cbd5e1" />
          <text class="add-text">添加图片</text>
        </view>
      </view>

      <!-- 选项列表 -->
      <view class="options-list">
        <!-- 选择分类 -->
        <view class="option-item" @click="showCategorySheet = true">
          <view class="left-icon">
            <van-icon name="label-o" size="20" color="#64748b" />
            <text class="option-label">选择分类</text>
          </view>
          <view class="right-content">
             <!-- 简单的分类展示，这里模拟选中状态 -->
            <view class="category-tags">
               <text
                v-for="(cat, idx) in categories"
                :key="idx"
                :class="['cat-tag', { active: currentCategory === cat }]"
                @click.stop="currentCategory = cat"
               >
                 {{ cat }}
               </text>
            </view>
            <van-icon name="arrow" size="16" color="#cbd5e1" />
          </view>
        </view>

        <!-- 显示位置 -->
        <view class="option-item">
          <view class="left-icon">
            <van-icon name="location-o" size="20" color="#64748b" />
            <text class="option-label">显示位置</text>
          </view>
          <view class="right-content">
            <text class="location-text" v-if="showLocation">杭州市 · 滨江区</text>
            <van-switch v-model="showLocation" size="20px" active-color="#10b981" />
          </view>
        </view>

        <!-- 谁可以看 -->
        <view class="option-item" @click="showVisibilitySheet = true">
          <view class="left-icon">
            <van-icon name="eye-o" size="20" color="#64748b" />
            <text class="option-label">谁可以看</text>
          </view>
          <view class="right-content">
            <text class="value-text">{{ visibility }}</text>
            <van-icon name="arrow" size="16" color="#cbd5e1" />
          </view>
        </view>
      </view>
    </view>

    <!-- 谁可以看 - 选择弹窗 -->
    <van-popup :show="showVisibilitySheet" position="bottom" round @close="showVisibilitySheet = false">
      <van-picker
        title="选择可见性"
        show-toolbar
        :columns="visibilityColumns"
        @confirm="onVisibilityConfirm"
        @cancel="showVisibilitySheet = false"
      />
    </van-popup>
  </view>
</template>

<script setup>
import { ref } from 'vue';

// --- 状态定义 ---

// 动态内容
const content = ref('');

// 图片列表
const fileList = ref([]);

// 分类数据
const categories = ['省钱攻略', '心情分享'];
const currentCategory = ref('心情分享');
const showCategorySheet = ref(false);

// 位置开关
const showLocation = ref(true);

// 可见性选择
const visibility = ref('公开');
const showVisibilitySheet = ref(false);
const visibilityColumns = [
  { text: '公开', value: '公开' },
  { text: '私密', value: '私密' }
];

// --- 方法定义 ---

// 确认可见性选择
const onVisibilityConfirm = ({ selectedOptions }) => {
  visibility.value = selectedOptions[0].text;
  showVisibilitySheet.value = false;
};

// 返回上一页
const onCancel = () => {
  const pages = getCurrentPages();
  if (pages.length > 1) {
    uni.navigateBack();
  } else {
    uni.reLaunch({
      url: '/pages/page_discover/community'
    });
  }
};

// 发布动态
const onPublish = () => {
  if (!content.value.trim() && fileList.value.length === 0) {
    uni.showToast({
      title: '写点什么吧~',
      icon: 'none'
    });
    return;
  }

  uni.showLoading({ title: '发布中...' });

  // 模拟发布请求
  setTimeout(() => {
    uni.hideLoading();
    uni.showToast({
      title: '发布成功',
      icon: 'success'
    });
    // 延迟返回
    setTimeout(() => {
      uni.navigateBack();
    }, 1500);
  }, 1000);
};

// 选择图片
const chooseImage = () => {
  uni.chooseImage({
    count: 9 - fileList.value.length, // 剩余可传数量
    sizeType: ['original', 'compressed'],
    sourceType: ['album', 'camera'],
    success: (res) => {
      // 将新选择的图片添加到列表中
      fileList.value = [...fileList.value, ...res.tempFilePaths];
    }
  });
};

// 删除图片
const deleteImage = (index) => {
  fileList.value.splice(index, 1);
};

</script>

<style scoped>
.publish-container {
  min-height: 100vh;
  background-color: #fff;
  display: flex;
  flex-direction: column;
}

/* 顶部导航 */
.nav-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 44px 16px 12px; /* 适配状态栏高度，假设为44px */
  background-color: #fff;
  /* position: sticky;
  top: 0;
  z-index: 100; */
}

.cancel-text {
  font-size: 16px;
  color: #64748b;
  padding: 4px 8px; /* 增加点击区域 */
  margin-left: -8px; /* 抵消 padding 保证视觉对齐 */
}

.page-title {
  font-size: 18px;
  font-weight: 600;
  color: #0f172a;
}

/* 覆盖 Vant 按钮样式以匹配设计 */
:deep(.publish-btn) {
  padding: 0 20px !important;
  height: 32px !important;
  line-height: 30px !important;
  font-weight: 600 !important;
  color: #0f172a !important; /* 按钮文字颜色 */
  border: none !important;
}

/* 内容区域 */
.content-body {
  flex: 1;
  padding: 20px 16px;
}

.post-input {
  width: 100%;
  height: 120px;
  font-size: 16px;
  line-height: 1.5;
  color: #0f172a;
  margin-bottom: 20px;
}

/* 图片上传 */
.image-uploader {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 30px;
}

.add-btn {
  width: 100px;
  height: 100px;
  background-color: #f8fafc;
  border: 1px dashed #e2e8f0;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}

.add-text {
  font-size: 12px;
  color: #94a3b8;
  margin-top: 8px;
}

.preview-item {
  width: 100px;
  height: 100px;
  position: relative;
  border-radius: 12px;
  overflow: hidden;
}

.preview-image {
  width: 100%;
  height: 100%;
}

.delete-btn {
  position: absolute;
  top: 4px;
  right: 4px;
  background-color: rgba(0, 0, 0, 0.5);
  border-radius: 50%;
  padding: 2px;
  display: flex;
}

/* 选项列表 */
.options-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.option-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 16px;
  border-bottom: 1px solid #f1f5f9;
}

.option-item:last-child {
  border-bottom: none;
}

.left-icon {
  display: flex;
  align-items: center;
  gap: 8px;
}

.option-label {
  font-size: 15px;
  font-weight: 600;
  color: #0f172a;
}

.right-content {
  display: flex;
  align-items: center;
  gap: 8px;
}

.value-text {
  font-size: 14px;
  color: #94a3b8;
}

.location-text {
  font-size: 14px;
  color: #94a3b8;
  margin-right: 8px;
}

/* 分类标签样式 */
.category-tags {
  display: flex;
  gap: 8px;
}

.cat-tag {
  padding: 4px 12px;
  background-color: #f1f5f9;
  color: #64748b;
  font-size: 12px;
  border-radius: 12px;
}

.cat-tag.active {
  background-color: #fffbeb; /* 浅黄色背景 */
  color: #0f172a;
  font-weight: 500;
  border: 1px solid #ffd541; /* 黄色边框 */
}
</style>
