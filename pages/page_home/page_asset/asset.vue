<template>
	<view class="asset-container">
		<!-- 顶部资产卡片 -->
		<view class="asset-header">
			<view class="total-asset-card">
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

		<!-- 资产列表 -->
		<scroll-view scroll-y class="asset-list-scroll">
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
				<van-icon name="plus" color="#333" />
				<text>添加账户</text>
			</view>
		</view>
	</view>
</template>

<script setup>
import { ref, onMounted } from 'vue';

const netAsset = ref('611.00');
const totalAsset = ref('1111.00');
const totalLiability = ref('500.00');

// Animation Refs
const displayAssetPercent = ref(0);
const displayLiabilityPercent = ref(0);

const assetGroups = ref([
	{
		name: '现金',
		total: '1.00',
		items: [
			{ id: 1, name: '现金', amount: '1.00', icon: 'gold-coin', iconColor: '#fff', bgClass: 'bg-green' }
		]
	},
	{
		name: '储蓄卡',
		total: '555.00',
		items: [
			{ id: 2, name: '建设银行', amount: '555.00', icon: 'card', iconColor: '#fff', bgClass: 'bg-blue' }
		]
	},
	{
		name: '虚拟账户',
		total: '555.00',
		items: [
			{ id: 3, name: '微信', amount: '555.00', icon: 'wechat', iconColor: '#fff', bgClass: 'bg-green-dark' }
		]
	},
	{
		name: '负债',
		total: '-500.00',
		items: [
			{ id: 4, name: '哈哈', amount: '-500.00', icon: 'info', iconColor: '#fff', bgClass: 'bg-red' }
		]
	}
]);

const calculatePercents = () => {
  const asset = parseFloat(totalAsset.value);
  const liability = Math.abs(parseFloat(totalLiability.value));
  const max = Math.max(asset, liability);
  
  if (max === 0) return { asset: 0, liability: 0 };
  return {
    asset: (asset / max) * 100,
    liability: (liability / max) * 100
  };
};

onMounted(() => {
	setTimeout(() => {
		const { asset, liability } = calculatePercents();
		displayAssetPercent.value = asset;
		displayLiabilityPercent.value = liability;
	}, 100);
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
.asset-container {
	height: 100vh;
	display: flex;
	flex-direction: column;
	background-color: #ffff;
}

/* 顶部 Header */
.asset-header {
	padding: 5px 20px 20px; /* 适配状态栏 */
	display: flex;
	flex-direction: column;
	gap: 10px;
}
.total-asset-card {
	display: flex;
	flex-direction: column;
}

/* Chart Styles */
.chart-container {
    width: 100%;
    margin-top: 10px;
}

.chart-title-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
}

.chart-main-label {
    font-size: 14px;
    color: rgba(0,0,0,0.6);
}

.chart-main-value {
    font-size: 18px;
    font-weight: bold;
    color: #0f172a;
}

.chart-row {
    width: 100%;
}
.mt-15 { margin-top: 15px; }

.chart-label-group {
    display: flex;
    justify-content: space-between;
    margin-bottom: 6px;
}

.label-text {
    font-size: 12px;
    color: rgba(0,0,0,0.6);
}

.value-text {
    font-size: 14px;
    font-weight: bold;
}
.text-success { color: #10b981; } /* Green usually stands out well */
.text-danger { color: #ef4444; }

.progress-bar-track {
    height: 6px;
    background-color: rgba(255,255,255,0.5); /* Semi-transparent white for track on yellow bg */
    border-radius: 3px;
    overflow: hidden;
}

.progress-bar-fill {
    height: 100%;
    border-radius: 3px;
    transition: width 1s ease-out;
}
.bg-green { background-color: #10b981; }
.bg-red { background-color: #ef4444; }


/* 列表区域 */
.asset-list-scroll {
	flex: 1;
	overflow-y: auto;
	border-top: 1px solid #f1f5f9;
}

.list-content {
	padding: 20px 0 80px; /* 底部留出按钮空间 */
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

/* 复用 accounting_chart.vue 的 cell 样式 */
.custom-cell {
	background-color: #fff !important;
	padding: 15px 20px !important;
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

/* 图标背景色 */
.bg-green { background-color: #10b981; }
.bg-blue { background-color: #3b82f6; }
.bg-green-dark { background-color: #059669; }
.bg-red { background-color: #ef4444; }

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
	padding: 20px 20px 20px; /* 底部留出空间 */
}

.add-btn {
	background-color: #f1f5f9;
	height: 50px;
	display: flex;
	align-items: center;
    border-radius: 12px;
	justify-content: center;
	gap: 8px;
	box-shadow: 0 8px 16px -4px rgba(0, 0, 0, 0.15), 0 4px 6px -2px rgba(0, 0, 0, 0.1);
	border: 1px solid #f1f5f9;
	font-size: 16px;
	font-weight: 500;
	color: #333;
	transition: transform 0.2s ease, box-shadow 0.2s ease;
}

</style>