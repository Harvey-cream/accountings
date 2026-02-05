<template>
	<view class="page-container">
		<!-- Main Content Area: Detail View -->
		<view class="tab-content">
			<!-- Header Area -->
			<view class="header">
				<view class="status-bar">
					<view class="status-icons">
						<van-icon name="signal-full" size="16" />
						<van-icon name="wifi" size="16" />
						<van-icon name="battery-full" size="16" class="rotate-90" />
					</view>
				</view>

				<view class="header-content">
					<text class="title">每月账单明细</text>
					<view class="header-actions">
						<view class="icon-btn">
							<van-icon name="bell" size="20" />
						</view>
					</view>
				</view>
			</view>

			<!-- Summary Card -->
			<view class="summary-card">
				<view class="summary-header">
					<view class="month-selector" @click="showMonthPicker = true">
						<text class="month-text">{{ summary.month }}</text>
						<van-icon name="arrow-down" color="#94a3b8" />
					</view>
					<van-tag round type="primary" color="#f1f5f9" text-color="#64748b" class="badge">账单概览</van-tag>
				</view>
				<view class="summary-stats">
					<view class="stat-item">
						<text class="stat-label">本月支出</text>
						<text class="stat-value">{{ summary.expense }}</text>
					</view>
					<view class="stat-item border-left">
						<text class="stat-label">本月收入</text>
						<text class="stat-value">{{ summary.income }}</text>
					</view>
				</view>
			</view>

			<!-- Quick Actions Grid -->
			<view class="quick-actions">
				<van-grid :column-num="5" :border="false" :gutter="10">
					<van-grid-item v-for="action in quickActions" :key="action.id">
						<template #icon>
							<view :class="['action-icon-wrap', action.bgColor]">
								<van-icon :name="action.icon" :color="action.iconColor" size="24" />
							</view>
						</template>
						<template #text>
							<text class="action-name">{{ action.name }}</text>
						</template>
					</van-grid-item>
				</van-grid>
			</view>

			<!-- Transactions Section -->
			<view class="transactions-section">
				<van-list v-model:loading="loading" :finished="finished" finished-text="没有更多了" @load="onLoad">
					<view v-for="group in dailyTransactions" :key="group.id" class="day-group">
						<view class="day-header">
							<text class="day-date">{{ group.date }}</text>
							<text class="day-total">支出: {{ group.totalExpense }}</text>
						</view>

						<van-cell-group inset class="transaction-list">
							<van-cell v-for="item in group.items" :key="item.id" center class="transaction-card">
								<template #icon>
									<view :class="['item-icon-wrap', item.iconBg]">
										<van-icon :name="item.icon" :color="item.iconColor" size="24" />
									</view>
								</template>
								<template #title>
									<view class="item-main">
										<text class="item-title">{{ item.title }}</text>
										<text class="item-amount">{{ item.amount }}</text>
									</view>
								</template>
								<template #label>
									<text class="item-details">{{ item.time }} · {{ item.location }}</text>
								</template>
							</van-cell>
						</van-cell-group>
					</view>
				</van-list>
			</view>

			<!-- Map FAB -->
			<view class="fab-map">
				<van-icon name="location-o" size="24" />
			</view>

			<!-- Month Picker Popup -->
			<van-popup v-model:show="showMonthPicker" position="bottom">
				<van-date-picker
					v-model="currentDateArray"
					title="选择月份"
					:min-date="minDate"
					:max-date="maxDate"
					:columns-type="['year', 'month']"
					@confirm="onMonthConfirm"
					@cancel="showMonthPicker = false"
				/>
			</van-popup>
		</view>
		<custom-tabbar />
	</view>
</template>

<script setup>
import { ref } from 'vue';
import CustomTabbar from '@/components/Tabbar/Tabbar.vue';

const showMonthPicker = ref(false);
const currentDateArray = ref(['2025', '12']);
const minDate = new Date(2020, 0, 1);
const maxDate = new Date(2025, 11, 31);
const activeNav = ref(0);

const loading = ref(false);
const finished = ref(false);

const summary = ref({
	month: '2025年12月',
	expense: '26,521.00',
	income: '4,250.00'
});

const quickActions = ref([
	{ id: 1, name: '账单', icon: 'notes-o', bgColor: 'bg-amber', iconColor: '#f59e0b' },
	{ id: 2, name: '预算', icon: 'balance-o', bgColor: 'bg-blue', iconColor: '#3b82f6' },
	{ id: 3, name: '资产', icon: 'gold-coin-o', bgColor: 'bg-emerald', iconColor: '#10b981' },
	{ id: 4, name: '返现', icon: 'gift-o', bgColor: 'bg-rose', iconColor: '#f43f5e' },
	{ id: 5, name: '更多', icon: 'apps-o', bgColor: 'bg-slate', iconColor: '#64748b' }
]);

const dailyTransactions = ref([]);

const onLoad = () => {
	// 模拟异步加载
	setTimeout(() => {
		// 模拟生成更多历史数据
		const lastId = dailyTransactions.value.length ? dailyTransactions.value[dailyTransactions.value.length - 1].id : 0;
		const newData = [
			{
				id: lastId + 1,
				date: '12月' + (31 - lastId) + '日 星期' + ['三', '二', '一', '日', '六', '五', '四'][lastId % 7],
				totalExpense: '16,246.00',
				items: [
					{
						id: (lastId + 1) * 100 + 1,
						title: '育儿费用',
						amount: '-4,225.00',
						time: '14:20',
						location: '幼儿园生活区',
						icon: 'smile-o',
						iconBg: 'bg-amber-light',
						iconColor: '#d97706'
					},
					{
						id: (lastId + 1) * 100 + 2,
						title: '办公租赁',
						amount: '-6,466.00',
						time: '10:30',
						location: '科技园园区',
						icon: 'shop-o',
						iconBg: 'bg-blue-light',
						iconColor: '#2563eb'
					},
					{
						id: (lastId + 1) * 100 + 3,
						title: '交通保险',
						amount: '-5,555.00',
						time: '09:15',
						location: '私家车月度车险',
						icon: 'logistics',
						iconBg: 'bg-purple-light',
						iconColor: '#9333ea'
					}
				]
			},
			{
				id: lastId + 2,
				date: '12月' + (30 - lastId) + '日 星期' + ['二', '一', '日', '六', '五', '四', '三'][lastId % 7],
				totalExpense: '5,225.00',
				items: [
					{
						id: (lastId + 2) * 100 + 1,
						title: '医疗健康',
						amount: '-5,225.00',
						time: '16:45',
						location: '市立医院',
						icon: 'hospital-o',
						iconBg: 'bg-emerald-light',
						iconColor: '#059669'
					}
				]
			}
		];

		dailyTransactions.value.push(...newData);
		loading.value = false;

		// 数据加载完毕
		if (dailyTransactions.value.length >= 10) {
			finished.value = true;
		}
	}, 1000);
};

const navItems = ref([
	{ id: 1, name: '明细', icon: 'list-switch', active: true },
	{ id: 2, name: '图表', icon: 'chart-trending-o', active: false },
	{ id: 3, name: '记账', icon: 'plus', isFab: true },
	{ id: 4, name: '发现', icon: 'search', active: false },
	{ id: 5, name: '我的', icon: 'user-o', active: false }
]);

const onMonthConfirm = ({ selectedValues }) => {
	summary.value.month = `${selectedValues[0]}年${selectedValues[1]}月`;
	showMonthPicker.value = false;
};
</script>

<style scoped>
.page-container {
	font-family: 'Inter', -apple-system, sans-serif;
	background-color: #f7f8fa;
	min-height: 100vh;
	padding-bottom: 70px;
}

/* Header Styles */
.header {
	background-color: #ffd541;
	padding: 10px 20px 60px;
	position: relative;
}

.status-bar {
	height: 20px;
	display: flex;
	justify-content: flex-end;
	align-items: center;
}

.time {
	font-size: 14px;
	font-weight: 700;
	color: #0f172a;
}

.status-icons {
	display: flex;
	gap: 6px;
	color: #0f172a;
}

.rotate-90 {
	transform: rotate(90deg);
}

.header-content {
	margin-top: 5px;
	display: flex;
	justify-content: space-between;
	align-items: center;
}

.title {
	font-size: 20px;
	font-weight: 700;
	color: #0f172a;
}

.header-actions {
	display: flex;
	gap: 12px;
}

.icon-btn {
	background-color: rgba(255, 255, 255, 0.3);
	padding: 8px;
	border-radius: 50%;
	color: #0f172a;
	display: flex;
	align-items: center;
	justify-content: center;
}

/* Summary Card */
.summary-card {
	margin: -40px 20px 0;
	background-color: #ffffff;
	border-radius: 24px;
	padding: 24px;
	box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
	position: relative;
	z-index: 10;
}

.summary-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 24px;
}

.month-selector {
	display: flex;
	align-items: center;
	gap: 4px;
}

.month-text {
	font-size: 24px;
	font-weight: 700;
	color: #0f172a;
}

.summary-stats {
	display: flex;
}

.stat-item {
	flex: 1;
}

.border-left {
	border-left: 1px solid #f1f5f9;
	padding-left: 32px;
}

.stat-label {
	font-size: 12px;
	color: #94a3b8;
	display: block;
	margin-bottom: 4px;
}

.stat-value {
	font-size: 24px;
	font-weight: 700;
	color: #0f172a;
}

/* Quick Actions */
.quick-actions {
	margin: 24px 10px 0;
}

:deep(.van-grid-item__content) {
	background-color: transparent;
	padding: 8px 0;
}

.action-item {
	display: flex;
	flex-direction: column;
	align-items: center;
}

.action-icon-wrap {
	width: 48px;
	height: 48px;
	border-radius: 16px;
	display: flex;
	align-items: center;
	justify-content: center;
	margin-bottom: 6px;
}

.action-name {
	font-size: 11px;
	font-weight: 500;
	color: #475569;
}

/* Action Colors */
.bg-amber {
	background-color: #fffbeb;
}
.bg-blue {
	background-color: #eff6ff;
}
.bg-emerald {
	background-color: #ecfdf5;
}
.bg-rose {
	background-color: #fff1f2;
}
.bg-slate {
	background-color: #f1f5f9;
}

/* Transactions */
.transactions-section {
	margin-top: 22px;
	padding: 0 0px;
}

.day-group {
	margin-bottom: 24px;
}

.day-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 12px;
	padding: 0 20px;
}

.day-date {
	font-size: 14px;
	font-weight: 700;
	color: #0f172a;
}

.day-total {
	font-size: 12px;
	font-weight: 500;
	color: #94a3b8;
}

.transaction-list {
	margin: 0 !important;
}

.transaction-card {
	padding: 16px !important;
	border-radius: 20px !important;
	margin-bottom: 12px;
	box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05);
}

.item-icon-wrap {
	width: 44px;
	height: 44px;
	border-radius: 12px;
	display: flex;
	align-items: center;
	justify-content: center;
	margin-right: 16px;
}

.item-main {
	display: flex;
	justify-content: space-between;
	align-items: center;
	width: 100%;
}

.item-title {
	font-weight: 700;
	color: #0f172a;
	font-size: 16px;
}

.item-amount {
	font-weight: 700;
	color: #0f172a;
	font-size: 16px;
}

.item-details {
	font-size: 12px;
	color: #94a3b8;
	margin-top: 2px;
}

/* Item Colors */
.bg-amber-light {
	background-color: #fef3c7;
}
.bg-blue-light {
	background-color: #dbeafe;
}
.bg-purple-light {
	background-color: #f3e8ff;
}
.bg-emerald-light {
	background-color: #d1fae5;
}

/* FAB Map */
.fab-map {
	position: fixed;
	bottom: calc(var(--window-bottom) + 20px);
	right: 20px;
	width: 48px;
	height: 48px;
	background-color: #ffffff;
	border-radius: 50%;
	display: flex;
	align-items: center;
	justify-content: center;
	border: 1px solid #f1f5f9;
	color: #f59e0b;
}
</style>
