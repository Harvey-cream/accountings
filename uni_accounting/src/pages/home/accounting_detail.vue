<template>
	<view class="page-container" :class="currentThemeClass">
		<view class="tab-content">
			<view class="header">
				<view class="status-bar"></view>
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
							<text class="stat-value">{{ summary.income }}</text>
						</view>
						<view class="stat-item">
							<text class="stat-label">支出</text>
							<text class="stat-value">{{ summary.expense }}</text>
						</view>
					</view>
				</view>
			</view>
			<view class="quick-actions">
				<van-grid :column-num="5" :border="false" :gutter="8">
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
							<text class="text-style-desc">{{ group.date }}</text>
							<text class="text-style-desc">{{ getDaySummary(group) }}</text>
						</view>

						<view class="list-container">
							<van-swipe-cell v-for="(item, index) in group.items" :key="item.id" right-width="65">
								<van-cell center :class="['custom-cell', 'flat-cell', { 'last-item': index === group.items.length - 1 }]">
									<template #icon>
										<view class="list-icon-wrap" :style="item.iconBgStyle">
											<van-icon :name="item.icon" :color="item.iconColorStyle" size="20" />
										</view>
									</template>
									<template #title>
										<view class="cell-content">
											<view class="cell-main">
												<text class="cell-title text-style-title">{{ item.remark || item.title }}</text>
												<view class="cell-sub-info">
													<text v-if="item.location" class="cell-location text-style-desc">{{ item.location }}</text>
												</view>
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
			<van-popup v-model:show="showMonthPicker" position="bottom">
				<van-datetime-picker
					v-model="currentDate"
					type="year-month"
					title="选择月份"
					:min-date="minDate"
					:max-date="maxDate"
					@confirm="onMonthConfirm"
					@cancel="showMonthPicker = false"
				/>
			</van-popup>
		</view>
		<custom-tabbar />
	</view>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { onShow } from '@dcloudio/uni-app';
import CustomTabbar from '@/components/Tabbar/Tabbar.vue';
import { getBills, deleteBill, getBillSummary } from '@/api/api.js';
import { colorPairs } from '@/utils/color.js';

const showMonthPicker = ref(false);
const currentDate = ref(new Date());
const minDate = new Date(2020, 0, 1);
const maxDate = new Date(2030, 11, 31);
const activeNav = ref(0);

const loading = ref(false);
const finished = ref(false);

const summary = ref({
	year: new Date().getFullYear().toString(),
	month: (new Date().getMonth() + 1).toString().padStart(2, '0'),
	expense: '0.00',
	income: '0.00'
});

const quickActions = ref([
	{ id: 1, name: '账单', icon: 'notes-o', bgColor: 'bg-action-amber', iconColor: '#f59e0b' },
	{ id: 2, name: '预算', icon: 'balance-o', bgColor: 'bg-action-blue', iconColor: '#3b82f6' },
	{ id: 3, name: '资产', icon: 'gold-coin-o', bgColor: 'bg-action-emerald', iconColor: '#10b981' },
	{ id: 4, name: '发票', icon: 'records', bgColor: 'bg-action-rose', iconColor: '#f43f5e' },
	{ id: 5, name: '更多', icon: 'apps-o', bgColor: 'bg-action-slate', iconColor: '#64748b' }
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

// 获取月度/年度汇总统计 (使用新接口)
const fetchSummary = async () => {
	try {
		const res = await getBillSummary(summary.value.year);
		if (res.code === 0) {
			const data = res.data;
			// 从月度明细中找到当前选中的月份
			const currentMonthData = data.monthBills.find(m => m.month === parseInt(summary.value.month).toString());
			if (currentMonthData) {
				summary.value.expense = currentMonthData.expense;
				summary.value.income = currentMonthData.income;
			} else {
				summary.value.expense = '0.00';
				summary.value.income = '0.00';
			}
		}
	} catch (e) {
		console.error('获取汇总统计失败:', e);
	}
};

const onLoad = async () => {
	// 如果正在加载，直接返回，避免重复请求
	if (loading.value) return;

	loading.value = true;
	try {
		// 1. 获取汇总统计
		fetchSummary();

		// 2. 获取当前年月的账单明细
		const res = await getBills({
			year: summary.value.year,
			month: summary.value.month
		});

		if (res.code === 0) {
			// console.log('账单原始数据:', JSON.stringify(res.data));
			// 直接使用后端返回的已分组数据
			const formattedData = res.data.map((group) => {
				return {
					...group,
					items: group.items.map((item) => {
						// console.log(`账单项 ID: ${item.id}, 标题: ${item.title}, 图标: ${item.icon}, ID: ${item.icon_id}`);
						// 根据 icon_id 从 color.js 中取色，确保颜色与保存账单时一致
						const colorIndex = Number(item.icon_id) % colorPairs.length;
						const colors = colorPairs[colorIndex];
						return {
							...item,
							icon: item.icon || 'notes-o', 
							iconBgStyle: `background-color: ${colors.bg}`,
							iconColorStyle: colors.icon
						};
					})
				};
			});

			dailyTransactions.value = formattedData;
		}
	} catch (e) {
		console.error('获取账单列表失败:', e);
	} finally {
		loading.value = false;
		finished.value = true;
	}
};

// 页面每次显示时（包括从保存页面返回时）都重新刷新数据
onShow(() => {
	finished.value = false; // 重置完成状态以允许 onLoad 运行
	onLoad();
});

onMounted(() => {
	// 初始加载由 onShow 负责
});

const onDelete = (groupId, itemId) => {
	uni.showModal({
		title: '提示',
		content: '确定要删除这条记录吗？',
		success: async (res) => {
			if (res.confirm) {
				try {
					const deleteRes = await deleteBill(itemId);
					if (deleteRes.code === 0) {
						uni.showToast({
							title: '删除成功',
							icon: 'success'
						});
						// 重新加载数据以同步最新统计和列表
						onLoad();
					} else {
						uni.showToast({
							title: deleteRes.msg || '删除失败',
							icon: 'none'
						});
					}
				} catch (e) {
					console.error('删除账单失败:', e);
					uni.showToast({
						title: '网络错误，删除失败',
						icon: 'none'
					});
				}
			}
		}
	});
};

const onMonthConfirm = (value) => {
	const date = new Date(value);
	summary.value.year = date.getFullYear().toString();
	summary.value.month = (date.getMonth() + 1).toString().padStart(2, '0');
	showMonthPicker.value = false;
	// 切换月份后立即刷新数据
	onLoad();
};

const getDaySummary = (group) => {
	const income = parseFloat(group.totalIncome || 0);
	const expense = parseFloat(group.totalExpense || 0);
	if (income > expense) {
		return `收入: ${(income - expense).toFixed(2)}`;
	} else {
		return `支出: ${(expense - income).toFixed(2)}`;
	}
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
	width: 0.5px;
	background-color: rgba(0, 0, 0, 0.15);
	margin: 0 20px;
}

.stat-group {
	flex: 1;
	display: flex;
	justify-content: flex-start;
	gap: 55px;
	min-width: 0;
}

.stat-item {
	display: flex;
	flex-direction: column;
	min-width: 0;
}

.stat-label {
	font-size: 11px;
	color: var(--secondary-text-color);
}

.stat-value {
	font-size: 18px;
	font-weight: 300;
	white-space: nowrap;
	overflow: hidden;
	text-overflow: ellipsis;
}

:deep(.van-grid-item__content) {
	background-color: transparent;
	padding: 4px 0;
}

.action-item {
	display: flex;
	flex-direction: column;
	align-items: center;
}

.action-icon-wrap {
	width: 44px;
	height: 44px;
	border-radius: 12px;
	display: flex;
	align-items: center;
	justify-content: center;
	margin-bottom: 4px;
}

.action-name {
	font-size: 10px;
	font-weight: 500;
	color: var(--secondary-text-color);
}

/* Action Colors */
.bg-action-amber,
.bg-action-blue,
.bg-action-emerald,
.bg-action-rose,
.bg-action-slate {
	background-color: var(--secondary-bg-color);
}

/* Transactions */
.transactions-section {
	margin-top: 15px;
}

.day-group {
	margin-bottom: 15px;
}

.day-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	padding: 0 15px;
}
.custom-cell {
	background-color: transparent;
	border-radius: 0;
	margin-bottom: 0;
	padding: 16px 20px !important;
	position: relative;
}

.custom-cell::after {
	content: "";
	position: absolute;
	bottom: 0;
	left: 72px;
	right: 0px;
	height: 1px;
	background-color: #f1f5f9;
}

.custom-cell.last-item::after {
	left: 0;
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
.bg-amber-light,
.bg-blue-light,
.bg-purple-light,
.bg-emerald-light {
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
