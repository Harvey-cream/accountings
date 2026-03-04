<template>
	<view class="page-container" :class="currentThemeClass">
		<!-- 顶部导航栏 -->
		<view class="nav-header" :style="{ paddingTop: statusBarHeight + 'px' }">
			<view class="nav-content">
				<view class="nav-left"></view>
				<text class="nav-title">资产管理</text>
				<view class="nav-right">
					<CapsuleButton />
				</view>
			</view>
		</view>

		<scroll-view scroll-y class="main-content">
			<!-- 顶部资产卡片 -->
			<view class="asset-header">
				<view class="total-asset-card">
					<!-- 背景装饰图标 -->
					<view class="card-bg-icon">
						<van-icon name="gold-coin" size="120" color="rgba(0, 0, 0, 0.05)" />
					</view>
					<!-- 资产可视化图表 (条形图) -->
					<view class="chart-container">
						<view class="chart-title-row">
							<text class="chart-main-label">净资产</text>
							<text class="chart-main-value font-number">{{ netAsset }}</text>
						</view>

						<!-- 总资产 Bar -->
						<view class="chart-row">
							<view class="chart-label-group">
								<text class="label-text">总资产</text>
								<text class="value-text text-success font-number">{{ totalAsset }}</text>
							</view>
							<view class="progress-bar-track">
								<view 
									class="progress-bar-fill bg-green" 
									:style="{ width: displayAssetPercent + '%' }"
								></view>
							</view>
						</view>

						<!-- 负债 Bar -->
						<view class="chart-row mt-15">
							<view class="chart-label-group">
								<text class="label-text">负债</text>
								<text class="value-text text-danger font-number">{{ totalLiability }}</text>
							</view>
							<view class="progress-bar-track">
								<view 
									class="progress-bar-fill bg-red" 
									:style="{ width: displayLiabilityPercent + '%' }"
								></view>
							</view>
						</view>
					</view>
				</view>
			</view>
			<view class="list-content">
				<view v-for="(group, index) in assetGroups" :key="index" class="asset-group">
					<view class="group-header">
						<text class="group-title">{{ group.name }}</text>
						<text class="group-total text-style-number">{{ group.total }}</text>
					</view>
					
					<view class="group-list">
						<van-cell v-for="item in group.items" :key="item.id" center class="custom-cell flat-cell">
							<template #icon>
								<view :class="['list-icon-wrap', item.bgClass]">
									<van-icon :name="item.icon" :color="item.iconColor" size="20" />
								</view>
							</template>
							<template #title>
								<view class="cell-content">
									<view class="cell-main">
										<text class="text-style-title">{{ item.name }}</text>
									</view>
									<view class="cell-right">
										<text class="text-style-number">{{ item.amount }}</text>
									</view>
								</view>
							</template>
						</van-cell>
					</view>
				</view>
			</view>
		</scroll-view>

		<!-- 底部添加按钮 -->
		<view class="footer-action">
			<view class="add-btn" @click="goToAdd">
				<van-icon name="plus" color="#0f172a" size="16" />
				<text class="add-text-asset">添加账户</text>
			</view>
		</view>
	</view>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { onShow } from '@dcloudio/uni-app';
import CapsuleButton from '@/components/CapsuleButton/CapsuleButton.vue';
import { getAssetList } from '@/api/api.js';

const statusBarHeight = ref(20);

onMounted(() => {
	const sysInfo = uni.getSystemInfoSync();
	statusBarHeight.value = sysInfo.statusBarHeight || 20;
});

const netAsset = ref('0.00');
const totalAsset = ref('0.00');
const totalLiability = ref('0.00');

// Animation Refs
const displayAssetPercent = ref(0);
const displayLiabilityPercent = ref(0);

const assetGroups = ref([]);

const fetchAssetData = async () => {
	try {
		const res = await getAssetList();
		if (res.code === 0) {
			const { groups, summary } = res.data;
			assetGroups.value = groups;
			netAsset.value = summary.net_asset;
			totalAsset.value = summary.total_asset;
			totalLiability.value = summary.total_debt;
			
			// 更新进度条百分比
			updatePercents();
		}
	} catch (e) {
		console.error('获取资产列表失败:', e);
	}
};

const updatePercents = () => {
	const asset = parseFloat(totalAsset.value);
	const liability = Math.abs(parseFloat(totalLiability.value));
	const max = Math.max(asset, liability);
	
	if (max === 0) {
		displayAssetPercent.value = 0;
		displayLiabilityPercent.value = 0;
	} else {
		displayAssetPercent.value = (asset / max) * 100;
		displayLiabilityPercent.value = (liability / max) * 100;
	}
};

onShow(() => {
	fetchAssetData();
});

const goBack = () => {
	uni.navigateBack();
};

const goToAdd = () => {
	uni.navigateTo({
		url: '/pages/page_home/page_asset/asset_add'
	});
};
</script>

<style scoped>
.page-container {
	min-height: 100vh;
	background-color: #ffffff;
	display: flex;
	flex-direction: column;
}

/* 导航栏 */
.nav-header {
	z-index: 100;
	background-color: #fcd34d; 
}

.nav-content {
	height: 34px;
	display: flex;
	align-items: center;
	justify-content: space-between;
	padding: 0 16px;
}

.nav-left, .nav-right {
	width: 80px;
	display: flex;
	align-items: center;
	padding-bottom: 15px;
}

.nav-right {
	justify-content: flex-end;
}

.nav-title {
	font-size: 17px;
	font-weight: 600;
	color: #0f172a;
	padding-bottom: 15px;
}

/* 顶部 Header */
.asset-header {
	padding: 10px 10px 10px;
	display: flex;
	flex-direction: column;
}
.total-asset-card {
	background: transparent;
	border-radius: 15px;
	padding: 15px 20px;
	position: relative;
	overflow: hidden;
	box-shadow: 1px 1px 3px 2px rgba(0, 0, 0, 0.1); 
}



/* 背景装饰图标 */
.card-bg-icon {
	position: absolute;
	right: -20px;
	bottom: -30px;
	z-index: 0;
	transform: rotate(-15deg);
}
.chart-container {
    width: 100%;
	position: relative;
	z-index: 1;
}

.chart-title-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 24px;
}

.chart-main-label {
    font-size: 14px;
    color: #64748b; /* 更深的灰色 */
	font-weight: 500;
}

.chart-main-value {
    font-size: 22px; /* 稍微调小 */
    font-weight: 700; /* 稍微降低粗细 */
    color: #0f172a; /* 更深的颜色 */
}

.chart-row {
    width: 100%;
}
.mt-15 { margin-top: 20px; }

.chart-label-group {
    display: flex;
    justify-content: space-between;
    margin-bottom: 8px;
}

.label-text {
    font-size: 13px;
    color: #64748b; /* 更深的灰色 */
}

.value-text {
    font-size: 14px; /* 稍微调小 */
    font-weight: 600;
	color: #0f172a;
}
.text-success { color: #065f46 !important; } 
.text-danger { color: #991b1b !important; } 

.progress-bar-track {
    height: 8px;
    background-color: rgba(255, 255, 255, 0.3);
    border-radius: 4px;
    overflow: hidden;
}

.progress-bar-fill {
    height: 100%;
    border-radius: 4px;
    transition: width 1s cubic-bezier(0.34, 1.56, 0.64, 1);
}


/* 列表区域 */
.main-content {
	flex: 1;
	overflow-y: auto;
}

.list-content {
	padding: 15px 0 80px; /* 底部留出按钮空间 */
}

.asset-group {
	margin-bottom: 5px;
}

.group-header {
	padding: 0 20px 5px;
	display: flex;
	justify-content: space-between;
	align-items: center;
}

.group-title {
	font-size: 14px;
	color: #64748b;
}

.group-total {
	font-size: 14px;
	color: #94a3b8;
}

.custom-cell {
	padding: 15px 25px !important;
}

.list-icon-wrap {
	width: 30px;
	height: 30px;
	border-radius: 50%; /* 圆形图标背景 */
	display: flex;
	align-items: center;
	justify-content: center;
	margin-right: 12px;
}

/* 图标背景色已移动到 common.css */

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

.cell-right {
	font-weight: bold;
	color: #0f172a;
}

/* 底部按钮 */
.footer-action {
	position: fixed;
	bottom: 0;
	left: 0;
	right: 0;
	background-color: #fff;
	padding: 14px 16px 20px; /* 适配底部安全区 */
	box-shadow: 0 -4px 16px rgba(0, 0, 0, 0.05);
	z-index: 10;
}

.add-btn {
	background-color: #fff;
	height: 20px;
	display: flex;
	justify-content: center;
	align-items: center;
	gap: 8px;
}

.add-text-asset {
	font-size: 16px;
	font-weight: 600;
	color: #0f172a;
}
</style>