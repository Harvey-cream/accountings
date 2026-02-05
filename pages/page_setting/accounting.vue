<template>
	<view class="my-container">
		<!-- 头部个人信息卡片 -->
		<view class="header-card">
			<view class="user-info">
				<image class="avatar" src="/static/4.jpg" mode="aspectFill"></image>
				<view class="user-detail">
					<text class="user-name">oxo</text>
				</view>
				<view class="check-in-btn" @click="toggleCheckIn">
					<van-icon :name="isChecked ? 'passed' : 'todo-list-o'" size="14" />
					<text class="check-in-text">{{ isChecked ? '已打卡' : '打卡' }}</text>
				</view>
			</view>

			<!-- 数据统计 -->
			<view class="stats-row">
				<view class="stat-item">
					<text class="stat-num">1</text>
					<text class="stat-label">已连续打卡</text>
				</view>
				<view class="stat-item">
					<text class="stat-num">32</text>
					<text class="stat-label">记账总天数</text>
				</view>
				<view class="stat-item">
					<text class="stat-num">16</text>
					<text class="stat-label">记账总笔数</text>
				</view>
			</view>

			<!-- VIP 升级入口 -->
			<view class="menu-card vip-card">
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
			<view class="action-item">
				<van-icon name="bell" color="#facc15" size="26" />
				<text class="action-label">消息</text>
			</view>
			<view class="action-item">
				<van-icon name="medal" color="#d97706" size="26" />
				<text class="action-label">我的勋章</text>
			</view>
			<view class="action-item">
				<van-icon name="gift" color="#3b82f6" size="26" />
				<text class="action-label">我的积分</text>
			</view>
			<view class="action-item">
				<van-icon name="smile" color="#f97316" size="26" />
				<text class="action-label">邀请好友</text>
			</view>
			<view class="action-item">
				<view class="dot-badge"></view>
				<van-icon name="setting" color="#475569" size="26" />
				<text class="action-label">设置</text>
			</view>
		</view>

		<!-- 菜单列表组 1 -->
		<view class="menu-group">
			<view class="menu-item">
				<view class="menu-left">
					<van-icon name="notes-o" size="20" color="#1e293b" />
					<text class="item-title">我的账本</text>
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

		<!-- 菜单列表组 2 -->
		<view class="menu-group">
			<view class="menu-item">
				<view class="menu-left">
					<van-icon name="setting-o" size="20" color="#1e293b" />
					<text class="item-title">设置</text>
				</view>
				<van-icon name="arrow" color="#cbd5e1" />
			</view>
			<view class="menu-item">
				<view class="menu-left">
					<van-icon name="question-o" size="20" color="#1e293b" />
					<text class="item-title">使用帮助</text>
				</view>
				<van-icon name="arrow" color="#cbd5e1" />
			</view>
			<view class="menu-item">
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

		<custom-tabbar />
	</view>
</template>

<script setup>
import { ref } from 'vue';
import CustomTabbar from '@/components/Tabbar/Tabbar.vue';

// 打卡状态
const isChecked = ref(false);

// 切换打卡状态
const toggleCheckIn = () => {
	isChecked.value = !isChecked.value;
	if (isChecked.value) {
		uni.showToast({
			title: '打卡成功',
			icon: 'success'
		});
	}
};
</script>

<style scoped>
.my-container {
	background-color: #f8fafc;
	min-height: 100vh;
	padding: 0 16px 100px;
}

/* 头部卡片 */
.header-card {
	background-color: #ffd541;
	margin: 0 -16px 35px;
	padding: 20px 16px 20px; 
}

.user-info {
	display: flex;
	align-items: center;
	margin-bottom: 30px;
	padding: 0 10px; /* 增加左右内边距，使内容往中间挤一点 */
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
	font-size: 24px;
	font-weight: 800;
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
	padding: 16px;
	box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02);
}

/* VIP 卡片 */
.vip-card {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-top: 24px;
	margin-bottom: -45px; 
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
	padding: 20px 10px;
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
</style>
