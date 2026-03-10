<template>
	<view class="page-container" :class="currentThemeClass">
		<!-- 顶部固定导航 -->
		<view class="fixed-nav-container">
			<view class="nav-header">
				<!-- 左侧年份选择 -->
				<view class="year-selector" @click="showYearPicker = true">
					<text class="year-text">{{ currentYear }}年</text>
					<van-icon name="arrow-down" size="14" color="#0f172a" />
				</view>
				
				<!-- 右侧胶囊按钮 -->
				<view class="nav-right-actions">
					<CapsuleButton />
				</view>
			</view>
		</view>

		<!-- 月份预算列表 -->
		<scroll-view scroll-y class="main-content">
			<view class="card-list" v-if="monthlyBudgets.length > 0">
				<view 
					v-for="(monthData, index) in monthlyBudgets" 
					:key="monthData.month" 
					class="month-card"
					@click="openMonthDetail(monthData)"
				>
					<view class="card-header">
						<text class="month-title">{{ monthData.month }}月</text>
						<van-icon name="arrow" color="#94a3b8" size="16" />
					</view>
					
					<view class="card-body">
						<!-- 左侧图表 -->
						<view class="chart-box">
							<van-circle
								v-model:current-rate="listCurrentRates[monthData.month]"
								:rate="monthData.expenseRate"
								:color="getChartColor(monthData.isOverBudget)"
								:text="getListChartText(monthData)"
								:stroke-width="8"
								size="80"
								layer-color="#f1f5f9"
								speed="100"
							/>
						</view>
						
						<!-- 右侧数据 -->
						<view class="stats-box">
							<view class="stat-row">
								<text class="label">剩余预算</text>
								<text class="value large-num text-style-number" :class="{ 'text-danger': monthData.isOverBudget }">
									{{ (monthData.budget - monthData.expense).toFixed(2) }}
								</text>
							</view>
							<view class="stat-row small-row">
								<text class="label">本月预算</text>
								<text class="value text-style-number">{{ monthData.budget }}</text>
							</view>
							<view class="stat-row small-row">
								<text class="label">本月支出</text>
								<text class="value text-style-number">{{ monthData.expense }}</text>
							</view>
						</view>
					</view>
				</view>
			</view>

			<!-- 全年空状态 -->
			<view class="empty-state-full" v-else>
				<view class="empty-icon-bg">
					<van-icon name="balance-list-o" size="64" color="#cbd5e1" />
				</view>
				<text class="empty-text">该年份暂无预算记录</text>
				<text class="empty-sub-text">快去设置预算，开启科学理财吧！</text>
			</view>
		</scroll-view>

		<!-- 年份选择弹窗 -->
		<van-popup :show="showYearPicker" position="bottom" round @close="showYearPicker = false">
			<van-picker
				title="选择年份"
				show-toolbar
				:columns="yearColumns"
				@confirm="onConfirmYear"
				@cancel="showYearPicker = false"
			/>
		</van-popup>

		<!-- 月份详情弹窗 -->
		<van-popup 
			v-model:show="showDetailPopup" 
			position="bottom" 
			round 
			class="detail-popup"
			:style="{ height: '80%' }"
		>
			<view class="popup-header">
				<text class="popup-title">{{ selectedMonth?.month }}月预算详情</text>
				<van-icon name="cross" class="close-icon" @click="showDetailPopup = false" />
			</view>
			
			<scroll-view scroll-y class="popup-content">
				<!-- 顶部图表区域 (复用样式) -->
				<view class="detail-chart-section" v-if="selectedMonth">
					<view class="chart-box-large">
						<van-circle
							v-model:current-rate="currentDetailRate"
							:rate="selectedMonth.expenseRate"
							:color="getChartColor(selectedMonth.isOverBudget)"
							:text="detailChartText"
							:stroke-width="8"
							size="100"
							layer-color="#f1f5f9"
							speed="100"
						/>
					</view>
					<view class="detail-stats">
						<view class="stat-item">
							<text class="stat-label">总预算</text>
							<text class="stat-value">{{ selectedMonth.budget }}</text>
						</view>
						<view class="stat-item">
							<text class="stat-label">已支出</text>
							<text class="stat-value">{{ selectedMonth.expense }}</text>
						</view>
						<view class="stat-item">
							<text class="stat-label">剩余</text>
							<text class="stat-value" :class="{ 'text-danger': selectedMonth.isOverBudget }">
								{{ (selectedMonth.budget - selectedMonth.expense).toFixed(2) }}
							</text>
						</view>
					</view>
				</view>

				<!-- 分类预算列表 -->
				<view class="category-list-section" v-if="selectedMonth && selectedMonth.categories.length > 0">
					<view class="list-container">
						<van-cell v-for="item in selectedMonth.categories" :key="item.id" center class="custom-cell flat-cell">
							<template #icon>
								<view class="list-icon-wrap" :style="{ backgroundColor: getIconColors(item.icon_id).bg }">
									<van-icon :name="item.icon" :color="getIconColors(item.icon_id).icon" size="24" />
								</view>
							</template>
							<template #title>
								<view class="cell-content">
									<view class="cell-main">
										<view class="cell-header">
											<text class="text-style-title">{{ item.name }}</text>
											<view class="amount-info">
												<text class="spent-text text-style-number">¥{{ item.spent.toFixed(2) }}</text>
												<text class="total-text text-style-desc">/ ¥{{ item.amount.toFixed(2) }}</text>
											</view>
										</view>
										<view class="progress-container">
											<view class="progress-bar-bg">
												<view class="progress-bar-fill" :style="{ width: (showDetailAnimation ? item.percent : 0) + '%', backgroundColor: getIconColors(item.icon_id).icon }"></view>
											</view>
											<text class="percent-text text-style-desc">{{ item.percent }}%</text>
										</view>
									</view>
								</view>
							</template>
						</van-cell>
					</view>
				</view>
				
				<!-- 空状态 -->
				<view class="empty-state" v-else>
					<view class="empty-icon-bg">
						<van-icon name="balance-list-o" size="48" color="#cbd5e1" />
					</view>
					<text class="empty-text">该月未设置分类预算</text>
				</view>
			</scroll-view>
		</van-popup>
	</view>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import CapsuleButton from '@/components/CapsuleButton/CapsuleButton.vue';
import { getBudgets } from '@/api/api.js';
import { getIconColors } from '@/utils/color.js';

// 初始化年份选择数据
const getYearColumns = () => {
	const years = [];
	const nowYear = new Date().getFullYear();
	for (let i = nowYear - 5; i <= nowYear + 1; i++) {
		years.push(i);
	}
	return years.map(y => ({ text: `${y}年`, value: y }));
};

// --- 状态定义 ---
const currentYear = ref(new Date().getFullYear());
const showYearPicker = ref(false);
const showDetailPopup = ref(false);
const showDetailAnimation = ref(false);
const selectedMonth = ref(null);
const currentDetailRate = ref(0);
const detailChartText = computed(() => {
	if (!selectedMonth.value) return '0%';
	if (selectedMonth.value.isOverBudget) return '已超支';
	return currentDetailRate.value.toFixed(0) + '%';
});

// 年份选择数据
const yearColumns = getYearColumns();

// 月份数据容器
const monthlyBudgets = ref([]);

// 列表项圆环当前进度
const listCurrentRates = ref({});

// 异步加载全年的月份数据汇总
const loadYearData = async () => {
	uni.showLoading({ title: '加载中...' });
	
	const promises = Array.from({ length: 12 }, (_, i) => {
		const month = i + 1;
		const period = `${currentYear.value}-${month.toString().padStart(2, '0')}`;
		return getBudgets({ budget_type: 'month', period })
			.then(res => {
				// 只要有预算总额 > 0 或者是该月有分类预算
				if (res.code === 0 && (res.data.totalAmount > 0 || (res.data.categories && res.data.categories.length > 0))) {
					const { totalAmount, totalSpent, categories } = res.data;
					const rate = totalAmount > 0 ? (totalSpent / totalAmount) * 100 : 0;
					
					// 初始化列表项进度
					listCurrentRates.value[month] = 0;
					
					return {
						month,
						budget: totalAmount,
						expense: totalSpent,
						expenseRate: Math.min(rate, 100),
						isOverBudget: totalSpent > totalAmount,
						categories: categories || []
					};
				}
				return null;
			})
			.catch(() => null);
	});
	
	const results = await Promise.all(promises);
	uni.hideLoading();
	
	// 过滤掉没有预算数据的月份，并按月份排序
	monthlyBudgets.value = results.filter(item => item !== null).sort((a, b) => a.month - b.month);
};

onMounted(() => {
	loadYearData();
});

// --- 方法 ---
const onConfirmYear = (event) => {
	const { value } = event.detail || event;
	// 如果是单列，value 可能直接是值，也可能是对象
	const selectedValue = typeof value === 'object' ? value.value : value;
	currentYear.value = selectedValue;
	showYearPicker.value = false;
	loadYearData();
};

const openMonthDetail = (monthData) => {
	selectedMonth.value = monthData;
	currentDetailRate.value = 0; // 重置动画
	showDetailAnimation.value = false;
	showDetailPopup.value = true;
	
	// 延迟开启进度条动画
	setTimeout(() => {
		showDetailAnimation.value = true;
	}, 100);
};

const getChartColor = (isOver) => {
	if (isOver) {
		return { '0%': '#fca5a5', '100%': '#ef4444' }; // 红色渐变
	}
	return { '0%': '#6ee7b7', '100%': '#10b981' }; // 绿色渐变
};

const getListChartText = (data) => {
	if (data.isOverBudget) return '已超支';
	const current = listCurrentRates.value[data.month] || 0;
	return current.toFixed(0) + '%';
};
</script>

<style scoped>
.page-container {
	min-height: 100vh;
	background-color: #f8fafc;
	display: flex;
	flex-direction: column;
}

/* 顶部固定导航 */
.fixed-nav-container {
	background-color: #ffffff;
	padding: 10px 20px;
	box-sizing: border-box;
	flex-shrink: 0;
	z-index: 100;
	position: sticky;
	top: 0;
	box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.nav-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
}

.year-selector {
	display: flex;
	align-items: center;
	gap: 4px;
	padding: 6px 12px;
	background-color: #f1f5f9;
	border-radius: 20px;
}

.year-text {
	font-size: 16px;
	font-weight: 600;
	color: #0f172a;
}

.nav-right-actions {
	display: flex;
	align-items: center;
}

/* 主内容区 */
.main-content {
	flex: 1;
	padding: 10px;
	box-sizing: border-box;
}

.card-list {
	display: flex;
	flex-direction: column;
	gap: 10px;
}

.month-card {
	background-color: #ffffff;
	border-radius: 16px;
	padding: 16px;
	box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
}

.card-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 10px;
	padding-bottom: 10px;
	border-bottom: 1px solid #f1f5f9;
}

.month-title {
	font-size: 16px;
	font-weight: 600;
	color: #0f172a;
}

.card-body {
	display: flex;
	align-items: center;
	gap: 20px;
}

.chart-box {
	position: relative;
}

/* 深度选择器修改 van-circle 文字样式 */
:deep(.van-circle__text) {
	font-weight: bold;
	color: #0f172a;
	font-size: 14px;
}

.stats-box {
	flex: 1;
	display: flex;
	flex-direction: column;
	gap: 8px;
}

.stat-row {
	display: flex;
	justify-content: space-between;
	align-items: baseline;
}

.label {
	font-size: 12px;
	color: #64748b;
}

.value {
	font-size: 14px;
	font-weight: 600;
	color: #0f172a;
}

.large-num {
	font-size: 20px;
}

.small-row {
	margin-top: 4px;
}

.text-danger {
	color: #ef4444 !important;
}

/* 详情弹窗样式 */
.detail-popup {
	background-color: #f8fafc;
	display: flex;
	flex-direction: column;
}

.popup-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	padding: 16px 20px;
	background-color: #ffffff;
	border-bottom: 1px solid #f1f5f9;
}

.popup-title {
	font-size: 18px;
	font-weight: 600;
	color: #0f172a;
}

.close-icon {
	font-size: 20px;
	padding: 4px;
	color: #64748b;
}

.popup-content {
	flex: 1;
	overflow-y: auto;
}

.detail-chart-section {
	background-color: #ffffff;
	padding: 20px;
	margin-bottom: 12px;
	display: flex;
	flex-direction: column;
	align-items: center;
}

.chart-box-large {
	margin-bottom: 20px;
}

.detail-stats {
	display: flex;
	justify-content: space-around;
	width: 100%;
}

.stat-item {
	display: flex;
	flex-direction: column;
	align-items: center;
	gap: 4px;
}

.stat-label {
	font-size: 12px;
	color: #64748b;
}

.stat-value {
	font-size: 16px;
	font-weight: 600;
	color: #0f172a;
}

/* 复用列表样式 */
.category-list-section {
	padding: 16px;
	background-color: #ffffff;
	min-height: 200px;
}

.list-container {
	background: #ffffff;
}

.custom-cell {
	padding: 12px 0 !important;
}

.flat-cell {
	background: transparent !important;
}

.list-icon-wrap {
	width: 42px;
	height: 42px;
	border-radius: 12px;
	display: flex;
	justify-content: center;
	align-items: center;
	margin-right: 12px;
}

.bg-orange-light, 
.bg-blue-light, 
.bg-purple-light, 
.bg-pink-light, 
.bg-green-light, 
.bg-yellow-light, 
.bg-slate-light { 
	background-color: #f1f5f9; 
}

.cell-content {
	display: flex;
	justify-content: space-between;
	align-items: center;
	flex: 1;
	overflow: hidden;
}

.cell-main {
	display: flex;
	flex-direction: column;
	gap: 8px;
	flex: 1;
	min-width: 0;
}

.cell-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
}

.progress-container {
	display: flex;
	align-items: center;
	gap: 12px;
}

.progress-bar-bg {
	flex: 1;
	height: 6px;
	background: #f1f5f9;
	border-radius: 3px;
	overflow: hidden;
}

.progress-bar-fill {
	height: 100%;
	border-radius: 3px;
	transition: width 0.8s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.percent-text {
	font-size: 12px;
	font-weight: 500;
	color: #94a3b8;
	width: 36px;
	text-align: right;
}

.amount-info {
	display: flex;
	align-items: baseline;
}

.spent-text {
	font-size: 15px;
	font-weight: 700;
	color: #0f172a;
}

.total-text {
	font-size: 11px;
	color: #94a3b8;
	margin-left: 2px;
}

.empty-state {
	padding: 40px 0;
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
}

.empty-icon-bg {
	width: 80px;
	height: 80px;
	background-color: #fff;
	border-radius: 50%;
	display: flex;
	align-items: center;
	justify-content: center;
	margin-bottom: 16px;
	box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);
}

.empty-text {
	font-size: 14px;
	color: #94a3b8;
}

.empty-state-full {
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	padding-top: 100px;
}

.empty-sub-text {
	font-size: 12px;
	color: #cbd5e1;
	margin-top: 8px;
}
</style>
