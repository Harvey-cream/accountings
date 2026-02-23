<template>
	<view class="page-container">
		<!-- 年份账单列表视图 -->
		<view v-if="!currentYear" class="year-list-container">
			<view class="header-row">
				<view class="section-title">年度账单</view>
				<CapsuleButton />
			</view>
			<van-swipe-cell v-for="(yearData, index) in yearsList" :key="yearData.year" right-width="65" class="year-swipe-cell">
				<view class="year-card" @click="openYearDetail(yearData)">
					<view class="year-card-left">
						<text class="year-text">{{ yearData.year }}年</text>
						<view class="year-stats">
							<text class="stat-text income">收入 {{ yearData.income }}</text>
							<text class="stat-text expense">支出 {{ yearData.expense }}</text>
						</view>
					</view>
					<van-icon name="arrow" color="#94a3b8" />
				</view>
				<template #right>
					<view class="delete-button" @click="onDeleteYear(index)">
						<van-icon name="delete-o" size="24" color="#fff" />
					</view>
				</template>
			</van-swipe-cell>
		</view>

		<!-- 年度账单明细视图 -->
		<view v-else class="detail-container">
			<!-- 顶部导航栏 -->
			<view class="detail-header">
				<view class="header-left" @click="closeYearDetail">
					<van-icon name="arrow-left" size="20" color="#0f172a" />
					<text class="header-title">{{ currentYear.year }}年账单</text>
				</view>
				<view class="header-right" @click="toggleEditMode">
					<text class="action-text">{{ isEditMode ? '完成' : '管理' }}</text>
				</view>
			</view>

			<!-- 批量操作栏 -->
			<view v-if="isEditMode" class="batch-action-bar">
				<view class="select-all" @click.stop="toggleSelectAll">
					<van-checkbox :model-value="isAllSelected" checked-color="#f59e0b" icon-size="18px" @click.stop="toggleSelectAll">全选</van-checkbox>
				</view>
				<view class="delete-btn" @click="batchDelete" :class="{ 'disabled': selectedIds.length === 0 }">
					<text>删除</text>
				</view>
			</view>

			<!-- 账单列表 -->
			<scroll-view scroll-y class="bill-scroll-view" :style="{ height: isEditMode ? 'calc(100vh - 140px)' : 'calc(100vh - 88px)' }">
				<view v-for="group in currentYearDetails" :key="group.id" class="day-group">
					<view class="day-header">
						<text class="day-date">{{ group.date }}</text>
						<text class="text-style-desc">支出: {{ group.totalExpense }}</text>
					</view>

					<view class="list-container">
						<van-swipe-cell v-for="item in group.items" :key="item.id" right-width="65" :disabled="isEditMode">
							<van-cell center class="custom-cell flat-cell" @click="onItemClick(item)">
								<template #icon>
									<view class="cell-left-wrapper">
										<view 
											v-if="isEditMode" 
											class="item-checkbox-wrap"
											@click.stop="toggleSelect(item.id)"
										>
											<van-checkbox 
												:model-value="selectedIds.includes(item.id)" 
												checked-color="#f59e0b"
												class="item-checkbox"
											/>
										</view>
										<view :class="['list-icon-wrap', item.iconBg]">
											<van-icon :name="item.icon" :color="item.iconColor" size="20" />
										</view>
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
							<template #right>
								<view class="delete-button" @click.stop="onDeleteItem(group.id, item.id)">
									<van-icon name="delete-o" size="24" color="#fff" />
								</view>
							</template>
						</van-swipe-cell>
					</view>
				</view>
				<!-- 空状态 -->
				<view v-if="currentYearDetails.length === 0" class="empty-state">
					<van-icon name="description" size="48" color="#cbd5e1" />
					<text class="empty-text">暂无账单数据</text>
				</view>
			</scroll-view>
		</view>
	</view>
</template>

<script setup>
import { ref, computed } from 'vue';
import CapsuleButton from '@/components/CapsuleButton/CapsuleButton.vue';

// 状态管理
const currentYear = ref(null);
const isEditMode = ref(false);
const selectedIds = ref([]);

// 虚拟数据 - 年度列表
const yearsList = ref([
	{ year: '2025', income: '45,200.00', expense: '26,510.00' },
	{ year: '2024', income: '128,400.00', expense: '98,320.00' },
	{ year: '2023', income: '110,000.00', expense: '88,150.00' }
]);

// 虚拟数据 - 详情数据 (按年份存储)
const yearDetailsMap = ref({
	'2025': [
		{
			id: 1,
			date: '12月31日 星期三',
			totalExpense: '16,246.00',
			items: [
				{
					id: 101,
					title: '育儿费用',
					amount: '-4,225.00',
					time: '14:20',
					location: '幼儿园生活区',
					icon: 'smile-o',
					iconBg: 'bg-amber-light',
					iconColor: '#d97706'
				},
				{
					id: 102,
					title: '办公租赁',
					amount: '-6,466.00',
					time: '10:30',
					location: '科技园园区',
					icon: 'shop-o',
					iconBg: 'bg-blue-light',
					iconColor: '#2563eb'
				},
				{
					id: 103,
					title: '交通保险',
					amount: '-5,555.00',
					time: '09:15',
					location: '私家车月度车险',
					icon: 'logistics',
					iconBg: 'bg-purple-light',
					iconColor: '#9333ea'
				}
			]
		},
		{
			id: 2,
			date: '12月30日 星期二',
			totalExpense: '5,225.00',
			items: [
				{
					id: 201,
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
	],
	'2024': [
		{
			id: 3,
			date: '12月15日 星期日',
			totalExpense: '2,000.00',
			items: [
				{
					id: 301,
					title: '餐饮美食',
					amount: '-2,000.00',
					time: '18:30',
					location: '海底捞火锅',
					icon: 'shop-o',
					iconBg: 'bg-rose-light',
					iconColor: '#f43f5e'
				}
			]
		}
	]
});

// 当前显示的详情列表
const currentYearDetails = computed(() => {
	if (!currentYear.value) return [];
	return yearDetailsMap.value[currentYear.value.year] || [];
});

// 计算全选状态
const isAllSelected = computed({
	get: () => {
		const allItemIds = [];
		currentYearDetails.value.forEach(group => {
			group.items.forEach(item => {
				allItemIds.push(item.id);
			});
		});
		return allItemIds.length > 0 && selectedIds.value.length === allItemIds.length;
	},
	set: (val) => {
		if (val) {
			const allItemIds = [];
			currentYearDetails.value.forEach(group => {
				group.items.forEach(item => {
					allItemIds.push(item.id);
				});
			});
			selectedIds.value = allItemIds;
		} else {
			selectedIds.value = [];
		}
	}
});

// 打开年份详情
const openYearDetail = (yearData) => {
	currentYear.value = yearData;
	isEditMode.value = false;
	selectedIds.value = [];
};

// 关闭年份详情
const closeYearDetail = () => {
	currentYear.value = null;
	isEditMode.value = false;
	selectedIds.value = [];
};

// 删除年份
const onDeleteYear = (index) => {
	uni.showModal({
		title: '提示',
		content: '确定要删除该年份的所有账单吗？',
		success: (res) => {
			if (res.confirm) {
				const year = yearsList.value[index].year;
				yearsList.value.splice(index, 1);
				delete yearDetailsMap.value[year];
				uni.showToast({ title: '删除成功', icon: 'success' });
			}
		}
	});
};

// 切换编辑模式
const toggleEditMode = () => {
	isEditMode.value = !isEditMode.value;
	if (!isEditMode.value) {
		selectedIds.value = [];
	}
};

// 切换选中项
const toggleSelect = (id) => {
	const index = selectedIds.value.indexOf(id);
	if (index > -1) {
		selectedIds.value.splice(index, 1);
	} else {
		selectedIds.value.push(id);
	}
};

// 全选/取消全选
const toggleSelectAll = () => {
	isAllSelected.value = !isAllSelected.value;
};

// 批量删除
const batchDelete = () => {
	if (selectedIds.value.length === 0) return;
	
	uni.showModal({
		title: '提示',
		content: `确定要删除选中的 ${selectedIds.value.length} 条记录吗？`,
		success: (res) => {
			if (res.confirm) {
				const yearKey = currentYear.value.year;
				const groups = yearDetailsMap.value[yearKey];
				
				// 过滤掉被选中的项
				const newGroups = groups.map(group => {
					return {
						...group,
						items: group.items.filter(item => !selectedIds.value.includes(item.id))
					};
				}).filter(group => group.items.length > 0); // 移除空组
				
				yearDetailsMap.value[yearKey] = newGroups;
				selectedIds.value = [];
				isEditMode.value = false;
				uni.showToast({ title: '删除成功', icon: 'success' });
			}
		}
	});
};

// 单条删除
const onDeleteItem = (groupId, itemId) => {
	uni.showModal({
		title: '提示',
		content: '确定要删除这条记录吗？',
		success: (res) => {
			if (res.confirm) {
				const yearKey = currentYear.value.year;
				const groups = yearDetailsMap.value[yearKey];
				const groupIndex = groups.findIndex(g => g.id === groupId);
				
				if (groupIndex > -1) {
					const group = groups[groupIndex];
					const itemIndex = group.items.findIndex(i => i.id === itemId);
					if (itemIndex > -1) {
						group.items.splice(itemIndex, 1);
						
						// 如果组为空，移除组
						if (group.items.length === 0) {
							groups.splice(groupIndex, 1);
						}
						
						uni.showToast({ title: '删除成功', icon: 'success' });
					}
				}
			}
		}
	});
};

// 点击条目 (非编辑模式下)
const onItemClick = (item) => {
	if (isEditMode.value) {
		toggleSelect(item.id);
	}
};
</script>

<style scoped>
.page-container {
	min-height: 100vh;
	background-color: #f8fafc;
	padding-bottom: 20px;
}

/* 年度列表样式 */
.year-list-container {
	padding: 20px;
}

.header-row {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 16px;
}

.section-title {
	font-size: 18px;
	font-weight: 700;
	color: #0f172a;
}

.year-swipe-cell {
	margin-bottom: 12px;
	border-radius: 12px;
	overflow: hidden;
}

.year-card {
	background-color: #fff;
	padding: 20px;
	display: flex;
	justify-content: space-between;
	align-items: center;
}

.year-card-left {
	display: flex;
	flex-direction: column;
}

.year-text {
	font-size: 20px;
	font-weight: 700;
	color: #0f172a;
	margin-bottom: 8px;
}

.year-stats {
	display: flex;
	gap: 12px;
}

.stat-text {
	font-size: 13px;
}

.stat-text.income {
	color: #ef4444;
}

.stat-text.expense {
	color: #10b981;
}

/* 详情页样式 */
.detail-container {
	height: 100vh;
	display: flex;
	flex-direction: column;
}

.detail-header {
	height: 44px;
	padding: 10px 16px 10px; /* 适配状态栏 */
	display: flex;
	justify-content: space-between;
	align-items: center;
	background-color: #fff;
	position: sticky;
	top: 0;
	z-index: 100;
	border-bottom: 1px solid #f1f5f9;
}

.header-left {
	display: flex;
	align-items: center;
	gap: 4px;
}

.header-title {
	font-size: 17px;
	font-weight: 600;
	color: #0f172a;
}

.action-text {
	font-size: 15px;
	color: #3b82f6;
	padding: 4px 8px;
}

.batch-action-bar {
	height: 50px;
	background-color: #fff;
	display: flex;
	justify-content: space-between;
	align-items: center;
	padding: 0 20px;
	border-bottom: 1px solid #f1f5f9;
}

.select-all {
	display: flex;
	align-items: center;
}

.delete-btn {
	color: #ef4444;
	font-size: 15px;
	font-weight: 500;
	transition: color 0.3s;
}

.delete-btn.disabled {
	color: #cbd5e1;
	pointer-events: none;
}

.bill-scroll-view {
	flex: 1;
	background-color: #f8fafc;
	padding-top: 10px;
}

/* 列表项样式 (复用 accounting_detail.vue 风格) */
.day-group {
	margin-bottom: 24px;
}

.day-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 12px;
	padding: 0 20px;
}

.day-date {
	font-size: 14px;
	font-weight: 700;
	color: #0f172a;
}

.text-style-desc {
	font-size: 12px;
	color: #64748b;
}

.custom-cell {
	background-color: #fff;
	padding: 16px 20px !important;
	border-bottom: 1px solid #f1f5f9;
}

.cell-left-wrapper {
	display: flex;
	align-items: center;
}

.item-checkbox {
	margin-right: 12px;
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
	flex: 1;
}

.cell-main {
	display: flex;
	flex-direction: column;
}

.text-style-title {
	font-size: 15px;
	font-weight: 600;
	color: #0f172a;
}

.cell-right {
	display: flex;
	flex-direction: column;
	align-items: flex-end;
}

.text-style-number {
	font-size: 16px;
	font-weight: 600;
	color: #0f172a;
}

/* 滑动删除按钮 */
.delete-button {
	height: 100%;
	width: 65px;
	background-color: #ee0a24;
	display: flex;
	justify-content: center;
	align-items: center;
}

/* 颜色类 */
.bg-amber-light { background-color: #fef3c7; }
.bg-blue-light { background-color: #dbeafe; }
.bg-purple-light { background-color: #f3e8ff; }
.bg-emerald-light { background-color: #d1fae5; }
.bg-rose-light { background-color: #ffe4e6; }

/* 空状态 */
.empty-state {
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	padding-top: 100px;
	gap: 16px;
}

.empty-text {
	color: #94a3b8;
	font-size: 14px;
}
</style>