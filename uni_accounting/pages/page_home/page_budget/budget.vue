<template>
	<view class="page-container" :class="currentThemeClass">
		<!-- 顶部固定导航区域 -->
		<view class="fixed-nav-container">
			<view class="nav-header">
				<view class="nav-left-title">
					<text class="nav-title-text">{{ budgetType }}概览</text>
				</view>
				<!-- Segmented Control -->
				<view class="segmentControl">
					<view 
						class="segmentItem" :class="{ active: budgetType === '月预算' }" @click="budgetType = '月预算'">
						<text class="segmentText">月预算</text>
					</view>
					<view 
						class="segmentItem" :class="{ active: budgetType === '年预算' }" @click="budgetType = '年预算'">
						<text class="segmentText">年预算</text>
					</view>
				</view>
				<!-- 微信样式胶囊按钮 & 编辑按钮 -->
				<view class="nav-right-actions">
					<CapsuleButton class="nav-capsule" />
					<view class="nav-edit-btn" @click="onEditBudget">
						<van-icon name="edit" size="18" color="#0f172a" />
					</view>
				</view>
			</view>
		</view>
		<scroll-view scroll-y class="main-content">
			<view class="card-container">
				<view class="budget-card">
					<view class="card-content">
						<view class="chart-box">
							<van-circle
								v-model:current-rate="currentRate"
								:rate="expenseRate"
								:color="chartColor"
								:text="chartText"
								:stroke-width="8"
								size="100"
								layer-color="#f1f5f9"
								speed="100"
							/>
						</view>
						
						<!-- 右侧数据 -->
						<view class="stats-box">
							<view class="stat-row">
									<text class="label">剩余预算</text>
								<text class="value large-num text-style-number" :class="{ 'text-danger': isOverBudget }">{{ remainingBudget }}</text>
							</view>
							<view class="stat-row small-row">
									<text class="label">{{ budgetType === '月预算' ? '本月' : '本年' }}预算</text>
								<text class="value text-style-number">{{ currentBudgetValue }}</text>
							</view>
							<view class="stat-row small-row">
									<text class="label">{{ budgetType === '月预算' ? '本月' : '本年' }}支出</text>
								<text class="value text-style-number">{{ currentExpenseValue }}</text>
							</view>
						</view>
					</view>
				</view>
			</view>

			<!-- 分类预算列表 -->
			<view class="category-list-section" v-if="filteredCategoryBudgets.length > 0">
				
				<view class="list-container">
					<van-cell v-for="item in filteredCategoryBudgets" :key="item.id" center class="custom-cell flat-cell">
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
											<view class="progress-bar-fill" :style="{ width: (showAnimation ? item.percent : 0) + '%', backgroundColor: getIconColors(item.icon_id).icon }"></view>
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
				<text class="empty-text">未设置分类预算</text>
			</view>
		</scroll-view>

		<!-- 底部固定按钮 -->
		<view class="bottom-bar">
			<view class="add-button" @click="onAddBudget">
				<van-icon name="plus" color="#0f172a" size="16" />
				<text class="add-text">添加{{ budgetType }}分类</text>
			</view>
		</view>

		<!-- 预算类型选择弹窗 -->
		<van-action-sheet 
			v-model:show="showTypeSheet" 
			:actions="viewActions" 
			@select="onTypeSelect" 
			z-index="2000"
			position="top"
			class="top-action-sheet"
		/>

		<!-- 分类选择弹窗 -->
		<van-popup
			v-model:show="showCategoryPopup"
			position="bottom"
			round
			class="category-popup"
		>
			<view class="popup-header">
				<text class="popup-title">选择分类</text>
				<van-icon name="cross" class="close-icon" @click="showCategoryPopup = false" />
			</view>
			<view class="category-grid">
				<view v-for="cat in categories" :key="cat.id" class="category-item" @click="onSelectCategory(cat)">
					<view class="icon-circle" :style="{ backgroundColor: cat.colorBg }">
						<van-icon :name="cat.icon" :color="cat.colorIcon" size="24" />
					</view>
					<text class="category-name">{{ cat.name }}</text>
				</view>
			</view>
		</van-popup>

		<!-- 金额输入弹窗 -->
		<van-popup
			v-model:show="showEditPopup"
			position="bottom"
			round
			class="edit-popup"
			:close-on-click-overlay="false"
		>
			<view class="popup-header">
				<text class="popup-title">
					{{ isAddingCategory ? (selectedCategory ? selectedCategory.name + '预算' : '分类预算') : (editBudgetType === '月预算' ? '每月总预算' : '每年总预算') }}
				</text>
				<van-icon name="cross" class="close-icon" @click="showEditPopup = false" />
			</view>
			
			<van-field
				v-model="editBudgetValue"
				type="digit"
				input-align="center"
				class="budget-input-field"
				:border="false"
				autofocus
			>
			</van-field>
			
			<view class="limit-info" v-if="budgetLimitInfo">
				<van-icon name="info-o" size="14" color="#94a3b8" style="margin-right: 4px;" />
				<text class="limit-text">{{ budgetLimitInfo }}</text>
			</view>
			
			<view class="confirm-btn-box">
				<van-button block round 
					@click="onConfirmAmount" 
					class="confirm-btn-vant"
					:class="{ 'active-btn': editBudgetValue }"
					:disabled="!editBudgetValue"
				>确定</van-button>
			</view>
		</van-popup>
	</view>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue';
import CapsuleButton from '@/components/CapsuleButton/CapsuleButton.vue';
import { getAllIcons, getBudgets, saveBudget } from '@/api/api.js';
import { assignDefaultColors, colorPairs } from '@/utils/color.js';

// --- 状态定义 ---
const showTypeSheet = ref(false);
const showEditPopup = ref(false);
const showCategoryPopup = ref(false);
const selectedCategory = ref(null);
const isAddingCategory = ref(false);
const showAnimation = ref(false);
const editBudgetType = ref('月预算');
const editBudgetValue = ref('');
const budgetLimitInfo = ref(''); // 用于展示限额提示

const budgetType = ref('月预算');
const viewActions = [
	{ name: '月预算' },
	{ name: '年预算' },
];

// 记账分类数据 - 初始为空，从接口获取
const categories = ref([]);

// 分类预算列表
const categoryBudgets = ref([]);

// 模拟数据 (改为由接口返回真实数据)
const monthBudget = ref(0);
const monthExpense = ref(0);
const yearBudget = ref(0);
const yearExpense = ref(0);

// --- 计算属性 ---
const filteredCategoryBudgets = computed(() => {
	return categoryBudgets.value.filter(item => item.type === budgetType.value);
});

const getIconColors = (iconId) => {
	const colorIndex = Number(iconId) % colorPairs.length;
	return colorPairs[colorIndex];
};

const currentBudgetValue = computed(() => {
	return budgetType.value === '月预算' ? monthBudget.value : yearBudget.value;
});

const currentExpenseValue = computed(() => {
	return budgetType.value === '月预算' ? monthExpense.value : yearExpense.value;
});

const remainingBudget = computed(() => {
	return (currentBudgetValue.value - currentExpenseValue.value).toFixed(2);
});

const expenseRate = computed(() => {
	if (currentBudgetValue.value === 0) return 0;
	const rate = (currentExpenseValue.value / currentBudgetValue.value) * 100;
	return Math.min(rate, 100); 
});

const currentRate = ref(0); 

const isOverBudget = computed(() => {
	return currentExpenseValue.value > currentBudgetValue.value;
});

// 获取当前周期 (2024-03 或 2024)
const getCurrentPeriod = () => {
	const now = new Date();
	if (budgetType.value === '月预算') {
		const year = now.getFullYear();
		const month = String(now.getMonth() + 1).padStart(2, '0');
		return `${year}-${month}`;
	} else {
		return String(now.getFullYear());
	}
};

const fetchBudgetData = async () => {
	try {
		const isMonth = budgetType.value === '月预算';
		const params = {
			budget_type: isMonth ? 'month' : 'year',
			period: getCurrentPeriod()
		};
		const res = await getBudgets(params);
		if (res.code === 0) {
			if (isMonth) {
				monthBudget.value = res.data.totalAmount;
				monthExpense.value = res.data.totalSpent;
				
				// 额外获取一次年度总预算，用于前端限额判断提示
				const yearParams = {
					budget_type: 'year',
					period: getCurrentPeriod().split('-')[0]
				};
				const yearRes = await getBudgets(yearParams);
				if (yearRes.code === 0) {
					yearBudget.value = yearRes.data.totalAmount;
				}
			} else {
				yearBudget.value = res.data.totalAmount;
				yearExpense.value = res.data.totalSpent;
			}
			// 映射分类预算数据，保持前端渲染结构
			categoryBudgets.value = res.data.categories.map(item => ({
				...item,
				type: budgetType.value,
				icon_id: item.icon_id
			}));
		}
	} catch (e) {
		console.error('Failed to fetch budgets:', e);
	}
};

const chartColor = computed(() => {
	// 使用渐变色对象
	if (isOverBudget.value) {
		return { '0%': '#fca5a5', '100%': '#ef4444' }; // 红色渐变
	}
	return { '0%': '#6ee7b7', '100%': '#10b981' }; // 绿色渐变
});

const chartText = computed(() => {
	return isOverBudget.value ? '已超支' : `${expenseRate.value.toFixed(0)}%`;
});

// --- 生命周期 & 动画 ---
onMounted(async () => {
	try {
		const res = await getAllIcons();
		if (res.code === 0) {
			// 只展示普通分类，且类型为支出或全部
			const normalIcons = res.data.filter(i => i.group === 'normal' && (i.type === 'expense' || i.type === 'all'));
			
			// 将“其他”图标移到最后
			const restIcons = normalIcons.filter(i => i.name !== '其他');
			const otherIcon = normalIcons.find(i => i.name === '其他');
			const sortedIcons = otherIcon ? [...restIcons, otherIcon] : restIcons;
			
			// 分配颜色
			categories.value = assignDefaultColors(sortedIcons);
		}
	} catch (e) {
		console.error('Failed to load icons:', e);
	}

	// 获取预算真实数据
	fetchBudgetData();
	
	setTimeout(() => {
		showAnimation.value = true;
	}, 100);
});

// 监听切换，重新触发动画
watch(budgetType, () => {
	showAnimation.value = false;
	fetchBudgetData();
	setTimeout(() => {
		showAnimation.value = true;
	}, 50);
});

// --- 方法 ---
const onTypeSelect = (event) => {
	budgetType.value = event.name;
	showTypeSheet.value = false;
};

const onEditBudget = () => {
	isAddingCategory.value = false;
	editBudgetType.value = budgetType.value;
	
	// 关闭键盘，防止遮挡
	uni.hideKeyboard();
	
	// 回显当前已有的预算值
	const currentVal = editBudgetType.value === '月预算' ? monthBudget.value : yearBudget.value;
	editBudgetValue.value = currentVal > 0 ? currentVal.toString() : '';
	
	// 设置限额提示
	if (editBudgetType.value === '月预算') {
		if (yearBudget.value > 0) {
			budgetLimitInfo.value = `年总限额: ¥${yearBudget.value}`;
		} else {
			budgetLimitInfo.value = '提示: 请先设置年度总预算';
		}
	} else {
		budgetLimitInfo.value = '';
	}
	
	showEditPopup.value = true;
};

const onAddBudget = () => {
	isAddingCategory.value = true;
	showCategoryPopup.value = true;
};

const onSelectCategory = (cat) => {
	selectedCategory.value = cat;
	editBudgetValue.value = '';
	
	// 关闭键盘
	uni.hideKeyboard();
	
	// 计算当前已分配的分类预算总额
	const allocated = categoryBudgets.value.reduce((sum, item) => sum + item.amount, 0);
	const limit = budgetType.value === '月预算' ? monthBudget.value : yearBudget.value;
	
	if (limit > 0) {
		budgetLimitInfo.value = `${budgetType.value}上限: ¥${limit} / 已添加: ¥${allocated.toFixed(2)}`;
	} else {
		budgetLimitInfo.value = `提示: 请先设置${budgetType.value}总额`;
	}
	
	showCategoryPopup.value = false;
	showEditPopup.value = true;
};

const onConfirmAmount = async () => {
	const value = parseFloat(editBudgetValue.value) || 0;
	if (value <= 0) {
		uni.showToast({ title: '金额必须大于0', icon: 'none' });
		return;
	}

	uni.showLoading({ title: '保存中...' });
	try {
		const params = {
			amount: value,
			budget_type: (isAddingCategory.value ? budgetType.value : editBudgetType.value) === '月预算' ? 'month' : 'year',
			period: getCurrentPeriod(),
			is_total: !isAddingCategory.value,
			icon_id: isAddingCategory.value && selectedCategory.value ? selectedCategory.value.id : null
		};
		
		const res = await saveBudget(params);
		if (res.code === 0) {
			uni.showToast({ title: '保存成功', icon: 'success' });
			showEditPopup.value = false;
			// 刷新数据
			fetchBudgetData();
		} else {
			// 检测到超支等规则错误，先关闭输入弹窗，再显示 Modal 提示
			showEditPopup.value = false;
			
			uni.showModal({
				title: '预算警告',
				content: res.msg || '预算金额不符合规则',
				showCancel: false,
				confirmText: '我知道了',
				confirmColor: '#ffd541'
			});
		}
	} catch (e) {
		console.error('Failed to save budget:', e);
		uni.showToast({ title: '网络异常', icon: 'none' });
	} finally {
		uni.hideLoading();
	}
};
</script>

<style scoped>
.page-container {
	min-height: 100vh;
	background-color: #ffffff; 
	display: flex;
	flex-direction: column;
	position: relative;
}

/* 顶部固定导航 */
.fixed-nav-container {
	background-color: #ffffff;
	padding: 10px 20px;
	box-sizing: border-box;
	flex-shrink: 0;
	z-index: 2001; 
}

.nav-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	position: relative;
}

.segmentControl {
	display: flex;
	background-color: #ffffff;
	border: 1px solid #0f172a;
	border-radius: 6px;
	overflow: hidden;
	margin-left: auto;
	margin-right: auto;
}

.nav-left-title {
	width: 85px;
	display: flex;
	align-items: center;
}

.nav-title-text {
	font-size: 14px;
	font-weight: 500;
	/* color: #0f172a; */
}

.nav-right-actions {
	width: 80px; 
	display: flex;
	align-items: center;
	justify-content: flex-end;
	gap: 8px;
}

.nav-edit-btn {
	width: 32px;
	height: 32px;
	display: flex;
	align-items: center;
	justify-content: center;
	background-color: rgba(255, 255, 255, 0.6);
	border: 0.5px solid rgba(0, 0, 0, 0.1);
	border-radius: 50%;
}

.nav-edit-btn:active {
	background-color: rgba(0, 0, 0, 0.05);
}

.nav-capsule {
	position: static !important;
}

.segmentItem {
	padding: 4px 16px;
	cursor: pointer;
	transition: all 0.3s;
}

.segmentItem.active {
	background-color: #0f172a;
}

.segmentItem.active .segmentText {
	color: #fff;
}


/* 悬浮卡片容器 */
.card-container {
	padding: 6px;
	position: relative;
	z-index: 2;
}

.budget-card {  
	background-color: #ffffff;
	padding: 10px;
}

.card-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 24px;
}

.card-title {
	font-size: 14px;
	color: #64748b;
	font-weight: 500;
}

.edit-btn {
	display: flex;
	align-items: center;
	gap: 4px;
	padding: 4px 8px;
}

.edit-text {
	font-size: 12px;
	color: #64748b;
}

.card-content {
	display: flex;
	align-items: center;
	justify-content: space-between;
    gap: 20px;
}

.chart-box {
	position: relative;
	margin-right: 20px;
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
	gap: 14px;
}

.stat-row {
	display: flex;
	justify-content: space-between;
	align-items: baseline;
}
/* 主要内容区 */
.main-content {
	flex: 1;
	padding-bottom: 80px; /* 为底部按钮留空间 */
}

.empty-state {
	margin-top: 60px;
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	opacity: 0.8;
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
	font-size: 15px;
	color: #94a3b8;
	margin-bottom: 8px;
}


/* 底部固定栏 */
.bottom-bar {
	position: fixed;
	bottom: 0;
	left: 0;
	right: 0;
	background-color: #fff;
	padding: 14px 16px 20px; /* 适配底部安全区 */
	box-shadow: 0 -4px 16px rgba(0, 0, 0, 0.05);
	z-index: 10;
}

.add-button {
	background-color: #fff;
	height: 20px;
	display: flex;
	justify-content: center;
	align-items: center;
	gap: 8px;
}

.add-text {
	font-size: 16px;
	font-weight: 600;
	color: #0f172a;
}

/* 分类预算列表样式 */
.category-list-section {
	padding: 5px;
}

.section-title-wrap {
	margin-bottom: 16px;
}

.section-title {
	font-size: 18px;
	font-weight: 700;
	color: #0f172a;
}

.list-container {
	background: #ffffff;
	overflow: hidden;
}

.custom-cell {
	padding: 10px !important;
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

.cell-content {
	display: flex;
	justify-content: space-between;
	align-items: center;
	flex: 1;
	overflow: hidden; /* 防止溢出 */
}

.cell-main {
	display: flex;
	flex-direction: column;
	gap: 10px;
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

/* 分类选择弹窗样式 */
.category-popup {
	max-height: 70vh;
	padding-bottom: 30px;
}

.category-grid {
	display: grid;
	grid-template-columns: repeat(4, 1fr);
	gap: 20px;
	padding: 20px;
}

.category-item {
	display: flex;
	flex-direction: column;
	align-items: center;
	gap: 8px;
}

.icon-circle {
	width: 42px;
	height: 42px;
	border-radius: 16px;
	display: flex;
	justify-content: center;
	align-items: center;
	transition: transform 0.2s;
}

.category-item:active .icon-circle {
	transform: scale(0.9);
}

.category-name {
	font-size: 12px;
	color: #64748b;
}

/* 金额输入弹窗样式 */
.edit-popup {
	background-color: #ffffff;
}

.popup-header {
	display: flex;
	align-items: center;
	justify-content: center;
	padding: 20px 16px 10px;
	position: relative;
}

.popup-title {
	font-size: 16px;
	font-weight: 600;
	color: #1e293b;
}

.close-icon {
	position: absolute;
	right: 16px;
	font-size: 18px;
	padding: 4px;
}

.budget-input-field {
	margin: 0px 0px 10px;
}

.currency-label {
	font-size: 18px;
	font-weight: 600;
	color: #1e293b;
	margin-right: 4px;
}

:deep(.budget-input-field .van-field__control) {
	font-size: 28px;
	font-weight: 700;
	color: #1e293b;
	text-align: center;
}

.limit-info {
	display: flex;
	align-items: center;
	justify-content: center;
	padding: 8px 16px;
	margin: 0 24px 20px;
	background-color: #f8fafc;
	border-radius: 8px;
	border: 1px solid #f1f5f9;
}

.limit-text {
	font-size: 12px;
	color: #64748b;
	line-height: 1.4;
	text-align: center;
}

.confirm-btn-box {
	padding: 0 24px 20px;
}

.confirm-btn-vant {
	background-color: #f1f5f9 !important;
	border: none !important;
	color: #94a3b8 !important;
	font-weight: 600;
	font-size: 16px;
}

.confirm-btn-vant.active-btn {
	background-color: #ffd541 !important;
	color: #0f172a !important;
}

:deep(.van-number-keyboard) {
	position: relative !important;
	padding-bottom: constant(safe-area-inset-bottom);
	padding-bottom: env(safe-area-inset-bottom);
}
</style>
