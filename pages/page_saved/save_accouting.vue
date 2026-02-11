<template>
	<view class="page-container">
		<view class="top-section">
			<view class="header-bar">
				<van-icon name="arrow-left" size="24" color="#0f172a" @click="goBack" />
				<view class="tab-box">
					<view class="tab-item" :class="{ active: activeTab === 'expense' }" @click="activeTab = 'expense'">支出</view>
					<view class="tab-item" :class="{ active: activeTab === 'income' }" @click="activeTab = 'income'">收入</view>
				</view>
				<view style="width: 24px;"></view>
			</view>
		</view>

		<view class="content-card">
			<view class="category-grid">
				<view v-for="cat in currentCategories" :key="cat.id" class="category-item" @click="onSelectCategory(cat)">
					<view class="icon-circle" :class="{ active: selectedCategoryId === cat.id }" :style="{ backgroundColor: cat.colorBg }">
						<van-icon :name="cat.icon" :color="cat.colorIcon" size="24" />
					</view>
					<text class="category-name">{{ cat.name }}</text>
				</view>
			</view>

			<van-popup
				v-model:show="showMoreIcons"
				position="bottom"
				round
				class="more-icons-popup"
			>
				<view class="popup-header">
					<text class="popup-title">更多分类</text>
					<van-icon name="cross" class="close-icon" @click="showMoreIcons = false" />
				</view>
				<view class="category-grid">
					<view v-for="icon in currentMoreIcons" :key="icon.name" class="category-item" @click="onSelectMoreIcon(icon)">
						<view class="icon-circle" :style="{ backgroundColor: icon.colorBg }">
							<van-icon :name="icon.icon" :color="icon.colorIcon" size="24" />
						</view>
						<text class="category-name">{{ icon.name }}</text>
					</view>
				</view>
			</van-popup>

			<view class="form-group">
				<view class="form-row">
					<view class="form-icon-wrap">
						<van-icon name="gold-coin-o" size="20" color="#64748b" />
					</view>
					<view class="form-content">
						<text class="form-label">金额</text>
						<input type="digit" v-model="amount" class="form-input" :placeholder="inputPlaceholder" placeholder-class="input-placeholder"
							@focus="onAmountFocus" @blur="onAmountBlur"/>
					</view>
				</view>

				<!-- Date Picker -->
				<view class="form-row" @click="showCalendar = true">
					<view class="form-icon-wrap">
						<van-icon name="calendar-o" size="20" color="#64748b" />
					</view>
					<view class="form-content">
						<text class="form-label">日期</text>
						<text class="form-value">{{ currentDate }}</text>
					</view>
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
				</view>
			</view>

			<!-- Save Button -->
			<button class="save-btn" @click="saveBill">
				<van-icon name="success" color="#0f172a" size="18" style="margin-right: 6px" />
				<text class="save-text">保存账单</text>
			</button>
		</view>

		<van-calendar v-model:show="showCalendar" color="#FFD541" :min-date="minDate" :max-date="maxDate" @confirm="onConfirmDate" />
	</view>
</template>

<script setup>
import { ref, computed } from 'vue';
const amount = ref('');
const selectedCategoryId = ref(1);
const activeTab = ref('expense'); 

const now = new Date();
const currentDate = ref(`${now.getMonth() + 1}/${now.getDate()}/${now.getFullYear()}`);
const minDate = new Date(now.getFullYear() - 10, 0, 1);
const maxDate = new Date();
const location = ref('');
const remark = ref('');
const showCalendar = ref(false);
const showMoreIcons = ref(false);
const inputPlaceholder = ref('0.00'); 

// --- Data ---
const categories = ref([
	{ id: 1, name: '餐饮', icon: 'logistics', colorBg: '#fffbeb', colorIcon: '#d97706' },
	{ id: 2, name: '购物', icon: 'bag-o', colorBg: '#eff6ff', colorIcon: '#3b82f6' },
	{ id: 3, name: '交通', icon: 'logistics', colorBg: '#ecfdf5', colorIcon: '#10b981' },
	{ id: 4, name: '娱乐', icon: 'video-o', colorBg: '#f3e8ff', colorIcon: '#9333ea' },
	{ id: 5, name: '医疗', icon: 'friends-o', colorBg: '#fee2e2', colorIcon: '#ef4444' },
	{ id: 6, name: '学习', icon: 'bookmark-o', colorBg: '#ffedd5', colorIcon: '#f97316' },
	{ id: 7, name: '房租', icon: 'wap-home-o', colorBg: '#ecfeff', colorIcon: '#06b6d4' },
	{ id: 8, name: '其他', icon: 'ellipsis', colorBg: '#f1f5f9', colorIcon: '#64748b' }
]);

const incomeCategories = ref([
	{ id: 101, name: '工资', icon: 'gold-coin-o', colorBg: '#f0fdf4', colorIcon: '#16a34a' },
	{ id: 102, name: '兼职', icon: 'records', colorBg: '#eff6ff', colorIcon: '#3b82f6' },
	{ id: 103, name: '理财', icon: 'balance-o', colorBg: '#fffbeb', colorIcon: '#d97706' },
	{ id: 104, name: '奖金', icon: 'diamond-o', colorBg: '#fdf2f8', colorIcon: '#db2777' },
	{ id: 106, name: '报销', icon: 'notes-o', colorBg: '#eff6ff', colorIcon: '#3b82f6' },
	{ id: 107, name: '租金', icon: 'wap-home-o', colorBg: '#ecfeff', colorIcon: '#06b6d4' },
	{ id: 108, name: '分红', icon: 'chart-trending-o', colorBg: '#f0fdf4', colorIcon: '#16a34a' },
	{ id: 105, name: '其他', icon: 'ellipsis', colorBg: '#f1f5f9', colorIcon: '#64748b' }
]);

const currentCategories = computed(() => {
	return activeTab.value === 'expense' ? categories.value : incomeCategories.value;
});

const moreIcons = ref([
	{ name: '电影', icon: 'video-o', colorBg: '#f3e8ff', colorIcon: '#9333ea' },
	{ name: '运动', icon: 'fire-o', colorBg: '#ffedd5', colorIcon: '#f97316' },
	{ name: '礼物', icon: 'gift-o', colorBg: '#fdf2f8', colorIcon: '#db2777' },
	{ name: '餐饮', icon: 'logistics', colorBg: '#fffbeb', colorIcon: '#d97706' },
	{ name: '办公', icon: 'description', colorBg: '#eff6ff', colorIcon: '#3b82f6' },
	{ name: '维修', icon: 'setting-o', colorBg: '#ecfdf5', colorIcon: '#10b981' },
	{ name: '话费', icon: 'phone-o', colorBg: '#fee2e2', colorIcon: '#ef4444' },
	{ name: '社交', icon: 'friends-o', colorBg: '#f3e8ff', colorIcon: '#9333ea' },
	{ name: '美发', icon: 'brush-o', colorBg: '#ffedd5', colorIcon: '#f97316' },
	{ name: '其他', icon: 'ellipsis', colorBg: '#f1f5f9', colorIcon: '#64748b' }
]);

const moreIncomeIcons = ref([
	{ name: '礼金', icon: 'gift-o', colorBg: '#fdf2f8', colorIcon: '#db2777' },
	{ name: '退款', icon: 'refund-o', colorBg: '#fffbeb', colorIcon: '#d97706' },
	{ name: '利息', icon: 'balance-list-o', colorBg: '#f1f5f9', colorIcon: '#64748b' },
	{ name: '二手', icon: 'shop-o', colorBg: '#ffedd5', colorIcon: '#f97316' },
	{ name: '红包', icon: 'paimai', colorBg: '#fee2e2', colorIcon: '#ef4444' },
	{ name: '其他', icon: 'ellipsis', colorBg: '#f1f5f9', colorIcon: '#64748b' }
]);

const currentMoreIcons = computed(() => {
	return activeTab.value === 'expense' ? moreIcons.value : moreIncomeIcons.value;
});

// --- Methods ---
const goBack = () => {
	const pages = getCurrentPages();
	if (pages.length > 1) {
		uni.navigateBack();
	} else {
		uni.switchTab({
			url: '/pages/home/accounting_detail'
		});
	}
};

const onSelectCategory = (cat) => {
	if ((activeTab.value === 'expense' && cat.id === 8) || (activeTab.value === 'income' && cat.id === 105)) {
		showMoreIcons.value = true;
	} else {
		selectedCategoryId.value = cat.id;
	}
};

const onSelectMoreIcon = (icon) => {
	// 这里可以根据需要处理选择更多图标后的逻辑
	// 比如更新“其他”分类的图标或者直接选中
	const targetId = activeTab.value === 'expense' ? 8 : 105;
	const categoriesToSearch = activeTab.value === 'expense' ? categories.value : incomeCategories.value;
	const otherCat = categoriesToSearch.find(c => c.id === targetId);
	if (otherCat) {
		otherCat.icon = icon.icon;
		otherCat.colorBg = icon.colorBg;
		otherCat.colorIcon = icon.colorIcon;
		otherCat.name = icon.name;
		selectedCategoryId.value = otherCat.id;
	}
	showMoreIcons.value = false;
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
	padding: 10px 20px 30px;
	display: flex;
	flex-direction: column;
}

.header-bar {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 10px;

}

.tab-box {
	display: flex;
	gap: 40px;
	background-color: transparent;
}

.tab-item {
	position: relative;
	height: 30px;
	line-height: 30px;
	text-align: center;
	font-size: 16px;
	font-weight: 500;
	color: #0f172a;
	transition: all 0.2s;
}

.tab-item.active {
	font-weight: bold;
	color: #000;
}

.tab-item.active::after {
	content: '';
	position: absolute;
	bottom: -2px;
	left: 50%;
	transform: translateX(-50%);
	width: 28px;
	height: 3px;
	background-color: #000;
	border-radius: 2px;
}

/* --- Main Content --- */
.content-card {
	flex: 1;
	background-color: #fff;
	margin-top: -20px;
	padding: 10px 10px 24px;
	display: flex;
	flex-direction: column;
}

.section-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
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


/* Category Grid */
.category-grid {
	display: grid;
	grid-template-columns: repeat(4, 1fr);
	gap: 20px;
	padding: 15px;
}

.category-item {
	display: flex;
	flex-direction: column;
	align-items: center;
	gap: 8px;
}

.icon-circle {
	width: 45px;
	height: 45px;
	border-radius: 25px;
	display: flex;
	justify-content: center;
	align-items: center;
	transition: transform 0.2s;
	border: 2px solid transparent;
}

.icon-circle.active {
	border-color: #ffd541;
	transform: scale(1.1);
	box-shadow: 0 4px 12px rgba(255, 213, 65, 0.3);
}

.category-item:active .icon-circle {
	transform: scale(0.9);
}

.category-name {
	font-size: 12px;
	color: #64748b;
}

/* More Icons Popup */
.more-icons-popup {
	max-height: 70vh;
	padding-bottom: 20px;
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

/* Form Group */
.form-group {
	background-color: #fff;
	padding: 10px 25px;
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
	width: 42px;
	height: 42px;
	border-radius: 8px;
	display: flex;
	align-items: center;
	justify-content: center;
	margin-right: 15px;
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
	background-color: #ffd541;
	border-radius: 12px;
	height: 48px;
	display: flex;
	align-items: center;
	justify-content: center;
	border: none;
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
