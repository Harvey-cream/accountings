<template>
  <view class="account-container" :class="currentThemeClass">
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
            <image class="avatar-img" :src="userInfo.avatarUrl" mode="aspectFill"></image>
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
        <view class="settings-item" @click="handleEdit('bio')">
          <text class="item-title">个性签名</text>
          <view class="item-right">
            <text class="item-value bio-text">{{ userInfo.bio || '未填写' }}</text>
            <van-icon name="arrow" color="#cbd5e1" size="16" />
          </view>
        </view>
      </view>

      <!-- 账号绑定 -->
      <view class="settings-group">
        <view class="settings-item" @click="handleEdit('phone')">
          <text class="item-title">手机号</text>
          <view class="item-right">
            <text class="item-value" :class="{ 'not-set': !userInfo.phone }">{{ userInfo.phone ? userInfo.phone : '去绑定' }}</text>
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

      <van-popup
        v-model:show="showNicknamePopup"
        position="bottom"
        round
        :style="{ height: '50%' }"
      >
        <view class="popup-content">
          <view class="popup-header">
            <text class="popup-title">修改昵称</text>
            <van-icon name="cross" size="20" color="#94a3b8" @click="showNicknamePopup = false" />
          </view>
          <view class="popup-body padding-20">
            <view class="input-group">
              <view class="input-label">新昵称</view>
              <input class="popup-input-bg" v-model="nicknameDraft" type="text" placeholder="请输入昵称" maxlength="20" />
            </view>
            <view class="popup-tips">好听的昵称能让大家更快记住你哦。</view>
          </view>
          <view class="popup-footer">
            <view class="confirm-btn" @click="confirmNickname">确定</view>
          </view>
        </view>
      </van-popup>

      <!-- 修改签名弹窗 -->
      <van-popup
        v-model:show="showBioPopup"
        position="bottom"
        round
        :style="{ height: '50%' }"
      >
        <view class="popup-content">
          <view class="popup-header">
            <text class="popup-title">修改个性签名</text>
            <van-icon name="cross" size="20" color="#94a3b8" @click="showBioPopup = false" />
          </view>
          <view class="popup-body padding-20">
            <view class="input-group">
              <view class="input-label">新签名</view>
              <textarea 
                class="popup-input-bg bio-textarea" 
                v-model="bioDraft" 
                placeholder="填写个性签名，展现不一样的你" 
                maxlength="50"
                auto-height
              />
            </view>
            <view class="popup-tips">最多输入50个字符</view>
          </view>
          <view class="popup-footer">
            <view class="confirm-btn" @click="confirmBio">确定</view>
          </view>
        </view>
      </van-popup>
    </scroll-view>
  </view>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useUserStore } from '@/store/user.js';

// 初始用户信息
const userInfo = ref({
  avatar: '/static/4.jpg',
  id: '',
  nickname: '',
  bio: '保持热爱，奔赴山海。✨',
  gender: '',
  phone: '',
  wechat: '',
  apple: '',
  emergency: ''
});

onMounted(() => {
  // 从 session 中获取真实用户信息
  const session = uni.getStorageSync('session');
  if (session && session.user_info) {
    const data = session.user_info;
    userInfo.value.id = data.userId || '';
    userInfo.value.nickname = data.username || '';
    userInfo.value.phone = data.mobile || '';
    userInfo.value.avatar = data.avatarUrl || '/static/4.jpg';
  }
});

const goBack = () => {
  uni.navigateTo({
    url: '/pages/page_setting/setting'
  });
};

const userStore = useUserStore();
const showNicknamePopup = ref(false);
const nicknameDraft = ref('');
const showBioPopup = ref(false);
const bioDraft = ref('');

const confirmNickname = () => {
  const val = nicknameDraft.value.trim();
  if (!val) {
    uni.showToast({ title: '昵称不能为空', icon: 'none' });
    return;
  }
  userInfo.value.nickname = val;
  showNicknamePopup.value = false;
  uni.showToast({ title: '已更新', icon: 'success' });
};

const confirmBio = () => {
  userInfo.value.bio = bioDraft.value.trim();
  showBioPopup.value = false;
  uni.showToast({ title: '签名已更新', icon: 'success' });
};

const confirmPhone = () => {
  const val = phoneDraft.value.trim();
  if (!/^1[3-9]\d{9}$/.test(val)) {
    uni.showToast({ title: '请输入有效的手机号', icon: 'none' });
    return;
  }
  if (!verifyCode.value.trim()) {
    uni.showToast({ title: '请输入验证码', icon: 'none' });
    return;
  }
  
  userInfo.value.phone = val;
  showPhoneSheet.value = false;
  uni.showToast({ title: '绑定成功', icon: 'success' });
};

const confirmEmergency = () => {
  const phone = emergencyPhone.value.trim();
  const email = emergencyEmail.value.trim();
  
  if (phone && !/^1[3-9]\d{9}$/.test(phone)) {
    uni.showToast({ title: '请输入有效的应急手机号', icon: 'none' });
    return;
  }
  if (email && !/^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/.test(email)) {
    uni.showToast({ title: '请输入有效的邮箱地址', icon: 'none' });
    return;
  }
  
  if (!phone && !email) {
    uni.showToast({ title: '请至少填写一项', icon: 'none' });
    return;
  }

  userInfo.value.emergency = phone || email;
  showEmergencySheet.value = false;
  uni.showToast({ title: '保存成功', icon: 'success' });
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
    showNicknamePopup.value = true;
    return;
  }
  if (type === 'bio') {
    bioDraft.value = userInfo.value.bio || '';
    showBioPopup.value = true;
    return;
  }
  if (type === 'phone') {
    const phoneVal = userInfo.value.phone || '';
    uni.navigateTo({
      url: '/pages/page_setting/setting_function/account_setting/page_account/phone?phone=' + phoneVal
    });
    return;
  }
  if (type === 'emergency') {
    const contact = encodeURIComponent(userInfo.value.emergency || '');
    uni.navigateTo({
      url: '/pages/page_setting/setting_function/account_setting/page_account/emergency?contact=' + contact
    });
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
      url: '/pages/page_setting/setting_function/account_setting/page_account/delete_account'
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
        userStore.logout();
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

/* 导航栏样式已移至全局 common.css */

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

/* 弹窗样式 */
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
}

.padding-20 {
  padding: 20px;
}

.input-group {
  margin-bottom: 24px;
}

.input-label {
  font-size: 14px;
  color: #64748b;
  margin-bottom: 12px;
}

.popup-input-bg {
  width: 100%;
  height: 52px;
  background-color: #f8fafc;
  border-radius: 12px;
  padding: 0 16px;
  font-size: 16px;
  color: #1e293b;
  box-sizing: border-box;
}

.popup-tips {
  font-size: 12px;
  color: #94a3b8;
  line-height: 1.6;
}

.bio-textarea {
  padding: 10px;
  line-height: 1.6;
}

.popup-footer {
  padding: 20px;
  padding-bottom: calc(20px + env(safe-area-inset-bottom));
}

.confirm-btn {
  height: 50px;
  background-color: #ffd541;
  border-radius: 25px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  font-weight: 700;
  color: #1e293b;
}

.confirm-btn:active {
  opacity: 0.9;
}
</style>
