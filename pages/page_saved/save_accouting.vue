<template>
	<view class="page-container">
		<!-- Top Area: Header & Amount -->
		<view class="top-section">
			<!-- Header -->
			<view class="header-bar">
				<van-icon name="cross" size="24" color="#0f172a" @click="goBack" />
				<text class="page-title">新增账单</text>
				<van-icon name="question-o" size="24" color="#0f172a" />
			</view>

			<!-- Amount Display -->
			<view class="amount-section">
				<text class="amount-label">支出金额</text>
				<view class="amount-row">
					<text class="currency-symbol">¥</text>
					<input type="digit" v-model="amount" class="amount-input" :placeholder="inputPlaceholder" placeholder-class="amount-placeholder"
						@focus="onAmountFocus" @blur="onAmountBlur"/>
				</view>
			</view>
		</view>

		<!-- Main Content: White Card -->
		<view class="content-card">
			<!-- Categories -->
			<view class="section-header">
				<text class="section-title">选择分类</text>
				<text class="section-action">管理分类</text>
			</view>

			<view class="category-grid">
				<view v-for="cat in categories" :key="cat.id" class="category-item" @click="selectCategory(cat.id)">
					<view :class="['icon-circle', { active: selectedCategoryId === cat.id }]" :style="{ backgroundColor: cat.colorBg }">
						<van-icon :name="cat.icon" :color="cat.colorIcon" size="24" />
					</view>
					<text class="category-name">{{ cat.name }}</text>
				</view>
			</view>

			<!-- Bill Details -->
			<view class="section-header mt-6">
				<text class="section-title">账单详情</text>
			</view>

			<view class="form-group">
				<!-- Date Picker -->
				<view class="form-row" @click="showCalendar = true">
					<view class="form-icon-wrap">
						<van-icon name="calendar-o" size="20" color="#64748b" />
					</view>
					<view class="form-content">
						<text class="form-label">日期</text>
						<text class="form-value">{{ currentDate }}</text>
					</view>
					<van-icon name="calendar-o" size="16" color="#0f172a" />
				</view>

				<!-- Location -->
				<view class="form-row" @click="chooseLocation">
					<view class="form-icon-wrap">
						<van-icon name="location-o" size="20" color="#64748b" />
					</view>
					<view class="form-content">
						<text class="form-label">位置</text>
						<text class="form-value placeholder" v-if="!location">点击添加位置</text>
						<text class="form-value" v-else>{{ location }}</text>
					</view>
				</view>

				<!-- Remark -->
				<view class="form-row no-border">
					<view class="form-icon-wrap">
						<van-icon name="description" size="20" color="#64748b" />
					</view>
					<view class="form-content">
						<text class="form-label">备注</text>
						<input type="text" v-model="remark" class="form-input" placeholder="点击输入备注" placeholder-class="input-placeholder" />
					</view>
					<view class="remark-icon-btn">
						<van-icon name="edit" size="16" color="#0f172a" />
					</view>
				</view>
			</view>

			<!-- Save Button -->
			<button class="save-btn" @click="saveBill">
				<van-icon name="success" color="#0f172a" size="18" style="margin-right: 6px" />
				<text class="save-text">保存账单</text>
			</button>

			<view class="split-bill-banner">
				<view class="split-icon">
					<van-icon name="friends" color="#F59E0B" size="20" />
				</view>
				<view class="split-content">
					<text class="split-title">多人分账?</text>
					<text class="split-desc">你可以邀请好友一起分担这笔费用。</text>
				</view>
			</view>
		</view>

		<van-calendar v-model:show="showCalendar" color="#FFD541" :min-date="minDate" :max-date="maxDate" @confirm="onConfirmDate" />
	</view>
</template>

<script setup>
import { ref } from 'vue';
const amount = ref('');
const selectedCategoryId = ref(1);

const now = new Date();
const currentDate = ref(`${now.getMonth() + 1}/${now.getDate()}/${now.getFullYear()}`);
const minDate = new Date(now.getFullYear() - 10, 0, 1);
const maxDate = new Date();
const location = ref('');
const remark = ref('');
const showCalendar = ref(false);
const inputPlaceholder = ref('0.00'); 

// --- Data ---
const categories = ref([
	{ id: 1, name: '餐饮', icon: 'logistics', colorBg: '#fffbeb', colorIcon: '#d97706' }, // using logistics as fork-knife placeholder
	{ id: 2, name: '购物', icon: 'bag-o', colorBg: '#eff6ff', colorIcon: '#3b82f6' },
	{ id: 3, name: '交通', icon: 'logistics', colorBg: '#ecfdf5', colorIcon: '#10b981' }, // car placeholder
	{ id: 4, name: '娱乐', icon: 'video-o', colorBg: '#f3e8ff', colorIcon: '#9333ea' },
	{ id: 5, name: '医疗', icon: 'friends-o', colorBg: '#fee2e2', colorIcon: '#ef4444' },
	{ id: 6, name: '学习', icon: 'bookmark-o', colorBg: '#ffedd5', colorIcon: '#f97316' },
	{ id: 7, name: '房租', icon: 'wap-home-o', colorBg: '#ecfeff', colorIcon: '#06b6d4' },
	{ id: 8, name: '其他', icon: 'ellipsis', colorBg: '#f1f5f9', colorIcon: '#64748b' }
]);

// --- Methods ---
const goBack = () => {
	uni.navigateBack();
};

const selectCategory = (id) => {
	selectedCategoryId.value = id;
};

const chooseLocation = () => {
	uni.chooseLocation({
		success: (res) => {
			// 优先使用名称，如果名称为空则使用地址
			location.value = res.name || res.address;
		},
		fail: (err) => {
			// 用户取消或权限被拒绝时，不做任何操作或提示
			console.log('Location selection cancelled or failed', err);
		}
	});
};
const onAmountFocus = () => {
	inputPlaceholder.value = '';
};

const onAmountBlur = () => {
	if (!amount.value) {
		inputPlaceholder.value = '0.00';
	}
};

const onConfirmDate = (date) => {
	const d = new Date(date);
	currentDate.value = `${d.getMonth() + 1}/${d.getDate()}/${d.getFullYear()}`;
	showCalendar.value = false;
};

const saveBill = () => {
	if (!amount.value) {
		uni.showToast({ title: '请输入金额', icon: 'none' });
		return;
	}

	uni.showLoading({ title: '保存中' });
	setTimeout(() => {
		uni.hideLoading();
		uni.showToast({ title: '保存成功' });
		setTimeout(() => {
			uni.navigateBack();
		}, 1000);
	}, 800);
};
</script>

<style scoped>
.page-container {
	min-height: 100vh;
	background-color: #f7f8fa;
	display: flex;
	flex-direction: column;
}

/* --- Top Section --- */
.top-section {
	background-color: #ffd541;
	padding: 20px 20px 40px; /* Top padding for status bar */
	padding-bottom: 50px; /* Extra padding for overlap */
	display: flex;
	flex-direction: column;
}

.header-bar {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 20px;
}

.page-title {
	font-size: 16px;
	font-weight: 700;
	color: #0f172a;
}

.amount-section {
	display: flex;
	flex-direction: column;
	align-items: center;
}

.amount-label {
	font-size: 12px;
	color: rgba(15, 23, 42, 0.6);
	margin-bottom: 6px;
}

.amount-row {
	display: flex;
	align-items: center;
	position: relative;
}

.currency-symbol {
	font-size: 24px;
	font-weight: 700;
	color: #0f172a;
	margin-right: 4px;
	margin-top: 6px;
}

.amount-input {
	font-size: 40px;
	font-weight: 700;
	color: #0f172a;
	width: 200px;
	text-align: center;
	height: 50px;
	line-height: 50px;
	background: transparent;
	border: none;
}

.amount-placeholder {
	color: rgba(15, 23, 42, 0.4);
}

.type-switch {
	display: flex;
	flex-direction: column;
	margin-left: 8px;
	background-color: #fff;
	border-radius: 4px;
	padding: 2px;
}

/* --- Main Content --- */
.content-card {
	flex: 1;
	background-color: #fff;
	margin-top: -30px;
	border-top-left-radius: 24px;
	border-top-right-radius: 24px;
	padding: 24px 20px;
	display: flex;
	flex-direction: column;
}

.section-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 16px;
}

.section-title {
	font-size: 14px;
	font-weight: 700;
	color: #94a3b8;
}

.section-action {
	font-size: 12px;
	color: #ffd541;
	font-weight: 500;
}

.mt-6 {
	margin-top: 24px;
}

/* Category Grid */
.category-grid {
	display: flex;
	flex-wrap: wrap;
	justify-content: space-between;
	gap: 16px 0;
}

.category-item {
	width: 25%;
	display: flex;
	flex-direction: column;
	align-items: center;
}

.icon-circle {
	width: 44px;
	height: 44px;
	border-radius: 16px;
	display: flex;
	align-items: center;
	justify-content: center;
	margin-bottom: 6px;
	transition: all 0.2s;
	border: 2px solid transparent;
}

.icon-circle.active {
	border-color: #ffd541;
	transform: scale(1.05);
	box-shadow: 0 4px 10px rgba(255, 213, 65, 0.3);
}

.category-name {
	font-size: 11px;
	font-weight: 500;
	color: #0f172a;
}

/* Form Group */
.form-group {
	background-color: #fff;
	border-radius: 12px;
}

.form-row {
	display: flex;
	align-items: center;
	padding: 12px 0;
	border-bottom: 1px solid #f1f5f9;
}

.no-border {
	border-bottom: none;
}

.form-icon-wrap {
	width: 32px;
	height: 32px;
	background-color: #f8fafc;
	border-radius: 8px;
	display: flex;
	align-items: center;
	justify-content: center;
	margin-right: 12px;
}

.form-content {
	flex: 1;
	display: flex;
	flex-direction: row;
	align-items: center;
}

.form-label {
	font-size: 13px;
	font-weight: 700;
	color: #0f172a;
	width: 50px;
}

.form-value {
	flex: 1;
	font-size: 14px;
	color: #0f172a;
}

.placeholder {
	color: #94a3b8;
	font-size: 13px;
}

.form-input {
	flex: 1;
	font-size: 14px;
	color: #0f172a;
	border: none;
	background: transparent;
}

.input-placeholder {
	color: #94a3b8;
	font-size: 13px;
}

.remark-icon-btn {
	width: 28px;
	height: 28px;
	background-color: #0f172a;
	border-radius: 50%;
	display: flex;
	align-items: center;
	justify-content: center;
}
.remark-icon-btn :deep(.van-icon) {
	color: #fff !important;
}

/* Save Button */
.save-btn {
	margin-top: 24px;
	background-color: #ffd541;
	border-radius: 12px;
	height: 48px;
	display: flex;
	align-items: center;
	justify-content: center;
	border: none;
	box-shadow: 0 4px 12px rgba(255, 213, 65, 0.4);
}

.save-text {
	font-size: 14px;
	font-weight: 700;
	color: #0f172a;
}

/* Split Bill */
.split-bill-banner {
	margin-top: 24px;
	background-color: #fffbeb;
	border-radius: 16px;
	padding: 12px;
	display: flex;
	align-items: center;
	border: 1px solid #fef3c7;
}

.split-icon {
	margin-right: 10px;
}

.split-content {
	display: flex;
	flex-direction: column;
}

.split-title {
	font-size: 13px;
	font-weight: 700;
	color: #0f172a;
	margin-bottom: 2px;
}

.split-desc {
	font-size: 11px;
	color: #64748b;
}
</style>
