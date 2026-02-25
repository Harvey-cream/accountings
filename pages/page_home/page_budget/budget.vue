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
							<view :class="['list-icon-wrap', item.bgClass]">
								<van-icon :name="item.icon" :color="item.iconColor" size="24" />
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
											<view class="progress-bar-fill" :style="{ width: (showAnimation ? item.percent : 0) + '%', backgroundColor: item.iconColor }"></view>
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
					<view class="icon-circle">
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
import { ref, computed, onMounted, watch } from 'vue';
import CapsuleButton from '@/components/CapsuleButton/CapsuleButton.vue';

// --- 状态定义 ---
const showTypeSheet = ref(false);
const showEditPopup = ref(false);
const showCategoryPopup = ref(false);
const selectedCategory = ref(null);
const isAddingCategory = ref(false);
const showAnimation = ref(false);
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
	{ id: 1, type: '月预算', name: '餐饮美食', icon: 'fire-o', iconColor: '#d97706', bgClass: 'bg-orange-light', amount: 1500, spent: 422.55, percent: 28 },
	{ id: 2, type: '月预算', name: '房屋租金', icon: 'wap-home-o', iconColor: '#2563eb', bgClass: 'bg-blue-light', amount: 3000, spent: 3000, percent: 100 },
	{ id: 4, type: '月预算', name: '交通出行', icon: 'logistics', iconColor: '#3b82f6', bgClass: 'bg-blue-light', amount: 500, spent: 120.50, percent: 24 },
	{ id: 5, type: '月预算', name: '休闲娱乐', icon: 'music-o', iconColor: '#8b5cf6', bgClass: 'bg-purple-light', amount: 800, spent: 650, percent: 81 },
	{ id: 6, type: '月预算', name: '购物消费', icon: 'shopping-cart-o', iconColor: '#ec4899', bgClass: 'bg-pink-light', amount: 1200, spent: 1150, percent: 95 },
	{ id: 7, type: '年预算', name: '年度旅行', icon: 'aim', iconColor: '#f59e0b', bgClass: 'bg-yellow-light', amount: 15000, spent: 4000, percent: 27 },
	{ id: 8, type: '年预算', name: '数码产品', icon: 'desktop-o', iconColor: '#64748b', bgClass: 'bg-slate-light', amount: 10000, spent: 8900, percent: 89 }
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

// --- 生命周期 & 动画 ---
onMounted(() => {
	setTimeout(() => {
		showAnimation.value = true;
	}, 100);
});

// 监听切换，重新触发动画
watch(budgetType, () => {
	showAnimation.value = false;
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
.bg-orange-light, 
.bg-blue-light, 
.bg-purple-light, 
.bg-pink-light, 
.bg-green-light, 
.bg-yellow-light, 
.bg-slate-light { 
	background-color: var(--secondary-bg-color); 
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
	background-color: var(--secondary-bg-color) !important;
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
