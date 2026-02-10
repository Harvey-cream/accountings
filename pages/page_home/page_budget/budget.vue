<template>
	<view class="page-container">
		<!-- 顶部固定导航区域 -->
		<view class="fixed-nav-container">
			<view class="nav-header">
				<!-- 中间预算类型选择 -->
				<view class="type-selector" @click="showTypeSheet = true">
					<text class="type-text">{{ budgetType }}</text>
					<van-icon name="arrow-down" size="12" color="#0f172a" />
				</view>
			</view>
		</view>
		<scroll-view scroll-y class="main-content">
			<view class="card-container">
				<view class="budget-card">
					<view class="card-header">
						<text class="card-title">{{ budgetType }}概览</text>
						<view class="edit-btn" @click="onEditBudget">
							<text class="edit-text">编辑</text>
							<van-icon name="edit" size="14" color="#64748b" />
						</view>
					</view>
					
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
							<view :class="['list-icon-wrap', item.bgClass]" :style="item.customBg ? { backgroundColor: item.customBg } : {}">
								<van-icon :name="item.icon" :color="item.iconColor" size="20" />
							</view>
						</template>
						<template #title>
							<view class="cell-content">
								<view class="cell-main">
									<text class="text-style-title">{{ item.name }}</text>
									<view class="progress-bar-bg">
										<view class="progress-bar-fill" :style="{ width: item.percent + '%', backgroundColor: item.iconColor }"></view>
									</view>
								</view>
								<view class="cell-right">
									<view class="amount-info">
										<text class="spent-text text-style-number">¥{{ item.spent.toFixed(2) }}</text>
										<text class="total-text text-style-desc">/ ¥{{ item.amount.toFixed(2) }}</text>
									</view>
									<text class="percent-text text-style-desc">{{ item.percent }}%</text>
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
import { ref, computed } from 'vue';

// --- 状态定义 ---
const showTypeSheet = ref(false);
const showEditPopup = ref(false);
const showCategoryPopup = ref(false);
const selectedCategory = ref(null);
const isAddingCategory = ref(false);
const editBudgetType = ref('月预算');
const editBudgetValue = ref('');

const budgetType = ref('月预算');
const viewActions = [
	{ name: '月预算' },
	{ name: '年预算' },
];

// 记账分类数据
const categories = ref([
	{ id: 1, name: '餐饮', icon: 'logistics', colorBg: '#fffbeb', colorIcon: '#d97706' },
	{ id: 2, name: '购物', icon: 'bag-o', colorBg: '#eff6ff', colorIcon: '#3b82f6' },
	{ id: 3, name: '交通', icon: 'logistics', colorBg: '#ecfdf5', colorIcon: '#10b981' },
	{ id: 4, name: '娱乐', icon: 'video-o', colorBg: '#f3e8ff', colorIcon: '#9333ea' },
	{ id: 5, name: '医疗', icon: 'friends-o', colorBg: '#fee2e2', colorIcon: '#ef4444' },
	{ id: 6, name: '学习', icon: 'bookmark-o', colorBg: '#ffedd5', colorIcon: '#f97316' },
	{ id: 7, name: '房租', icon: 'wap-home-o', colorBg: '#ecfeff', colorIcon: '#06b6d4' },
	{ id: 8, name: '工资', icon: 'gold-coin-o', colorBg: '#f0fdf4', colorIcon: '#16a34a' },
	{ id: 9, name: '礼物', icon: 'gift-o', colorBg: '#fdf2f8', colorIcon: '#db2777' },
	{ id: 10, name: '其他', icon: 'ellipsis', colorBg: '#f1f5f9', colorIcon: '#64748b' }
]);

// 分类预算列表
const categoryBudgets = ref([
	{ id: 1, type: '月预算', name: '餐饮美食', icon: 'fire-o', iconColor: '#d97706', bgClass: 'bg-orange-light', amount: 1500, spent: 422.55, percent: 30 },
	{ id: 2, type: '月预算', name: '房屋租金', icon: 'wap-home-o', iconColor: '#2563eb', bgClass: 'bg-blue-light', amount: 3000, spent: 3000, percent: 100 },
	{ id: 3, type: '年预算', name: '保险支出', icon: 'shield-envelop-o', iconColor: '#10b981', bgClass: 'bg-green-light', amount: 5000, spent: 1200, percent: 24 }
]);

// 模拟数据
const monthBudget = ref(5000);
const monthExpense = ref(3200);
const yearBudget = ref(60000);
const yearExpense = ref(45000);

// --- 计算属性 ---
const filteredCategoryBudgets = computed(() => {
	return categoryBudgets.value.filter(item => item.type === budgetType.value);
});

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

// --- 方法 ---
const onTypeSelect = (event) => {
	budgetType.value = event.name;
	showTypeSheet.value = false;
};

const onEditBudget = () => {
	isAddingCategory.value = false;
	editBudgetType.value = budgetType.value;
	
	// 回显当前已有的预算值
	const currentVal = editBudgetType.value === '月预算' ? monthBudget.value : yearBudget.value;
	editBudgetValue.value = currentVal > 0 ? currentVal.toString() : '';
	
	showEditPopup.value = true;
};

const onAddBudget = () => {
	isAddingCategory.value = true;
	showCategoryPopup.value = true;
};

const onSelectCategory = (cat) => {
	selectedCategory.value = cat;
	editBudgetValue.value = '';
	showCategoryPopup.value = false;
	showEditPopup.value = true;
};

const onConfirmAmount = () => {
	const value = parseFloat(editBudgetValue.value) || 0;
	
	if (isAddingCategory.value && selectedCategory.value) {
		// 添加或更新分类预算
		const existingIdx = categoryBudgets.value.findIndex(b => b.name === selectedCategory.value.name && b.type === budgetType.value);
		if (existingIdx > -1) {
			categoryBudgets.value[existingIdx].amount = value;
		} else {
			categoryBudgets.value.push({
				id: Date.now(),
				type: budgetType.value,
				name: selectedCategory.value.name,
				icon: selectedCategory.value.icon,
				iconColor: selectedCategory.value.colorIcon,
				bgClass: 'bg-custom', // 后面在 style 中定义一个通用背景
				customBg: selectedCategory.value.colorBg,
				amount: value,
				spent: 0,
				percent: 0
			});
		}
		uni.showToast({ title: '添加成功', icon: 'success' });
	} else {
		// 更新总预算
		if (editBudgetType.value === '月预算') {
			monthBudget.value = value;
		} else {
			yearBudget.value = value;
		}
		uni.showToast({ title: '设置成功', icon: 'success' });
	}
	
	showEditPopup.value = false;
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
	background-color: #ffd541;
	padding: 5px 20px 0;
	box-sizing: border-box;
	flex-shrink: 0;
	z-index: 2001; 
}
:deep(.top-action-sheet) {
	margin-top: 57px; 
}

.nav-header {
	display: flex;
	flex-direction: column;
	align-items: center; 
	gap: 10px; 
	margin-bottom: 8px;
	height: 44px;
	justify-content: center;
}

.type-selector {
	display: flex;
	align-items: center;
	gap: 4px;
	padding: 4px 12px;
	border-radius: 14px;
}

.type-text {
	font-size: var(--font-size-number);
	font-weight: 700;
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
	background-color: #f1f5f9;
	border-radius: 12px;
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
	gap: 12px;
}

.stat-row {
	display: flex;
	justify-content: space-between;
	align-items: baseline;
}

.small-row {
	margin-top: 4px;
}

.label {
	font-size: 13px;
	color: #94a3b8;
}

.value {
	font-weight: 600;
	color: #0f172a;
}

.large-num {
	font-size: 24px;
}

.text-danger {
	color: #ef4444;
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

.empty-sub {
	font-size: 12px;
	color: #cbd5e1;
}

/* 底部固定栏 */
.bottom-bar {
	position: fixed;
	bottom: 0;
	left: 0;
	right: 0;
	background-color: #fff;
	padding: 12px 16px 30px; /* 适配底部安全区 */
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
	border-radius: 16px;
	overflow: hidden;
}

.custom-cell {
	padding: 16px !important;
}

.flat-cell {
	background: transparent !important;
}

.list-icon-wrap {
	width: 44px;
	height: 44px;
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
}

.cell-main {
	display: flex;
	flex-direction: column;
	gap: 8px;
	flex: 1;
	margin-right: 20px;
}

.progress-bar-bg {
	height: 6px;
	background: #f1f5f9;
	border-radius: 3px;
	overflow: hidden;
}

.progress-bar-fill {
	height: 100%;
	border-radius: 3px;
	transition: width 0.3s ease;
}

.cell-right {
	display: flex;
	flex-direction: column;
	align-items: flex-end;
	gap: 4px;
}

.amount-info {
	display: flex;
	align-items: baseline;
}

.spent-text {
	font-size: 16px;
	font-weight: 700;
	color: #0f172a;
}

.total-text {
	font-size: 12px;
	color: #94a3b8;
	margin-left: 2px;
}

.percent-text {
	font-size: 12px;
	font-weight: 500;
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
	width: 50px;
	height: 50px;
	border-radius: 25px;
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
