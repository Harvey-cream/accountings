<template>
	<view class="container">
		<!-- 导航栏 -->
		<view class="nav-bar">
			<view class="nav-left" @click="goBack">
				<van-icon name="arrow-left" size="20" color="#1e293b" />
				<text class="nav-title">返回</text>
			</view>
			<text class="page-title">设置</text>
			<view class="nav-right"></view>
		</view>

		<!-- 设置内容 -->
		<scroll-view scroll-y class="content-area">
			
			<!-- 账号设置 -->
			<view class="settings-group first-group">
				<view class="settings-item" @click="handleItemClick('account')">
					<view class="item-left">
						<van-icon name="user-o" size="20" color="#1e293b" />
						<text class="item-title">账号设置</text>
					</view>
					<van-icon name="arrow" color="#cbd5e1" size="16" />
				</view>
			</view>

			<view class="group-title">功能设置</view>
			<view class="settings-group">
				<view class="settings-item" @click="handleItemClick('category')">
					<view class="item-left">
						<van-icon name="apps-o" size="20" color="#1e293b" />
						<text class="item-title">类别设置</text>
					</view>
					<van-icon name="arrow" color="#cbd5e1" size="16" />
				</view>
				<view class="settings-item">
					<view class="item-left">
						<van-icon name="balance-list-o" size="20" color="#1e293b" />
						<view class="item-content">
							<text class="item-title">收支账户</text>
							<text class="item-desc">开启后，主账本记账时可选收支账户</text>
						</view>
					</view>
					<van-switch v-model="enableAccount" size="20px" active-color="#ffd541" />
				</view>
				<view class="settings-item" @click="handleItemClick('calendar')">
					<view class="item-left">
						<van-icon name="calendar-o" size="20" color="#1e293b" />
						<text class="item-title">日历设置</text>
					</view>
					<van-icon name="arrow" color="#cbd5e1" size="16" />
				</view>
				<view class="settings-item" @click="handleItemClick('monthStart')">
					<view class="item-left">
						<van-icon name="clock-o" size="20" color="#1e293b" />
						<text class="item-title">每月开始于</text>
					</view>
					<view class="item-right">
						<text class="value-text">1日</text>
						<van-icon name="arrow" color="#cbd5e1" size="16" />
					</view>
				</view>
				<view class="settings-item" @click="handleItemClick('defaultType')">
					<view class="item-left">
						<van-icon name="notes-o" size="20" color="#1e293b" />
						<text class="item-title">默认记账类型</text>
					</view>
					<view class="item-right">
						<text class="value-text">支出</text>
						<van-icon name="arrow" color="#cbd5e1" size="16" />
					</view>
				</view>
				<view class="settings-item" @click="handleItemClick('chart')">
					<view class="item-left">
						<van-icon name="chart-trending-o" size="20" color="#1e293b" />
						<text class="item-title">图表页设置</text>
					</view>
					<van-icon name="arrow" color="#cbd5e1" size="16" />
				</view>
			</view>

			<view class="group-title">个性化设置</view>
			<view class="settings-group">
				<view class="settings-item" @click="handleItemClick('sound')">
					<view class="item-left">
						<van-icon name="music-o" size="20" color="#1e293b" />
						<text class="item-title">声音与触感</text>
					</view>
					<van-icon name="arrow" color="#cbd5e1" size="16" />
				</view>
				<view class="settings-item" @click="handleItemClick('theme')">
					<view class="item-left">
						<van-icon name="brush-o" size="20" color="#1e293b" />
						<text class="item-title">个性装扮</text>
					</view>
					<van-icon name="arrow" color="#cbd5e1" size="16" />
				</view>
				<view class="settings-item" @click="handleItemClick('reminder')">
					<view class="item-left">
						<van-icon name="bell" size="20" color="#1e293b" />
						<text class="item-title">定时提醒</text>
					</view>
					<van-icon name="arrow" color="#cbd5e1" size="16" />
				</view>
			</view>

			<view class="group-title">社交与互动</view>
			<view class="settings-group">
				<view class="settings-item">
					<view class="item-left">
						<van-icon name="comment-o" size="20" color="#1e293b" />
						<view class="item-content">
							<text class="item-title">评论通知</text>
							<text class="item-desc">当有人回复您的动态或评论时提醒</text>
						</view>
					</view>
					<van-switch v-model="socialSettings.commentNotify" size="20px" active-color="#ffd541" />
				</view>
				<view class="settings-item">
					<view class="item-left">
						<van-icon name="good-job-o" size="20" color="#1e293b" />
						<view class="item-content">
							<text class="item-title">点赞通知</text>
							<text class="item-desc">当有人点赞您的动态或评论时提醒</text>
						</view>
					</view>
					<van-switch v-model="socialSettings.likeNotify" size="20px" active-color="#ffd541" />
				</view>
				<view class="settings-item" @click="handleItemClick('blacklist')">
					<view class="item-left">
						<van-icon name="shield-o" size="20" color="#1e293b" />
						<text class="item-title">黑名单管理</text>
					</view>
					<van-icon name="arrow" color="#cbd5e1" size="16" />
				</view>
			</view>
			
			<view class="logout-btn" @click="handleLogout">
				<text>退出登录</text>
			</view>

			<view class="version-info">
				<text>当前版本 1.0.0</text>
			</view>
		</scroll-view>
	</view>
</template>

<script setup>
import { ref } from 'vue';

const enableAccount = ref(false);

const socialSettings = ref({
	commentNotify: true,
	likeNotify: true
});

const goBack = () => {
	uni.navigateTo({
		url: '/pages/setting/center'
	});
};

const handleItemClick = (type) => {
	if (type === 'account') {
		uni.navigateTo({
			url: '/pages/page_setting/setting_function/account_setting/account'
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
				// 这里可以添加实际的退出逻辑，如清除 token 等
			}
		}
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

/* 导航栏 */
.nav-bar {
	display: flex;
	align-items: center;
	justify-content: space-between;
	padding: 14px 16px 10px;
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

.content-area {
	flex: 1;
	padding-bottom: 40px;
    overflow-y: auto;
}

/* 分组标题 */
.group-title {
	font-size: 13px;
	color: #64748b;
	margin: 20px 16px 8px;
	font-weight: 500;
}

/* 设置组 */
.settings-group {
	background-color: #fff;
	padding: 0 16px;
}

.first-group {
	margin-top: 10px;
}

/* 设置项 */
.settings-item {
	display: flex;
	justify-content: space-between;
	align-items: center;
	padding: 16px 0;
	border-bottom: 1px solid #f1f5f9;
}

.settings-group .settings-item:last-child {
	border-bottom: none;
}

.item-left {
	display: flex;
	align-items: center;
	gap: 12px;
	flex: 1;
}

.item-content {
	display: flex;
	flex-direction: column;
	gap: 2px;
}

.item-title {
	font-size: 15px;
	color: #1e293b;
	font-weight: 500;
}

.item-desc {
	font-size: 12px;
	color: #94a3b8;
}

.item-right {
	display: flex;
	align-items: center;
	gap: 4px;
}

.value-text {
	font-size: 14px;
	color: #64748b;
}

/* 退出登录按钮 */
.logout-btn {
	margin: 30px 16px 10px;
	background-color: #fff;
	height: 50px;
	display: flex;
	align-items: center;
	justify-content: center;
	border-radius: 8px;
	color: #ef4444;
	font-size: 16px;
	font-weight: 600;
}

.logout-btn:active {
	opacity: 0.8;
	background-color: #f8fafc;
}

.version-info {
	text-align: center;
	margin-top: 20px;
	font-size: 12px;
	color: #94a3b8;
}
</style>