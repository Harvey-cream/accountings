<template>
	<view class="points-page" :class="currentThemeClass">
		<!-- 沉浸式头部 -->
		<view class="points-header">
			<view class="nav-bar">
				<view class="nav-left" @click="goBack">
					<van-icon name="arrow-left" size="20" />
				</view>
				<text class="nav-title">我的积分</text>
				<text class="nav-right" @click="showRules">规则</text>
			</view>
			
			<view class="points-display">
				<view class="points-value">
					<text class="number">{{ totalPoints }}</text>
					<text class="label">可用积分</text>
				</view>
				<view class="points-action" @click="goToHistory">
					<text>明细</text>
					<van-icon name="arrow" size="12" />
				</view>
			</view>
		</view>

		<!-- 悬浮卡片区 -->
		<view class="content-body">
			<!-- 签到模块 -->
			<view class="card check-in-card">
				<view class="card-header">
					<text class="card-title">每日签到</text>
					<text class="card-subtitle">已连续签到 {{ consecutiveDays }} 天</text>
				</view>
				
				<view class="check-in-steps">
					<view 
						v-for="(day, index) in weekDays" 
						:key="index" 
						class="step-item"
						:class="{ 'active': index < consecutiveDays, 'today': index === consecutiveDays && !isCheckedToday }"
					>
						<view class="step-circle">
							<van-icon v-if="index < consecutiveDays" name="success" color="#fff" size="12" />
							<text v-else class="step-points">+{{ day.points }}</text>
						</view>
						<text class="step-label">{{ day.label }}</text>
					</view>
				</view>
				
				<button 
					class="check-in-btn" 
					:class="{ 'disabled': isCheckedToday }"
					@click="handleCheckIn"
				>
					{{ isCheckedToday ? '今日已签到' : '立即签到领积分' }}
				</button>
			</view>

			<!-- 任务列表 -->
			<view class="card task-card">
				<view class="card-header">
					<text class="card-title">赚取积分</text>
				</view>
				
				<view class="task-list">
					<view v-for="(task, index) in taskList" :key="index" class="task-item">
						<view class="task-icon" :style="{ background: task.bgColor }">
							<van-icon :name="task.icon" size="20" :color="task.iconColor" />
						</view>
						<view class="task-info">
							<text class="task-name">{{ task.name }}</text>
							<text class="task-reward">+{{ task.reward }} 积分</text>
						</view>
						<button 
							class="task-btn" 
							:class="{ 'completed': task.completed }"
							@click="handleTask(task)"
						>
							{{ task.completed ? '已完成' : task.btnText }}
						</button>
					</view>
				</view>
			</view>
			
			<!-- 兑换推荐 (简单的横向滚动) -->
			<view class="card exchange-card">
				<view class="card-header">
					<text class="card-title">积分兑换</text>
					<view class="more-link">
						<text>更多</text>
						<van-icon name="arrow" size="12" color="#94a3b8" />
					</view>
				</view>
				<scroll-view scroll-x class="exchange-scroll" show-scrollbar="false">
					<view class="exchange-list">
						<view v-for="(item, index) in exchangeItems" :key="index" class="exchange-item">
							<image :src="item.image" mode="aspectFill" class="exchange-img"></image>
							<text class="exchange-name">{{ item.name }}</text>
							<text class="exchange-price">{{ item.points }} 积分</text>
						</view>
					</view>
				</scroll-view>
			</view>
		</view>
	</view>
</template>

<script setup>
import { ref, computed } from 'vue';

const goBack = () => uni.navigateBack();

// 状态数据
const totalPoints = ref(1280);
const consecutiveDays = ref(2);
const isCheckedToday = ref(false);

// 签到配置
const weekDays = computed(() => {
	const now = new Date();
	return Array.from({ length: 7 }, (_, i) => {
		const d = new Date(now.getFullYear(), now.getMonth(), now.getDate() - 2 + i); // 模拟从前两天开始显示
		const month = d.getMonth() + 1;
		const date = d.getDate();
		return {
			label: `${month}.${date < 10 ? '0' + date : date}`,
			points: i === 6 ? 10 : i + 1
		};
	});
});

// 任务列表
const taskList = ref([
	{ 
		id: 1, 
		name: '每日记账', 
		reward: 5, 
		icon: 'records', 
		bgColor: '#e0f2fe', 
		iconColor: '#0ea5e9',
		btnText: '去记账',
		completed: false 
	},
	{ 
		id: 2, 
		name: '邀请好友', 
		reward: 50, 
		icon: 'friends', 
		bgColor: '#fef3c7', 
		iconColor: '#d97706',
		btnText: '去邀请',
		completed: false 
	},
	{ 
		id: 3, 
		name: '完善个人信息', 
		reward: 20, 
		icon: 'manager', 
		bgColor: '#dcfce7', 
		iconColor: '#22c55e',
		btnText: '去完善',
		completed: true 
	}
]);

// 兑换商品
const exchangeItems = ref([
	{ name: 'VIP月卡', points: 500, image: '/static/vip-card.png' }, // 这里的图片路径仅为示例
	{ name: '记账本皮肤', points: 300, image: '/static/skin.png' },
	{ name: '导出功能', points: 200, image: '/static/export.png' },
	{ name: '补签卡', points: 100, image: '/static/card.png' },
]);

// 交互逻辑
const handleCheckIn = () => {
	if (isCheckedToday.value) return;
	isCheckedToday.value = true;
	consecutiveDays.value++;
	totalPoints.value += weekDays.value[consecutiveDays.value - 1]?.points || 1;
	uni.showToast({ title: '签到成功', icon: 'success' });
};

const handleTask = (task) => {
	if (task.completed) return;
	if (task.name === '每日记账') {
		uni.navigateTo({ url: '/pages/page_saved/save_accouting' });
	} else if (task.name === '邀请好友') {
		uni.switchTab({ url: '/pages/setting/center' });
	}
};

const showRules = () => {
	uni.showModal({
		title: '积分规则',
		content: '1. 每日签到可获得积分，连续签到奖励更多。\n2. 完成每日任务可获得额外积分。\n3. 积分可用于兑换会员权益和个性化皮肤。',
		showCancel: false,
		confirmText: '知道了',
		confirmColor: '#ffd541'
	});
};

const goToHistory = () => {
	uni.showToast({ title: '查看积分明细', icon: 'none' });
};
</script>

<style scoped>
.points-page {
	min-height: 100vh;
	background-color: #f8fafc;
}

/* 头部样式 */
.points-header {
	background-color: var(--main-color);
	padding: calc(var(--status-bar-height) + 14px) 16px 60px; /* 底部留白给悬浮卡片 */
	color: var(--main-text-color);
	position: relative;
}

.nav-bar {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 24px;
}

.nav-title {
	position: absolute;
	left: 50%;
	transform: translateX(-50%);
	font-size: 18px;
	font-weight: 600;
	white-space: nowrap;
}

.nav-right {
	width: 60px;
	text-align: right;
	font-size: 14px;
	opacity: 0.9;
}

.points-display {
	display: flex;
	flex-direction: column;
	align-items: center;
	position: relative;
}

.points-value {
	display: flex;
	flex-direction: column;
	align-items: center;
}

.points-value .number {
	font-size: 48px;
	font-weight: bold;
	line-height: 1;
	margin-bottom: 8px;
}

.points-value .label {
	font-size: 14px;
	opacity: 0.8;
}

.points-action {
	position: absolute;
	right: 0;
	bottom: 0;
	display: flex;
	align-items: center;
	gap: 4px;
	background-color: rgba(255, 255, 255, 0.2);
	padding: 4px 10px;
	border-radius: 12px;
	font-size: 12px;
}

.points-value .label {
	font-size: 14px;
	opacity: 0.9;
}

.points-action {
	background-color: rgba(255, 255, 255, 0.2);
	padding: 6px 12px;
	border-radius: 20px;
	font-size: 12px;
	display: flex;
	align-items: center;
	gap: 4px;
}

/* 内容区域 */
.content-body {
	margin-top: -40px; /* 负边距实现悬浮效果 */
	padding: 0 16px 40px;
	position: relative;
	z-index: 10;
}

/* 通用卡片样式 */
.card {
	background-color: #fff;
	border-radius: 16px;
	padding: 20px;
	margin-bottom: 16px;
	box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

.card-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 16px;
}

.card-title {
	font-size: 16px;
	font-weight: bold;
	color: #1e293b;
}

.card-subtitle {
	font-size: 12px;
	color: #64748b;
}

/* 签到卡片 */
.check-in-steps {
	display: flex;
	justify-content: space-between;
	margin-bottom: 24px;
}

.step-item {
	display: flex;
	flex-direction: column;
	align-items: center;
	gap: 8px;
	position: relative;
	flex: 1;
}

/* 连接线 */
.step-item:not(:last-child)::after {
	content: '';
	position: absolute;
	top: 14px;
	left: 50%;
	width: 100%;
	height: 2px;
	background-color: #f1f5f9;
	z-index: 0;
}

.step-item.active:not(:last-child)::after {
	background-color: #fcd34d;
}

.step-circle {
	width: 28px;
	height: 28px;
	border-radius: 50%;
	background-color: #f1f5f9;
	display: flex;
	align-items: center;
	justify-content: center;
	z-index: 1;
	transition: all 0.3s;
}

.step-item.active .step-circle {
	background-color: #f59e0b;
	color: #fff;
}

.step-item.today .step-circle {
	border: 2px solid #f59e0b;
	background-color: #fff;
	color: #f59e0b;
}

.step-points {
	font-size: 10px;
	font-weight: bold;
	color: #94a3b8;
}
.step-item.active .step-points { color: #fff; }
.step-item.today .step-points { color: #f59e0b; }

.step-label {
	font-size: 10px;
	color: #94a3b8;
}

.check-in-btn {
	background: linear-gradient(90deg, #f59e0b, #fbbf24);
	color: #fff;
	border: none;
	border-radius: 24px;
	font-size: 16px;
	font-weight: 600;
	height: 44px;
	line-height: 44px;
	box-shadow: 0 4px 12px rgba(245, 158, 11, 0.3);
}

.check-in-btn.disabled {
	background: #e2e8f0;
	color: #94a3b8;
	box-shadow: none;
}

/* 任务列表 */
.task-item {
	display: flex;
	align-items: center;
	padding: 12px 0;
	border-bottom: 1px solid #f8fafc;
}
.task-item:last-child { border-bottom: none; }

.task-icon {
	width: 40px;
	height: 40px;
	border-radius: 12px;
	display: flex;
	align-items: center;
	justify-content: center;
	margin-right: 12px;
}

.task-info {
	flex: 1;
}

.task-name {
	font-size: 14px;
	font-weight: 600;
	color: #333;
	display: block;
	margin-bottom: 4px;
}

.task-reward {
	font-size: 12px;
	color: #f59e0b;
	font-weight: 500;
}

.task-btn {
	font-size: 12px;
	padding: 0 16px;
	height: 28px;
	line-height: 28px;
	border-radius: 14px;
	background-color: #fff;
	color: #f59e0b;
	border: 1px solid #f59e0b;
	margin: 0;
}

.task-btn.completed {
	background-color: #f1f5f9;
	color: #94a3b8;
	border-color: transparent;
}

/* 兑换推荐 */
.more-link {
	font-size: 12px;
	color: #94a3b8;
	display: flex;
	align-items: center;
}

.exchange-scroll {
	width: 100%;
	white-space: nowrap;
}

.exchange-list {
	display: flex;
	gap: 12px;
}

.exchange-item {
	display: inline-flex;
	flex-direction: column;
	width: 100px;
	flex-shrink: 0;
}

.exchange-img {
	width: 100px;
	height: 100px;
	background-color: #f1f5f9;
	border-radius: 8px;
	margin-bottom: 8px;
}

.exchange-name {
	font-size: 13px;
	color: #333;
	margin-bottom: 2px;
	overflow: hidden;
	text-overflow: ellipsis;
	white-space: nowrap;
}

.exchange-price {
	font-size: 12px;
	color: #f59e0b;
	font-weight: 600;
}
</style>