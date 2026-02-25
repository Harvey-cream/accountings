<template>
	<view class="page-container" :class="currentThemeClass">
		<!-- Header -->
		<view class="header">
			<view class="status-bar"></view>
			<view class="title-row">
				<van-icon name="arrow-left" size="20" @click="goBack" />
				<text class="page-title">数据导出</text>
				<view class="placeholder"></view>
			</view>
			
			<view class="date-selector" @click="showCalendar = true">
				<view class="date-range">
					<text class="date-text">{{ dateRangeText }}</text>
					<van-icon name="calendar-o" size="20" color="#333" />
				</view>
				<text class="date-hint">点击选择导出时间范围</text>
			</view>
		</view>

		<!-- Summary -->
		<view class="summary-card">
			<view class="stat-item">
				<text class="stat-label">总收入</text>
				<text class="stat-value income">{{ summary.income }}</text>
			</view>
			<view class="divider"></view>
			<view class="stat-item">
				<text class="stat-label">总支出</text>
				<text class="stat-value expense">{{ summary.expense }}</text>
			</view>
			<view class="divider"></view>
			<view class="stat-item">
				<text class="stat-label">笔数</text>
				<text class="stat-value count">{{ summary.count }}</text>
			</view>
		</view>

		<!-- Transactions List Preview -->
		<view class="transactions-section">
			<view class="section-title">
				<text>导出预览</text>
				<text class="subtitle">仅展示部分数据</text>
			</view>
			
			<van-list v-model:loading="loading" :finished="finished" finished-text="更多数据将包含在导出文件中" @load="onLoad">
				<view v-for="group in dailyTransactions" :key="group.id" class="day-group">
					<view class="day-header">
						<text class="day-date">{{ group.date }}</text>
						<text class="text-style-desc">支出: {{ group.totalExpense }}</text>
					</view>

					<view class="list-container">
						<van-cell v-for="item in group.items" :key="item.id" center class="custom-cell flat-cell">
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
					</view>
				</view>
			</van-list>
		</view>

		<!-- Bottom Action -->
		<view class="bottom-action">
			<van-button round block type="primary" color="#ffd541" text-color="#000" @click="onExport">
				确认导出
			</van-button>
		</view>

		<!-- Calendar -->
		<van-calendar
			v-model:show="showCalendar"
			type="range"
			color="#ffd541"
			:min-date="minDate"
			:max-date="maxDate"
			@confirm="onConfirmDate"
		/>
	</view>
</template>

<script setup>
import { ref, computed } from 'vue';

const showCalendar = ref(false);
const minDate = new Date(2020, 0, 1);
const maxDate = new Date();
const dateRange = ref([new Date(new Date().setDate(1)), new Date()]); // Default to current month

const dateRangeText = computed(() => {
	const [start, end] = dateRange.value;
	if (!start || !end) return '请选择日期范围';
	return `${formatDate(start)} - ${formatDate(end)}`;
});

const formatDate = (date) => {
	return `${date.getFullYear()}/${date.getMonth() + 1}/${date.getDate()}`;
};

const summary = ref({
	income: '4,200.00',
	expense: '26,510.00',
	count: 158
});

const loading = ref(false);
const finished = ref(false);
const dailyTransactions = ref([]);

const goBack = () => {
	uni.navigateBack();
};

const onConfirmDate = (values) => {
	const [start, end] = values;
	dateRange.value = [start, end];
	showCalendar.value = false;
	
	// Reset list to simulate reloading data for new range
	dailyTransactions.value = [];
	loading.value = true;
	finished.value = false;
	onLoad();
	
	uni.showToast({
		title: '已更新预览',
		icon: 'none'
	});
};

const onLoad = () => {
	setTimeout(() => {
		if (dailyTransactions.value.length >= 4) {
			finished.value = true;
			return;
		}
		
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
	}, 500);
};

const onExport = () => {
	uni.showLoading({
		title: '正在导出...',
		mask: true
	});
	
	setTimeout(() => {
		uni.hideLoading();
		uni.showModal({
			title: '导出成功',
			content: `账单数据 (${dateRangeText.value}) 已导出至手机存储/Download目录`,
			showCancel: false,
			confirmText: '知道了',
			confirmColor: '#ffd541'
		});
	}, 1500);
};
</script>

<style scoped>
.page-container {
	min-height: 100vh;
	padding-bottom: 90px;
	background-color: #f8f8f8;
}

/* Header */
.header {
	background-color: #ffd541;
	padding: 20px 20px 30px;
}

.status-bar {
	height: var(--status-bar-height);
}

.title-row {
	display: flex;
	justify-content: space-between;
	align-items: center;
	height: 44px;
	margin-bottom: 10px;
}

.page-title {
	font-size: 16px;
	font-weight: 500;
}

.placeholder {
	width: 20px;
}

.date-selector {
	background-color: rgba(255, 255, 255, 0.9);
	border-radius: 12px;
	padding: 16px;
	display: flex;
	flex-direction: column;
	align-items: center;
	box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.date-range {
	display: flex;
	align-items: center;
	gap: 8px;
	margin-bottom: 4px;
}

.date-text {
	font-size: 18px;
	font-weight: 600;
	color: #333;
}

.date-hint {
	font-size: 12px;
	color: #666;
}

/* Summary Card */
.summary-card {
	background-color: #fff;
	margin: -20px 16px 16px;
	border-radius: 12px;
	padding: 20px;
	display: flex;
	justify-content: space-between;
	align-items: center;
	box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
	position: relative;
	z-index: 1;
}

.stat-item {
	flex: 1;
	display: flex;
	flex-direction: column;
	align-items: center;
}

.stat-label {
	font-size: 12px;
	color: #999;
	margin-bottom: 6px;
}

.stat-value {
	font-size: 18px;
	font-weight: 600;
}

.stat-value.income {
	color: #f43f5e;
}

.stat-value.expense {
	color: #10b981;
}

.stat-value.count {
	color: #333;
}

.divider {
	width: 1px;
	height: 30px;
	background-color: #eee;
}

/* Transactions List */
.transactions-section {
	margin: 0 16px;
}

.section-title {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 12px;
	padding: 0 4px;
	font-size: 14px;
	font-weight: 600;
	color: #333;
}

.subtitle {
	font-size: 12px;
	color: #999;
	font-weight: normal;
}

.day-group {
	background-color: #fff;
	border-radius: 12px;
	overflow: hidden;
	margin-bottom: 12px;
}

.day-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	padding: 12px 16px;
	background-color: #fafafa;
	border-bottom: 1px solid #f1f5f9;
}

.day-date {
	font-size: 14px;
	font-weight: 600;
	color: #333;
}

.text-style-desc {
	font-size: 12px;
	color: #999;
}

.custom-cell {
	padding: 16px !important;
}

.list-icon-wrap {
	width: 36px;
	height: 36px;
	border-radius: 10px;
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

.cell-title {
	font-size: 14px;
	color: #333;
	margin-bottom: 2px;
}

.cell-time {
	font-size: 12px;
	color: #999;
}

.cell-right {
	display: flex;
	align-items: center;
}

.cell-amount {
	font-size: 16px;
	font-weight: 600;
	color: #333;
}

/* Colors from original file */
.bg-amber-light { background-color: #fef3c7; }
.bg-blue-light { background-color: #dbeafe; }
.bg-purple-light { background-color: #f3e8ff; }
.bg-emerald-light { background-color: #d1fae5; }

/* Bottom Action */
.bottom-action {
	position: fixed;
	bottom: 0;
	left: 0;
	right: 0;
	padding: 16px 20px;
	background-color: #fff;
	box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.05);
	z-index: 10;
}
</style>