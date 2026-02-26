<template>
	<view class="page-container" :class="currentThemeClass">
		<view class="tab-content">
			<view class="header">
				<view class="status-bar">
				</view>
				<view class="summary-row">
					<view class="month-selector" @click="showMonthPicker = true">
						<text class="year-text">{{ summary.year }}年</text>
						<view class="month-display">
							<text class="month-text font-number">{{ summary.month }}</text>
						<text class="month-unit">月</text>
						<van-icon name="arrow-down" size="12" color="#0f172a" class="arrow-icon" />
					</view>
				</view>
				
				<view class="divider"></view>

				<view class="stat-group">
					<view class="stat-item">
						<text class="stat-label">收入</text>
						<text class="stat-value ">{{ summary.income }}</text>
					</view>
					<view class="stat-item">
						<text class="stat-label">支出</text>
						<text class="stat-value ">{{ summary.expense }}</text>
					</view>
				</view>
			</view>
		</view>
		<view class="quick-actions">
			<van-grid :column-num="5" :border="false" :gutter="10">
				<van-grid-item v-for="action in quickActions" :key="action.id" @click="onActionClick(action)">
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
		<view class="transactions-section">
			<van-list v-model:loading="loading" :finished="finished" finished-text="没有更多了" @load="onLoad">
				<view v-for="group in dailyTransactions" :key="group.id" class="day-group">
					<view class="day-header">
						<text class="day-date">{{ group.date }}</text>
						<text class="text-style-desc">支出: {{ group.totalExpense }}</text>
					</view>

					<view class="list-container">
						<van-swipe-cell v-for="item in group.items" :key="item.id" right-width="65">
							<van-cell center class="custom-cell flat-cell">
								<template #icon>
									<view :class="['list-icon-wrap', item.iconBg]">
										<van-icon :name="item.icon" :color="item.iconColor" size="20" />
									</view>
								</template>
								<template #title>
									<view class="cell-content">
										<view class="cell-main">
											<text class="cell-title text-style-title">{{ item.title }}</text>
											<text class="cell-time text-style-desc">{{ item.time }} · {{ item.location }}</text>
										</view>
										<view class="cell-right">
											<text class="cell-amount text-style-number">{{ item.amount }}</text>
										</view>
									</view>
								</template>
							</van-cell>
							<template #right>
								<view class="delete-button" @click="onDelete(group.id, item.id)">
									<van-icon name="delete-o" size="24" color="#fff" />
								</view>
							</template>
						</van-swipe-cell>
					</view>
				</view>
			</van-list>
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
	year: '2025',
	month: '12',
	expense: '26,510.00',
	income: '4,200.00'
});

const quickActions = ref([
	{ id: 1, name: '账单', icon: 'notes-o', bgColor: 'bg-amber', iconColor: '#f59e0b' },
	{ id: 2, name: '预算', icon: 'balance-o', bgColor: 'bg-blue', iconColor: '#3b82f6' },
	{ id: 3, name: '资产', icon: 'gold-coin-o', bgColor: 'bg-emerald', iconColor: '#10b981' },
	{ id: 4, name: '发票', icon: 'records', bgColor: 'bg-rose', iconColor: '#f43f5e' },
	{ id: 5, name: '更多', icon: 'apps-o', bgColor: 'bg-slate', iconColor: '#64748b' }
]);

const onActionClick = (action) => {
	if (action.name === '账单') {
		uni.navigateTo({
			url: '/pages/page_home/page_bill/BillList'
		});
	} else if (action.name === '预算') {
		uni.navigateTo({
			url: '/pages/page_home/page_budget/budget'
		});
	} else if (action.name === '资产') {
		uni.navigateTo({
			url: '/pages/page_home/page_asset/asset'
		});
	} else if (action.name === '发票') {
		uni.navigateTo({
			url: '/pages/page_home/page_invoice/invoice'
		});
	}
};

const dailyTransactions = ref([]);

const onLoad = () => {
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
	});
};

const onDelete = (groupId, itemId) => {
	uni.showModal({
		title: '提示',
		content: '确定要删除这条记录吗？',
		success: (res) => {
			if (res.confirm) {
				const groupIndex = dailyTransactions.value.findIndex(g => g.id === groupId);
				if (groupIndex > -1) {
					const group = dailyTransactions.value[groupIndex];
					const itemIndex = group.items.findIndex(i => i.id === itemId);
					if (itemIndex > -1) {
						group.items.splice(itemIndex, 1);
						uni.showToast({
							title: '删除成功',
							icon: 'success'
						});
						
						// 如果该组没有任何条目了，也移除该组
						if (group.items.length === 0) {
							dailyTransactions.value.splice(groupIndex, 1);
						}
					}
				}
			}
		}
	});
};

const navItems = ref([
	{ id: 1, name: '明细', icon: 'list-switch', active: true },
	{ id: 2, name: '图表', icon: 'chart-trending-o', active: false },
	{ id: 3, name: '记账', icon: 'plus', isFab: true },
	{ id: 4, name: '发现', icon: 'search', active: false },
	{ id: 5, name: '我的', icon: 'user-o', active: false }
]);

const onMonthConfirm = ({ selectedValues }) => {
	summary.value.year = selectedValues[0];
	summary.value.month = selectedValues[1];
	showMonthPicker.value = false;
};
</script>

<style scoped>
.page-container {
	min-height: 100vh;
	padding-bottom: 70px;
}

/* Header Styles */
.header {
	background-color: #ffd541;
	padding: 20px 20px 0px;
	position: relative;
}

.status-bar {
	display: flex;
	justify-content: flex-end;
	align-items: center;
}

.status-icons {
	display: flex;
	gap: 6px;
}

.rotate-90 {
	transform: rotate(90deg);
}

.summary-row {
	display: flex;
	align-items: center;
	position: relative;
	z-index: 10;
	height: 60px;
	bottom: 10px;
	flex: 1;
}

.month-selector {
	display: flex;
	flex-direction: column;
	justify-content: center;
	cursor: pointer;
}

.year-text {
	font-size: 12px;
	color: var(--secondary-text-color);
	margin-bottom: 2px;
	line-height: 1;
}

.month-display {
	display: flex;
	align-items: baseline;
	gap: 2px;
	line-height: 1;
}

.month-text {
	font-size: 28px;
	font-weight: 500;
}

.month-unit {
	font-size: 14px;
	margin-right: 4px;
}

.arrow-icon {
	margin-bottom: 2px;
}

.divider {
	width: 1px;
	background-color: rgba(0, 0, 0, 0.1);
	margin: 0 20px;
}

.stat-group {
	flex: 1;
	display: flex;
	justify-content: flex-start;
	gap: 60px;
	min-width: 0;
}

.stat-item {
	display: flex;
	flex-direction: column;
	min-width: 0;
}

.stat-label {
	font-size: 12px;
	color: var(--secondary-text-color);
}

.stat-value {
	font-size: 20px;
	font-weight: 300;
	white-space: nowrap;
	overflow: hidden;
	text-overflow: ellipsis;
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
	color: var(--secondary-text-color);
}

/* Action Colors */
.bg-amber, .bg-blue, .bg-emerald, .bg-rose, .bg-slate {
	background-color: var(--secondary-bg-color);
}

/* Transactions */
.transactions-section {
	margin-top: 22px;
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
}
.custom-cell {
	background-color: transparent;
	border-radius: 0;
	margin-bottom: 0;
	padding: 16px 20px !important;
	border-bottom: 1px solid #f1f5f9;
}

.custom-cell:last-child {
	border-bottom: none;
}

.flat-cell {
	background-color: transparent !important;
}

.list-icon-wrap {
	width: 40px;
	height: 40px;
	border-radius: 12px;
	display: flex;
	align-items: center;
	justify-content: center;
	margin-right: 12px;
}

.cell-content {
	display: flex;
	justify-content: space-between;
	align-items: center;
	width: 100%;
}

.cell-main {
	display: flex;
	flex-direction: column;
}

.cell-time {
	margin-top: 2px;
}

.cell-right {
	display: flex;
	flex-direction: column;
	align-items: flex-end;
}
/* Item Colors */
.bg-amber-light, .bg-blue-light, .bg-purple-light, .bg-emerald-light {
	background-color: var(--secondary-bg-color);
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
	color: var(--accent-color);
}

.delete-button {
	height: 100%;
	width: 65px;
	background-color: #ee0a24;
	display: flex;
	justify-content: center;
	align-items: center;
}
</style>
