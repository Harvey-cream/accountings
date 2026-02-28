<template>
	<view class="page-container" :class="currentThemeClass">
		<view class="top-section">
			<view class="header-bar">
				<van-icon name="arrow-left" size="24" color="#0f172a" @click="goBack('/pages/home/accounting_detail')" />
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
			<button class="save-btn" @click="saveBill">
				<van-icon name="success" color="#0f172a" size="18" style="margin-right: 6px" />
				<text class="save-text">保存账单</text>
			</button>
		</view>

		<van-calendar v-model:show="showCalendar" color="#FFD541" :min-date="minDate" :max-date="maxDate" @confirm="onConfirmDate" />
	</view>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue';
import { getAllIcons } from '@/api/api.js';
import { assignDefaultColors } from '@/utils/color.js';
import { goBack } from '@/utils/common.js';

const amount = ref('');
const selectedCategoryId = ref(null); // 初始设为 null
const activeTab = ref('expense'); 

const now = new Date();
// 监听 tab 切换，自动选中该 tab 下的第一个分类
watch(activeTab, (newTab) => {
	const currentList = newTab === 'expense' ? categories.value : incomeCategories.value;
	if (currentList.length > 0) {
		selectedCategoryId.value = currentList[0].id;
	}
});
const currentDate = ref(`${now.getMonth() + 1}/${now.getDate()}/${now.getFullYear()}`);
const minDate = new Date(now.getFullYear() - 10, 0, 1);
const maxDate = new Date();
const location = ref('');
const remark = ref('');
const showCalendar = ref(false);
const showMoreIcons = ref(false);
const inputPlaceholder = ref('0.00'); 

// --- Data ---
const categories = ref([]);
const incomeCategories = ref([]);

const currentCategories = computed(() => {
	return activeTab.value === 'expense' ? categories.value : incomeCategories.value;
});

// 初始设为空，从后端获取
const moreIcons = ref([]);
const moreIncomeIcons = ref([]);

const initCategoriesData = (allIcons) => {
	const normalIcons = allIcons.filter(i => i.group === 'normal');
	// 2. 按 type 拆分：all 类型在两边都展示
	const expenseIcons = normalIcons.filter(i => i.type === 'expense' || i.type === 'all');
	const incomeIcons = normalIcons.filter(i => i.type === 'income' || i.type === 'all');
	
	// 3. 分配固定颜色
	const coloredExpense = assignDefaultColors(expenseIcons);
	const coloredIncome = assignDefaultColors(incomeIcons);

	// 4. 排序逻辑辅助函数
	const moveOtherToEnd = (list) => {
		const rest = list.filter(i => i.name !== '其他');
		const other = list.find(i => i.name === '其他');
		return other ? [...rest, other] : rest;
	};

	const getGridList = (sortedList) => {
		const rest = sortedList.filter(i => i.name !== '其他');
		const other = sortedList.find(i => i.name === '其他');
		const main = rest.slice(0, 7);
		return other ? [...main, other] : main;
	};

	// 5. 更新响应式数据
	moreIcons.value = moveOtherToEnd(coloredExpense);
	moreIncomeIcons.value = moveOtherToEnd(coloredIncome);
	categories.value = getGridList(moreIcons.value);
	incomeCategories.value = getGridList(moreIncomeIcons.value);
	
	// 6. 设置初始选中的分类 ID
	const currentList = activeTab.value === 'expense' ? categories.value : incomeCategories.value;
	if (currentList.length > 0) {
		selectedCategoryId.value = currentList[0].id;
	}
};

onMounted(async () => {
	try {
		const res = await getAllIcons();
		if (res.code === 200) {
			initCategoriesData(res.data);
		}
	} catch (e) {
		console.error('Failed to load icons:', e);
	}
});

const currentMoreIcons = computed(() => {
	return activeTab.value === 'expense' ? moreIcons.value : moreIncomeIcons.value;
});

const onSelectCategory = (cat) => {
	if (cat.name === '其他') {
		showMoreIcons.value = true;
	} else {
		selectedCategoryId.value = cat.id;
	}
};

const onSelectMoreIcon = (icon) => {
	// 查找当前 tab 下的“其他”分类对象并更新它
	const categoriesToSearch = activeTab.value === 'expense' ? categories.value : incomeCategories.value;
	const otherCat = categoriesToSearch.find(c => c.name === '其他');
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
