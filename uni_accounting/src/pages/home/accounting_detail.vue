<template>
	<view class="page-container" :class="currentThemeClass">
		<view class="tab-content">
			<view class="header-section">
				<view class="status-bar"></view>
			</view>

			<!-- 统计卡片 -->
			<view class="summary-card-box">
				<view class="summary-card">
					<view class="card-top">
						<view class="date-range" @click="showMonthPicker = true">
							<van-icon name="calendar-o" size="14" color="#94a3b8" class="calendar-icon" />
							<text class="date-text">{{ summary.month }}月01日-{{ summary.month }}月{{ getLastDayOfMonth(summary.year, summary.month) }}日</text>
							<van-icon :name="showMonthPicker ? 'arrow-down' : 'arrow'" size="12" color="#94a3b8" class="arrow-icon" />
						</view>
						<view class="ai-section">
							<view class="ai-bubble">
								<text>开始今天的记账吧~</text>
							</view>
							<view class="ai-avatar">
								<image src="/static/ai_avatar.png" mode="aspectFill" class="avatar-img" />
							</view>
						</view>
					</view>

					<view class="card-main">
						<view class="card-flex-container">
							<view class="stats-left" @click="currentStatType = currentStatType === 'expense' ? 'income' : 'expense'">
								<view class="main-stat">
									<view class="stat-type">
										<text class="type-text" :class="{ 'income-text': currentStatType === 'income' }">
											{{ currentStatType === 'expense' ? '支出' : '收入' }}
										</text>
										<view class="type-icon" :class="{ 'income-bg': currentStatType === 'income' }">
											<van-icon v-if="currentStatType === 'income'" name="exchange" size="10" color="#fff" />
											<van-icon v-else name="exchange" size="10" color="#fff" />
										</view>
									</view>
									<view class="main-amount">
										<text class="currency">¥</text>
										<text class="amount-val font-number">
											{{ currentStatType === 'expense' ? formatAmount(summary.expense) : formatAmount(summary.income) }}
										</text>
									</view>
								</view>

								<view class="sub-stats">
									<view class="sub-item">
										<text class="sub-label">{{ currentStatType === 'expense' ? '收入' : '支出' }}</text>
										<text class="sub-value font-number">
											¥{{ currentStatType === 'expense' ? formatAmount(summary.income) : formatAmount(summary.expense) }}
										</text>
									</view>
									<view class="sub-item">
										<text class="sub-label">结余</text>
										<text class="sub-value font-number">¥{{ formatAmount(currentIncomeValue - currentExpenseValue) }}</text>
									</view>
								</view>
							</view>

							<view class="chart-right" v-if="currentBudgetValue > 0">
								<van-circle
									v-model:current-rate="currentRate"
									:rate="expenseRate"
									:color="chartColor"
									:stroke-width="8"
									size="90"
									layer-color="#f1f5f9"
									speed="100"
								>
									<view class="chart-inner">
										<text class="chart-percent">{{ chartText }}</text>
										<text class="chart-label">预算</text>
									</view>
								</van-circle>
							</view>
							<view class="chart-right empty-chart" v-else>
								<view class="chart-inner">
									<text class="chart-percent">未设置</text>
									<text class="chart-label">预算</text>
								</view>
							</view>
						</view>

						<view class="card-footer">
							<view class="footer-divider"></view>
							<van-grid :column-num="5" :border="false" :gutter="0" class="footer-grid">
								<van-grid-item v-for="action in quickActions" :key="action.id" @click="onActionClick(action)">
									<template #icon>
										<view class="footer-action-icon">
											<van-icon :name="action.icon" :color="action.iconColor" size="20" />
										</view>
									</template>
									<template #text>
										<text class="footer-action-name">{{ action.name }}</text>
									</template>
								</van-grid-item>
							</van-grid>
						</view>
					</view>
				</view>
			</view>

			<view class="transactions-section">
				<van-list v-model:loading="loading" :finished="finished" @load="onLoad">
					<view v-if="dailyTransactions.length > 0">
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
					</view>
					<!-- 空状态提示 -->
					<view v-else-if="!loading" class="empty-state">
						<van-empty image="search" description="暂无账单数据" />
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
import { ref, computed, onMounted, watch } from 'vue';
import { onShow } from '@dcloudio/uni-app';
import CustomTabbar from '@/components/Tabbar/Tabbar.vue';
import { getBills, deleteBill, getBillSummary, getBudgets } from '@/api/api.js';
import { colorPairs } from '@/utils/color.js';

const showMonthPicker = ref(false);
const currentDate = ref(new Date());
const minDate = new Date(2020, 0, 1);
const maxDate = new Date(2030, 11, 31);
const activeNav = ref(0);
const currentStatType = ref('expense'); // 'expense' 或 'income'

const loading = ref(false);
const finished = ref(false);

const summary = ref({
	year: new Date().getFullYear().toString(),
	month: (new Date().getMonth() + 1).toString().padStart(2, '0'),
	expense: '0.00',
	income: '0.00'
});

const monthBudget = ref(0);
const currentRate = ref(0);

// 辅助函数：将带逗号的字符串转换为数字
const toNum = (val) => {
	if (val === undefined || val === null) return 0;
	const s = val.toString();
	return parseFloat(s.replace(/,/g, '')) || 0;
};

// --- 参考 budget.vue 简化逻辑 ---
const currentBudgetValue = computed(() => toNum(monthBudget.value));
const currentExpenseValue = computed(() => toNum(summary.value.expense));
const currentIncomeValue = computed(() => toNum(summary.value.income));

const isOverBudget = computed(() => currentExpenseValue.value > currentBudgetValue.value);

const expenseRate = computed(() => {
	if (currentBudgetValue.value === 0) return 0;
	const rate = (currentExpenseValue.value / currentBudgetValue.value) * 100;
	return Math.min(rate, 100);
});

const chartText = computed(() => {
	return isOverBudget.value ? '已超支' : `${expenseRate.value.toFixed(0)}%`;
});

const chartColor = computed(() => {
	if (isOverBudget.value) return { '0%': '#fca5a5', '100%': '#ef4444' };
	if (expenseRate.value >= 80) return '#f59e0b';
	return { '0%': '#6ee7b7', '100%': '#10b981' };
});

const fetchBudgetData = async () => {
	try {
		const params = {
			budget_type: 'month',
			period: `${summary.value.year}-${summary.value.month.padStart(2, '0')}`
		};
		const res = await getBudgets(params);
		if (res.code === 0) {
			monthBudget.value = res.data.totalAmount || 0;
		}
	} catch (e) {
		console.error('获取预算数据失败:', e);
	}
};

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
		console.log('DEBUG: fetchSummary res:', res);
		if (res.code === 0) {
			const data = res.data;
			// 更加鲁棒的月份匹配：统一转换为数字进行比较
			const currentMonthInt = parseInt(summary.value.month);
			const currentMonthData = data.monthBills.find(m => parseInt(m.month) === currentMonthInt);
			
			console.log('DEBUG: currentMonthInt:', currentMonthInt, 'found data:', currentMonthData);
			
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
		// 1. 并发获取汇总统计和预算数据，并等待完成
		await Promise.all([
			fetchSummary(),
			fetchBudgetData()
		]);

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
	const income = toNum(group.totalIncome || 0);
	const expense = toNum(group.totalExpense || 0);
	if (income > expense) {
		return `收入: ${(income - expense).toFixed(2)}`;
	} else {
		return `支出: ${(expense - income).toFixed(2)}`;
	}
};

const getLastDayOfMonth = (year, month) => {
	return new Date(year, month, 0).getDate();
};

const formatAmount = (val) => {
	if (val === undefined || val === null) return '0.00';
	const num = toNum(val);
	return num.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
};
</script>

<style scoped>
.page-container {
	min-height: 100vh;
	padding-bottom: 70px;
	background-color: #FFFEF2;
}

/* Header Section Styles */
.header-section {
	background-color: #ffd541;
	border-radius: 0 0 20px 20px;
	padding: 10px 16px 120px;
	position: relative;
}

.status-bar {
	height: var(--status-bar-height);
}

/* Summary Card Box - 独立盒子，用于承载统计卡片并处理层级 */
.summary-card-box {
	position: relative;
	margin: -110px 16px 15px;
	z-index: 20;
}

.summary-card {
	background-color: #fffef2;
	border-radius: 16px;
	padding: 10px 12px 12px;
	box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
	z-index: 20;
	border: 2.5px solid #DCCEA9;
	border-bottom-width: 6px; /* 底部边框加粗，产生厚度感 */
}

.card-top {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 5px;
	gap: 4px;
}

.date-range {
	display: flex;
	align-items: center;
	gap: 4px;
	font-size: 11px;
	color: #94a3b8;
	flex-shrink: 0;
	white-space: nowrap;
}

.ai-section {
	display: flex;
	align-items: center;
	justify-content: flex-end;
	overflow: visible;
	flex-shrink: 0;
}

.ai-bubble {
	position: relative;
	background-color: #ffec99;
	padding: 4px 10px;
	border-radius: 10px;
	font-size: 11px;
	color: #0f172a;
	margin-left: 20%;
	white-space: nowrap;
	flex-shrink: 0;
}

.ai-bubble text {
	white-space: nowrap;
}

.ai-bubble::after {
	content: "";
	position: absolute;
	right: -4px;
	top: 50%;
	transform: translateY(-50%);
	border-left: 5px solid #ffec99;
	border-top: 4px solid transparent;
	border-bottom: 4px solid transparent;
}

.ai-avatar {
	width: 36px;
	height: 36px;
	border-radius: 50%;
	border: 2px solid #fff;
	overflow: hidden;
	background-color: #fff;
}

.avatar-img {
	width: 100%;
	height: 100%;
}

.main-stat {
	margin-bottom: 10px;
}

.stat-type {
	display: flex;
	align-items: center;
	gap: 8px;
	margin-bottom: 10px;
}

.type-text {
	font-size: 14px;
	color: #ef4444;
	font-weight: 500;
	transition: color 0.3s ease;
}

.type-text.income-text {
	color: #10b981;
}

.type-icon {
	width: 14px;
	height: 14px;
	background-color: #ef4444;
	border-radius: 50%;
	display: flex;
	align-items: center;
	justify-content: center;
	transition: background-color 0.3s ease;
}

.type-icon.income-bg {
	background-color: #10b981;
}

.main-amount {
	display: flex;
	align-items: baseline;
	gap: 6px;
}

.currency {
	font-size: 20px;
	font-weight: 800;
	color: #0f172a;
}

.amount-val {
	font-size: 36px;
	font-weight: 800;
	color: #0f172a;
	line-height: 1;
}

.card-flex-container {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 20px;
}

.stats-left {
	flex: 1;
	min-width: 0;
}

.chart-right {
	width: 90px;
	height: 90px;
	display: flex;
	align-items: center;
	justify-content: center;
	margin-left: 20px;
	flex-shrink: 0;
	position: relative;
}

.empty-chart {
	border: 8px solid #f1f5f9;
	border-radius: 50%;
	box-sizing: border-box;
}

.chart-inner {
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	position: absolute;
	top: 50%;
	left: 50%;
	transform: translate(-50%, -50%);
	width: 100%;
}

.chart-percent {
	font-size: 15px;
	font-weight: 800;
	color: #0f172a;
	line-height: 1.2;
	text-align: center;
}

.chart-label {
	font-size: 11px;
	color: #94a3b8;
	margin-top: 2px;
}

.sub-stats {
	display: flex;
	gap: 30px;
	margin-top: 15px;
	padding: 0 4px;
}

.sub-item {
	display: flex;
	flex-direction: column;
	gap: 2px;
}

.sub-label {
	font-size: 12px;
	color: #94a3b8;
}

.sub-value {
	font-size: 18px;
	font-weight: 700;
	color: #0f172a;
}

.card-footer {
	margin-top: 4px;
}

.footer-divider {
	height: 1px;
	background: repeating-linear-gradient(to right, #e2e8f0, #e2e8f0 4px, transparent 4px, transparent 8px);
	margin-bottom: 8px;
}

.footer-action-icon {
	margin-bottom: 2px;
}

.footer-action-name {
	font-size: 10px;
	font-weight: 500;
	color: #64748b;
}

:deep(.footer-grid .van-grid-item__content) {
	background-color: transparent !important;
	padding: 8px 0 !important;
}

/* Transactions Section - 独立盒子，自然跟随在卡片下方 */
.transactions-section {
	margin: 0 16px 20px;
	background-color: #fffef2;
	border-radius: 16px;
	padding: 10px 0;
	box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
	border: 2.5px solid #DCCEA9;
}

.day-group {
	margin-bottom: 10px;
}

.empty-state {
	padding: 40px 0;
}

.day-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	padding: 8px 16px;
	font-weight: 500;
}

.custom-cell {
	background-color: transparent !important;
	border-radius: 0;
	margin-bottom: 0;
	padding: 12px 16px !important;
	position: relative;
}

.flat-cell {
	background-color: transparent !important;
}

:deep(.van-cell) {
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
