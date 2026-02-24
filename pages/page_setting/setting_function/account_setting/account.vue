<template>
  <view class="account-container">
    <!-- 导航栏 -->
    <view class="nav-bar">
      <view class="nav-left" @click="goBack">
        <van-icon name="arrow-left" size="20" color="#1e293b" />
        <text class="nav-title">返回</text>
      </view>
      <text class="page-title">账号设置</text>
      <view class="nav-right"></view>
    </view>

    <!-- 内容区 -->
    <scroll-view scroll-y class="content-body">
      <!-- 基础资料 -->
      <view class="settings-group">
        <view class="settings-item avatar-item" @click="changeAvatar">
          <text class="item-title">头像</text>
          <view class="item-right">
            <image class="avatar-img" :src="userInfo.avatar" mode="aspectFill"></image>
            <van-icon name="arrow" color="#cbd5e1" size="16" />
          </view>
        </view>
        <view class="settings-item">
          <text class="item-title">ID</text>
          <view class="item-right">
            <text class="item-value id-value">{{ userInfo.id }}</text>
          </view>
        </view>
        <view class="settings-item" @click="handleEdit('nickname')">
          <text class="item-title">昵称</text>
          <view class="item-right">
            <text class="item-value">{{ userInfo.nickname }}</text>
            <van-icon name="arrow" color="#cbd5e1" size="16" />
          </view>
        </view>
        <view class="settings-item" @click="handleEdit('gender')">
          <text class="item-title">性别</text>
          <view class="item-right">
            <text class="item-value">{{ userInfo.gender || '未填写' }}</text>
            <van-icon name="arrow" color="#cbd5e1" size="16" />
          </view>
        </view>
      </view>

      <!-- 账号绑定 -->
      <view class="settings-group">
        <view class="settings-item" @click="handleEdit('phone')">
          <text class="item-title">手机号</text>
          <view class="item-right">
            <text class="item-value" :class="{ 'not-set': !userInfo.phone }">{{ userInfo.phone || '未绑定' }}</text>
            <van-icon name="arrow" color="#cbd5e1" size="16" />
          </view>
        </view>
        <view class="settings-item" @click="handleEdit('wechat')">
          <text class="item-title">微信</text>
          <view class="item-right">
            <text class="item-value">{{ userInfo.wechat || '未绑定' }}</text>
            <van-icon name="arrow" color="#cbd5e1" size="16" />
          </view>
        </view>
        <!-- <view class="settings-item" @click="handleEdit('apple')">
          <text class="item-title">Apple</text>
          <view class="item-right">
            <text class="item-value" :class="{ 'not-set': !userInfo.apple }">{{ userInfo.apple || '未绑定' }}</text>
            <van-icon name="arrow" color="#cbd5e1" size="16" />
          </view>
        </view> -->
        <view class="settings-item" @click="handleEdit('emergency')">
          <text class="item-title">应急联系方式</text>
          <view class="item-right">
            <text class="item-value" :class="{ 'not-set': !userInfo.emergency }">{{ userInfo.emergency || '未设置' }}</text>
            <van-icon name="arrow" color="#cbd5e1" size="16" />
          </view>
        </view>
      </view>

      <!-- 安全与隐私 -->
      <view class="settings-group">
        <view class="settings-item" @click="handleItemClick('export')">
          <text class="item-title">个人信息浏览及导出</text>
          <van-icon name="arrow" color="#cbd5e1" size="16" />
        </view>
        <view class="settings-item delete-item" @click="handleItemClick('delete')">
          <view class="item-content">
            <text class="item-title">申请注销账号</text>
            <text class="item-desc">注销后账号无法找回</text>
          </view>
          <van-icon name="arrow" color="#cbd5e1" size="16" />
        </view>
      </view>

      <!-- 退出登录 -->
      <view class="logout-section">
        <view class="logout-btn" @click="handleLogout">
          <text>退出登录</text>
        </view>
      </view>

      <view v-if="showNicknameSheet" class="bottom-sheet-mask" @click="showNicknameSheet = false">
        <view class="bottom-sheet" @click.stop>
          <view class="sheet-header">
            <text class="sheet-title">修改昵称</text>
            <van-icon name="cross" size="20" color="#94a3b8" @click="showNicknameSheet = false" />
          </view>
          <view class="sheet-body">
            <input class="sheet-input" v-model="nicknameDraft" type="text" placeholder="请输入昵称" maxlength="20" confirm-type="done" />
          </view>
          <view class="sheet-actions">
            <view class="sheet-btn cancel" @click="showNicknameSheet = false">取消</view>
            <view class="sheet-btn confirm" @click="confirmNickname">确定</view>
          </view>
        </view>
      </view>
    </scroll-view>
  </view>
</template>

<script setup>
import { ref } from 'vue';

// 虚拟用户信息
const userInfo = ref({
  avatar: '/static/4.jpg',
  id: '79266855',
  nickname: 'oxo',
  gender: '',
  phone: '',
  wechat: 'oxo',
  apple: '',
  emergency: ''
});

const goBack = () => {
  uni.navigateTo({
    url: '/pages/page_setting/setting'
  });
};

const showNicknameSheet = ref(false);
const nicknameDraft = ref('');

const confirmNickname = () => {
  const val = nicknameDraft.value.trim();
  if (!val) {
    uni.showToast({ title: '昵称不能为空', icon: 'none' });
    return;
  }
  userInfo.value.nickname = val;
  showNicknameSheet.value = false;
  uni.showToast({ title: '已更新', icon: 'success' });
};

// 修改头像
const changeAvatar = () => {
  uni.chooseImage({
    count: 1,
    sizeType: ['compressed'],
    sourceType: ['album', 'camera'],
    success: (res) => {
      const tempFile = res.tempFiles[0];
      const tempFilePath = res.tempFilePaths[0];
      if (tempFile.type && !tempFile.type.startsWith('image/')) {
        uni.showToast({ title: '请选择图片格式文件', icon: 'none' });
        return;
      }
      
      // 2. 如果没有 type，检查文件路径后缀 (处理带有参数或 Blob 的情况)
      if (!tempFile.type) {
        const pathWithoutQuery = tempFilePath.split('?')[0];
        const ext = pathWithoutQuery.split('.').pop().toLowerCase();
        const isImage = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp', 'heic', 'heif'].includes(ext);
        
        // 注意：在某些 H5 环境下，blob 链接可能没有后缀，此时我们信任 uni.chooseImage 的选择结果
        if (ext && !isImage && !tempFilePath.startsWith('blob:')) {
          uni.showToast({ title: '请选择图片格式文件', icon: 'none' });
          return;
        }
      }

      // 模拟上传成功
      userInfo.value.avatar = tempFilePath;
      uni.showToast({
        title: '更换成功',
        icon: 'success'
      });
    }
  });
};

const handleEdit = (type) => {
  if (type === 'nickname') {
    nicknameDraft.value = userInfo.value.nickname || '';
    showNicknameSheet.value = true;
    return;
  }
  if (type === 'gender') {
    uni.showActionSheet({
      itemList: ['男', '女'],
      success: (res) => {
        userInfo.value.gender = res.tapIndex === 0 ? '男' : '女';
        uni.showToast({ title: '已更新', icon: 'success' });
      }
    });
    return;
  }
  uni.showToast({ title: '功能开发中', icon: 'none' });
};

const handleItemClick = (type) => {
  if (type === 'delete') {
    uni.navigateTo({
      url: '/pages/page_setting/setting_function/account_setting/delete_account'
    });
    return;
  }
  uni.showToast({
    title: '功能开发中',
    icon: 'none'
  });
};

const handleLogout = () => {
  uni.showModal({
    title: '提示',
    content: '确定要退出登录吗？',
    success: (res) => {
      if (res.confirm) {
        uni.showToast({
          title: '已退出登录',
          icon: 'none'
        });
      }
    }
  });
};
</script>

<style scoped>
.account-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: #f8fafc;
}

/* 导航栏 */
.nav-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px 10px; /* 适配状态栏高度 */
  background-color: #ffd541;
  position: relative;
  z-index: 100;
}

.nav-left {
  display: flex;
  align-items: center;
  gap: 4px;
  width: 80px;
}

.nav-title {
  font-size: 16px;
  color: #1e293b;
  font-weight: 500;
}

.page-title {
  font-size: 18px;
  font-weight: 600;
  color: #0f172a;
}

.nav-right {
  width: 80px;
}

.content-body {
  flex: 1;
  overflow-y: auto;
}

/* 设置组 */
.settings-group {
  background-color: #fff;
  margin-top: 10px;
  padding: 0 16px;
}

/* 设置项 */
.settings-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 0;
  border-bottom: 1px solid #f1f5f9;
}

.settings-item:last-child {
  border-bottom: none;
}

.item-title {
  font-size: 15px;
  color: #334155;
  font-weight: 500;
}

.item-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.item-value {
  font-size: 15px;
  color: #94a3b8;
}

.id-value {
  color: #cbd5e1;
}

.not-set {
  color: #fca5a5; /* 浅红色提示未绑定 */
}

/* 头像项特有样式 */
.avatar-item {
  padding: 12px 0;
}

.avatar-img {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background-color: #f1f5f9;
}

/* 注销项特有样式 */
.delete-item .item-content {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.item-desc {
  font-size: 12px;
  color: #cbd5e1;
}

/* 退出登录 */
.logout-section {
  margin-top: 20px;
  padding: 0 16px 40px;
}

.logout-btn {
  background-color: #fff;
  height: 50px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  font-size: 16px;
  color: #475569;
  font-weight: 500;
}

.logout-btn:active {
  background-color: #f8fafc;
}

.bottom-sheet-mask {
  position: fixed;
  left: 0; right: 0; top: 0; bottom: 0;
  background-color: rgba(0,0,0,0.5);
  display: flex;
  justify-content: center;
  align-items: flex-end;
  z-index: 999;
}
.bottom-sheet {
  width: 100%;
  background-color: #fff;
  border-top-left-radius: 16px;
  border-top-right-radius: 16px;
  padding: 16px;
}
.sheet-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.sheet-title { font-size: 16px; font-weight: 600; color: #0f172a; }
.sheet-body { padding: 12px 0; }
.sheet-input {
  width: 100%;
  height: 40px;
  background-color: #f8fafc;
  border-radius: 8px;
  padding: 0 12px;
  font-size: 14px;
}
.sheet-actions { display: flex; justify-content: flex-end; gap: 12px; }
.sheet-btn { padding: 8px 16px; border-radius: 18px; font-size: 14px; }
.sheet-btn.cancel { background-color: #f1f5f9; color: #64748b; }
.sheet-btn.confirm { background-color: #ffd541; color: #0f172a; font-weight: 600; }
</style>
