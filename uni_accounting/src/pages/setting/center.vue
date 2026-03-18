<template>
	<view class="my-container" :class="currentThemeClass">
		<!-- 头部个人信息卡片 -->
		<view class="header-card">
			<view class="header-banner">
				<view class="user-info">
					<image class="avatar" :src="userInfo.avatarUrl || '/static/default_avatar.png'" mode="aspectFill"></image>
					<view class="user-detail">
						<text class="user-name">{{ userInfo.nickname || userInfo.username || '未登录' }}</text>
					</view>
					<view class="check-in-btn" @click="handleCheckIn">
						<van-icon :name="isChecked ? 'passed' : 'todo-list-o'" size="14" />
						<text class="check-in-text">{{ isChecked ? '已打卡' : '打卡' }}</text>
					</view>
				</view>

				<!-- 数据统计 -->
				<view class="stats-row">
					<view class="stat-item">
						<text class="stat-num">{{ userStats.continuousCheckIn }}</text>
						<text class="stat-label">已连续打卡</text>
					</view>
					<view class="stat-item">
						<text class="stat-num">{{ userStats.totalAccountingDays }}</text>
						<text class="stat-label">记账总天数</text>
					</view>
					<view class="stat-item">
						<text class="stat-num">{{ userStats.totalRecords }}</text>
						<text class="stat-label">记账总笔数</text>
					</view>
				</view>
			</view>

			<!-- VIP 升级入口 -->
			<view class="menu-card vip-card" @click="handleVIPClick">
				<view class="menu-left">
					<van-icon name="gold-coin" color="#f59e0b" size="24" />
					<view class="menu-text">
						<text class="menu-title">升级为VIP</text>
						<text class="menu-sub">畅享更多高级功能</text>
					</view>
				</view>
				<van-icon name="arrow" color="#cbd5e1" />
			</view>
		</view>

		<!-- 快捷功能图标栏 -->
		<view class="quick-actions-card">
			<view class="action-item" @click="goToMessage">
				<van-badge :dot="unreadCount > 0" position="top-right">
					<van-icon name="bell" color="#facc15" size="24" />
				</van-badge>
				<text class="action-label">消息</text>
			</view>
			<view class="action-item" @click="goToMedal">
				<van-icon name="medal" color="#d97706" size="24" />
				<text class="action-label">我的勋章</text>
			</view>
			<view class="action-item" @click="goToPoints">
				<van-icon name="gift" color="#3b82f6" size="24" />
				<text class="action-label">我的积分</text>
			</view>
			<view class="action-item" @click="handleOpenInvitePopup">
				<van-icon name="smile" color="#f97316" size="24" />
				<text class="action-label">邀请好友</text>
			</view>
			<view class="action-item" @click="goToSetting">
				<view class="dot-badge"></view>
				<van-icon name="setting" color="#475569" size="24"/>
				<text class="action-label">设置</text>
			</view>
		</view>
		<!-- 社交消息 -->
			<view class="menu-group">
			<view class="menu-item" @click="goToSocialProfile">
				<view class="menu-left">
					<van-icon name="user-o" size="20" color="#1e293b" />
					<text class="item-title">社交主页</text>
				</view>
				<van-icon name="arrow" color="#cbd5e1" />
			</view>
			<view class="menu-item" @click="goToSocialMessage">
				<view class="menu-left">
					<van-icon name="notes-o" size="20" color="#1e293b" />
					<text class="item-title">社交消息</text>
				</view>
				<van-icon name="arrow" color="#cbd5e1" />
			</view>
			</view>
		<!-- 菜单列表组 1 -->
		<view class="menu-group">
			<view class="menu-item" @click="goToBilling">
				<view class="menu-left">
					<van-icon name="notes-o" size="20" color="#1e293b" />
					<text class="item-title">账单管理</text>
				</view>
				<van-icon name="arrow" color="#cbd5e1" />
			</view>
			<view class="menu-item">
				<view class="menu-left">
					<van-icon name="wap-home-o" size="20" color="#1e293b" />
					<text class="item-title">家庭账单</text>
				</view>
				<van-icon name="arrow" color="#cbd5e1" />
			</view>
		</view>
		<!-- 财务与数据 -->
		<view class="menu-group">
			<view class="menu-item" @click="goToBudget">
				<view class="menu-left">
					<van-icon name="chart-trending-o" size="20" color="#1e293b" />
					<text class="item-title">预算中心</text>
				</view>
				<van-icon name="arrow" color="#cbd5e1" />
			</view>
			<view class="menu-item" @click="handleOpenTimePicker">
				<view class="menu-left">
					<van-icon name="clock-o" size="20" color="#1e293b" />
					<text class="item-title">定期记账</text>
				</view>
				<van-icon name="arrow" color="#cbd5e1" />
			</view>
			<view class="menu-item" @click="goToExport">
				<view class="menu-left">
					<van-icon name="down" size="20" color="#1e293b" />
					<text class="item-title">数据导出</text>
				</view>
				<van-icon name="arrow" color="#cbd5e1" />
			</view>
		</view>

		<!-- 菜单列表组 2 -->
		<view class="menu-group">
			<view class="menu-item" @click="goToSetting">
				<view class="menu-left">
					<van-icon name="setting-o" size="20" color="#1e293b" />
					<text class="item-title">设置</text>
				</view>
				<van-icon name="arrow" color="#cbd5e1" />
			</view>
			<view class="menu-item" @click="goToHelp">
				<view class="menu-left">
					<van-icon name="question-o" size="20" color="#1e293b" />
					<text class="item-title">使用帮助</text>
				</view>
				<van-icon name="arrow" color="#cbd5e1" />
			</view>
			<view class="menu-item" @click="goToFeedback">
				<view class="menu-left">
					<van-icon name="edit" size="20" color="#1e293b" />
					<text class="item-title">意见反馈</text>
				</view>
				<van-icon name="arrow" color="#cbd5e1" />
			</view>
			<view class="menu-item">
				<view class="menu-left">
					<van-icon name="thumb-circle-o" size="20" color="#1e293b" />
					<text class="item-title">去 App Store 给记账评分</text>
				</view>
				<van-icon name="arrow" color="#cbd5e1" />
			</view>
		</view>

		<!-- 时间选择弹窗 -->
		<van-popup :show="showTimePicker" position="bottom" round @close="showTimePicker = false">
			<van-picker
				title="选择记账时间"
				show-toolbar
				:columns="pickerColumns"
				@confirm="onConfirmDateClick"
				@cancel="showTimePicker = false"
			/>
		</van-popup>

		<CustomTabbar :selected="2" />
		
		<!-- 邀请好友弹窗 -->
		<view v-if="showInvitePopup" class="invite-modal-mask" @click.stop="handleCloseInvitePopup">
			<view class="invite-modal" @click.stop>
				<view class="modal-header">
					<text class="modal-title">邀请好友</text>
					<van-icon name="cross" size="20" color="#94a3b8" @click="handleCloseInvitePopup" />
				</view>
				<view class="qr-container">
					<image class="qr-code" src="https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=https://uni-accounting.com/invite?user=oxo" mode="aspectFit"></image>
					<text class="qr-tip">扫码下载小龙记账</text>
				</view>
				<view class="modal-actions">
					<view class="save-btn" @click="saveQRCode">
						<van-icon name="down" color="#fff" size="18" />
						<text>保存二维码</text>
					</view>
				</view>
			</view>
		</view>
	</view>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { onShow } from '@dcloudio/uni-app';
import CustomTabbar from '@/components/Tabbar/Tabbar.vue';
import { userCheckIn, getUserStats, getUnreadMessageCount, getUserInfo } from '@/api/api.js';

// 登录用户信息
const userInfo = ref({
	username: '',
	avatarUrl: ''
});

// 未读消息数量
const unreadCount = ref(0);

const fetchUserInfo = async () => {
	try {
		const res = await getUserInfo();
		if (res.code === 0) {
			userInfo.value = res.data;
			// 同步更新缓存中的头像和昵称，防止其他页面读取过期 URL
			const session = uni.getStorageSync('session');
			if (session && session.user_info) {
				session.user_info.avatarUrl = res.data.avatarUrl;
				session.user_info.nickname = res.data.nickname;
				uni.setStorageSync('session', session);
			}
		}
	} catch (e) {
		console.error('获取用户信息失败:', e);
	}
};

const fetchUnreadCount = async () => {
	try {
		const res = await getUnreadMessageCount();
		if (res.code === 0) {
			unreadCount.value = res.data.unread_count;
		}
	} catch (e) {
		console.error('获取未读消息数量失败:', e);
	}
};

const userStats = ref({
	continuousCheckIn: 0,
	totalAccountingDays: 0,
	totalRecords: 0,
	isCheckedIn: false
});

const fetchUserStats = async () => {
	try {
		const res = await getUserStats();
		if (res.code === 0) {
			userStats.value = res.data;
			isChecked.value = res.data.isCheckedIn;
		}
	} catch (e) {
		console.error('获取统计数据失败:', e);
	}
};

const handleCheckIn = async () => {
	if (isChecked.value) return;
	try {
		const res = await userCheckIn();
		if (res.code === 0) {
			const { continuous_days, new_unlocked_medals, next_progress } = res.data;
			
			// 1. 打卡成功基础提示
			let toastMsg = `打卡成功！已连续打卡${continuous_days}天`;
			if (next_progress) {
				toastMsg += `\n距离下一勋章还差${next_progress.required_days - next_progress.current_days}天`;
			}
			
			uni.showToast({ 
				title: toastMsg, 
				icon: 'none',
				duration: 2500
			});
			
			// 2. 如果解锁了新勋章，弹出成就弹窗
			if (new_unlocked_medals && new_unlocked_medals.length > 0) {
				setTimeout(() => {
					const medal = new_unlocked_medals[0];
					uni.showModal({
						title: '🎉 恭喜获得新勋章！',
						content: `解锁勋章：【${medal.name}】\n${medal.description}`,
						showCancel: false,
						confirmText: '太棒了',
						confirmColor: '#facc15'
					});
				}, 1500);
			}
			
			fetchUserStats();
		} else {
			uni.showToast({ title: res.msg || '打卡失败', icon: 'none' });
		}
	} catch (e) {
		uni.showToast({ title: '打卡异常', icon: 'none' });
	}
};

const handleVIPClick = () => {
	uni.showToast({
		title: 'VIP功能敬请期待！',
		icon: 'none'
	});
};

// 生成选择器数据（仅显示今天及以后的一年）
const getPickerColumns = () => {
	const weekdaysList = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'];
	const now = new Date();
	const dateColumn = Array.from({ length: 365 }, (_, i) => {
		const d = new Date(now.getFullYear(), now.getMonth(), now.getDate() + i);
		return {
			text: `${d.getMonth() + 1}月${d.getDate()}日 ${weekdaysList[d.getDay()]}`,
			value: `${d.getFullYear()}-${(d.getMonth() + 1).toString().padStart(2, '0')}-${d.getDate().toString().padStart(2, '0')}`
		};
	});
	const hours = Array.from({ length: 24 }, (_, i) => ({ text: `${i}时`, value: i.toString().padStart(2, '0') }));
	const minutes = Array.from({ length: 60 }, (_, i) => ({ text: `${i}分`, value: i.toString().padStart(2, '0') }));
	
	// Vant Weapp 多列格式
	return [
		{ values: dateColumn.map(i => i.text) },
		{ values: hours.map(i => i.text) },
		{ values: minutes.map(i => i.text) }
	];
};

// 打卡状态
const isChecked = ref(false);
// 时间选择
const showTimePicker = ref(false);
const selectedValues = ref([]);
const pickerColumns = getPickerColumns();

const handleOpenTimePicker = () => {
	showTimePicker.value = true;
};

const handleCloseTimePicker = () => showTimePicker.value = false;

onMounted(() => {
	const session = uni.getStorageSync('session');
	if (session && session.user_info) {
		userInfo.value = session.user_info;
	}
});

onShow(() => {
	fetchUserInfo();
	fetchUserStats();
	fetchUnreadCount();
});

const onConfirmDateClick = (event) => {
	const { value } = event.detail || event;
	showTimePicker.value = false;
	// value 现在是选中的 text 数组
	uni.showToast({ title: `已设置：${value.join(' ')}`, icon: 'none' });
};

// 邀请好友
const showInvitePopup = ref(false);
const handleOpenInvitePopup = () => showInvitePopup.value = true;
const handleCloseInvitePopup = () => showInvitePopup.value = false;

// 保存二维码
const saveQRCode = () => {
	// H5环境下直接提示长按保存
	// #ifdef H5
	uni.showToast({
		title: '请长按图片保存',
		icon: 'none'
	});
	// #endif
	
	// #ifndef H5
	uni.downloadFile({
		url: 'https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=https://uni-accounting.com/invite?user=oxo',
		success: (res) => {
			if (res.statusCode === 200) {
				uni.saveImageToPhotosAlbum({
					filePath: res.tempFilePath,
					success: function () {
						uni.showToast({
							title: '保存成功',
							icon: 'success'
						});
					},
					fail: function () {
						uni.showToast({
							title: '保存失败',
							icon: 'none'
						});
					}
				});
			}
		}
	});
	// #endif
};

// 跳转到消息页面
const goToMessage = () => {
	uni.navigateTo({
		url: '/pages/page_core/page_message/message'
	});
};

// 跳转到社交消息页面
const goToSocialMessage = () => {
	uni.navigateTo({
		url: '/pages/page_social/social_messages/message'
	});
};

// 跳转到社交主页
const goToSocialProfile = () => {
	uni.navigateTo({
		url: '/pages/page_social/social_profile/profile'
	});
};

// 跳转到勋章页面
const goToMedal = () => {
	uni.navigateTo({
		url: '/pages/page_core/page_medal/medal'
	});
};

// 跳转到积分页面
const goToPoints = () => {
	uni.navigateTo({
		url: '/pages/page_core/page_points/point'
	});
};

// 跳转到账单管理页面
const goToBilling = () => {
	uni.navigateTo({
		url: '/pages/page_function/bill_management/billing'
	});
};

const goToBudget = () => {
	uni.navigateTo({
		url: '/pages/page_function/budget_center/budget'
	});
};

// 跳转到数据导出页面
const goToExport = () => {
	uni.navigateTo({
		url: '/pages/page_function/data_export/export'
	});
};

// 跳转到设置页面
const goToSetting = () => {
	uni.navigateTo({
		url: '/pages/page_setting/setting'
	});
};

// 跳转到使用帮助页面
const goToHelp = () => {
	uni.navigateTo({
		url: '/pages/page_other/user_help/helpful'
	});
};

// 跳转到意见反馈页面
const goToFeedback = () => {
	uni.navigateTo({
		url: '/pages/page_other/user_feedback/feedback'
	});
};

// 跳转到消息页面
</script>

<style scoped>
.my-container {
	background-color: #f8fafc;
	min-height: 100vh;
	padding: 0 16px 100px;
}

/* 头部区域 */
.header-card {
	margin: 0 -16px 10px;
	position: relative;
}

/* 头部黄色背景块 - 整合了用户信息和数据统计的背景 */
.header-banner {
	background-color: #ffd541;
	padding: 20px 16px 50px; /* 底部增加 padding 用于放置 VIP 卡片 */
}

.user-info {
	display: flex;
	align-items: center;
	margin-bottom: 15px;
	padding: 0 10px;
}

.avatar {
	width: 60px;
	height: 60px;
	border-radius: 50%;
	border: 2px solid #fff;
	background-color: #fff;
}

.user-detail {
	flex: 1;
	margin-left: 15px;
}

.user-name {
	font-size: 22px;
	font-weight: 800;
	color: #0f172a;
}

.check-in-btn {
	background-color: #fff;
	padding: 6px 14px;
	border-radius: 20px;
	display: flex;
	align-items: center;
	gap: 4px;
}

.check-in-text {
	font-size: 13px;
	font-weight: 600;
	color: #0f172a;
}

.stats-row {
	display: flex;
	justify-content: space-around;
	text-align: center;
}

.stat-num {
	display: block;
	font-size: 20px;
	font-weight: 500;
	color: #0f172a;
}

.stat-label {
	font-size: 12px;
	color: #0f172a;
	opacity: 0.8;
	margin-top: 4px;
}

/* 通用卡片样式 */
.menu-card,
.quick-actions-card,
.menu-group {
	background-color: #fff;
	border-radius: 10px;
	margin-bottom: 10px;
	padding: 10px;
	box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02);
}

/* VIP 卡片 - 悬浮在 Banner 之上 */
.vip-card {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin: -35px 16px 0; /* 负 margin 向上提 */
	position: relative;
	z-index: 10;
}

.menu-left {
	display: flex;
	align-items: center;
	gap: 12px;
}

.menu-title {
	font-size: 16px;
	font-weight: 700;
	color: #1e293b;
	display: block;
}

.menu-sub {
	font-size: 12px;
	color: #94a3b8;
}

/* 快捷功能 */
.quick-actions-card {
	display: flex;
	justify-content: space-around;
	padding: 10px;
}

.action-item {
	display: flex;
	flex-direction: column;
	align-items: center;
	gap: 8px;
	position: relative;
}

.action-label {
	font-size: 12px;
	color: #64748b;
}

.dot-badge {
	position: absolute;
	top: 0;
	right: 4px;
	width: 6px;
	height: 6px;
	background-color: #ef4444;
	border-radius: 50%;
	border: 1px solid #fff;
}

/* 菜单列表 */
.menu-group {
	padding: 0 16px;
}

.menu-item {
	display: flex;
	justify-content: space-between;
	align-items: center;
	padding: 16px 0;
}

.menu-item:not(:last-child) {
	border-bottom: 1px solid #f1f5f9;
}

.item-title {
	font-size: 15px;
	font-weight: 600;
	color: #334155;
}

.menu-right {
	display: flex;
	align-items: center;
	gap: 4px;
}

.risk-text {
	font-size: 12px;
	color: #ef4444;
}

/* 时间选择弹窗卡片 */
.time-modal-mask {
	position: fixed;
	top: 0;
	left: 0;
	right: 0;
	bottom: 0;
	background-color: rgba(0, 0, 0, 0.6);
	display: flex;
	justify-content: center;
	align-items: center;
	z-index: 1000;
}

.time-modal-card {
	background-color: #fff;
	border-radius: 16px;
	width: 300px;
	padding: 20px;
	box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
}

.picker-container {
	padding: 10px 0;
	background-color: #f8fafc;
	border-radius: 12px;
	margin: 15px 0;
}

:deep(.van-picker) {
	background-color: transparent;
}

:deep(.van-picker-column__item) {
	font-size: 15px;
	color: #64748b;
}

:deep(.van-picker-column__item--selected) {
	color: #0f172a;
	font-weight: 600;
}

.time-modal-card .modal-actions {
	display: flex;
	justify-content: flex-end;
	gap: 15px;
	margin-top: 10px;
}

.cancel-btn {
	padding: 8px 20px;
	font-size: 14px;
	color: #64748b;
	background-color: #f1f5f9;
	border-radius: 20px;
}

.confirm-btn {
	padding: 8px 20px;
	font-size: 14px;
	color: #0f172a;
	background-color: #ffd541;
	border-radius: 20px;
	font-weight: 600;
}

.cancel-btn:active, .confirm-btn:active {
	opacity: 0.8;
}

/* 邀请好友弹窗 */
.invite-modal-mask {
	position: fixed;
	top: 0;
	left: 0;
	right: 0;
	bottom: 0;
	background-color: rgba(0, 0, 0, 0.6);
	display: flex;
	justify-content: center;
	align-items: center;
	z-index: 999;
}

.invite-modal {
	background-color: #fff;
	border-radius: 16px;
	width: 280px;
	padding: 20px;
	display: flex;
	flex-direction: column;
	align-items: center;
}

.modal-header {
	width: 100%;
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 20px;
}

.modal-title {
	font-size: 18px;
	font-weight: 700;
	color: #0f172a;
}

.qr-container {
	display: flex;
	flex-direction: column;
	align-items: center;
	margin-bottom: 20px;
}

.qr-code {
	width: 200px;
	height: 200px;
	margin-bottom: 12px;
}

.qr-tip {
	font-size: 14px;
	color: #64748b;
}

.modal-actions {
	width: 100%;
}

.save-btn {
	background: linear-gradient(135deg, #f59e0b, #fbbf24);
	color: #fff;
	height: 44px;
	border-radius: 22px;
	display: flex;
	align-items: center;
	justify-content: center;
	gap: 6px;
	font-size: 16px;
	font-weight: 600;
	box-shadow: 0 4px 6px -1px rgba(245, 158, 11, 0.3);
}

.save-btn:active {
	opacity: 0.9;
	transform: scale(0.98);
}
</style>
