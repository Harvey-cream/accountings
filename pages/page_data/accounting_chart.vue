<template>
	<view class="chart-container">
		<!-- 顶部固定导航区域 -->
		<view class="fixed-nav-container">
			<view class="nav-header">
				<!-- 支出/收入下拉选择器 -->
				<view class="type-selector" @click="showTypeSheet = true">
					<text class="type-text">{{ currentType }}</text>
					<van-icon name="arrow-down" size="12" color="#0f172a" />
				</view>
				<view class="segment-control">
					<text v-for="(item, index) in periods" :key="index" :class="['segment-item', { active: currentPeriod === index }]" @click="currentPeriod = index">{{ item }}</text>
				</view>
			</view>
		</view>

		<!-- 可滚动的区域 -->
		<scroll-view scroll-y class="scroll-view-content">
			<!-- 顶部展示区域 -->
			<view class="header-section">
				<view class="total-display">
					<text class="total-label">总支出 (12月)</text>
					<text class="total-amount">¥ 265,211.00</text>
					<view class="avg-badge">
						<text class="avg-text">日均支出: ¥ 8,555</text>
					</view>
				</view>
			</view>

			<!-- 内容区域 -->
			<view class="content-body">
			<!-- 支出分类卡片 -->
			<view class="card category-card">
				<view class="card-header">
					<text class="card-title">支出分类</text>
					<text class="card-subtitle">前五名</text>
				</view>

				<view class="chart-row">
					<!-- 模拟环形图 -->
					<view class="donut-chart">
						<view class="donut-center">
							<text class="donut-label">总支出</text>
							<text class="donut-value">100%</text>
						</view>
					</view>

					<!-- 图例列表 -->
					<view class="legend-list">
						<view v-for="(item, index) in categories" :key="index" class="legend-item">
							<view class="legend-info">
								<view :class="['dot', item.colorClass]"></view>
								<text class="legend-name">{{ item.name }}</text>
							</view>
							<text class="legend-percent">{{ item.percent }}%</text>
						</view>
					</view>
				</view>
			</view>

			<!-- 趋势卡片 -->
			<view class="card trend-card">
				<view class="card-header">
					<view>
						<text class="card-title">周趋势</text>
						<view class="trend-subtitle">
							<text class="trend-text">较上周增长 12%</text>
						</view>
					</view>
					<view class="trend-dots">
						<view class="dot-indicator active"></view>
						<view class="dot-indicator"></view>
					</view>
				</view>

				<!-- 简易 SVG 曲线图 -->
				<view class="line-chart-container">
					<svg viewBox="0 0 300 100" class="line-chart-svg">
						<path d="M0,80 Q50,60 100,80 T200,50 T300,80" fill="none" stroke="#FFD541" stroke-width="3" />
						<circle cx="200" cy="50" r="4" fill="#0f172a" />
						<!-- 浮动标签 -->
						<foreignObject x="160" y="10" width="80" height="30">
							<div class="float-tag" xmlns="http://www.w3.org/1999/xhtml">¥ 12,400</div>
						</foreignObject>
					</svg>
					<view class="x-axis">
						<text v-for="day in weekDays" :key="day">{{ day }}</text>
					</view>
				</view>
			</view>

			<!-- 支出明细列表 -->
			<view class="detail-section">
				<view class="section-header">
					<text class="section-title">支出明细</text>
					<text class="view-all">查看全部</text>
				</view>

				<view class="list-container">
					<van-cell v-for="item in expenseList" :key="item.id" center class="custom-cell">
						<template #icon>
							<view :class="['list-icon-wrap', item.bgClass]">
								<van-icon :name="item.icon" :color="item.iconColor" size="20" />
							</view>
						</template>
						<template #title>
							<view class="cell-content">
								<view class="cell-main">
									<text class="cell-title">{{ item.name }}</text>
									<text class="cell-time">{{ item.time }}</text>
								</view>
								<view class="cell-right">
									<text class="cell-amount">{{ item.amount }}</text>
									<text class="cell-percent">{{ item.percent }}%</text>
								</view>
							</view>
						</template>
					</van-cell>
				</view>
			</view></view>
		</scroll-view>

		<!-- 选择类型弹窗 (放在外层不影响布局) -->
		<van-action-sheet
			:show="showTypeSheet"
			:actions="typeActions"
			@close="showTypeSheet = false"
			@select="onTypeSelect"
		/>

		<custom-tabbar />
	</view>
</template>

<script setup>
import { ref } from 'vue';
import CustomTabbar from '@/components/Tabbar/Tabbar.vue';

const periods = ['日', '周', '月'];
const currentPeriod = ref(2);
const weekDays = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'];

// 类型选择逻辑
const currentType = ref('支出');
const showTypeSheet = ref(false);
const typeActions = [
	{ name: '支出' },
	{ name: '收入' }
];

const onTypeSelect = (event) => {
	currentType.value = event.name;
	showTypeSheet.value = false;
	// 这里可以根据类型切换数据
};

const categories = ref([
	{ name: '住房', percent: 40, colorClass: 'bg-blue' },
	{ name: '餐饮', percent: 30, colorClass: 'bg-orange' },
	{ name: '购物', percent: 20, colorClass: 'bg-yellow' },
	{ name: '其他', percent: 10, colorClass: 'bg-gray' }
]);

const expenseList = ref([
	{ id: 1, name: '餐饮美食', time: '今天, 12:45 PM', amount: '-¥ 42,255.00', percent: 30, icon: 'fire-o', iconColor: '#d97706', bgClass: 'bg-orange-light' },
	{ id: 2, name: '房屋租金', time: '12月1日, 09:00 AM', amount: '-¥ 64,662.00', percent: 40, icon: 'wap-home-o', iconColor: '#2563eb', bgClass: 'bg-blue-light' }
]);
</script>

<style scoped>
.chart-container {
	height: 100vh;
	display: flex;
	flex-direction: column;
	background-color: #f7f8fa;
	overflow: hidden;
}

/* 顶部固定导航 */
.fixed-nav-container {
	background-color: #ffd541;
	padding: 10px 20px 0;
	box-sizing: border-box;
	flex-shrink: 0;
}

.nav-header {
	display: flex;
	flex-direction: column;
	gap: 16px;
	margin-bottom: 10px;
}

/* 滚动区域调整 */
.scroll-view-content {
	flex: 1;
	overflow-y: auto;
}

/* 顶部展示区域 (随页面滑动的部分) */
.header-section {
	background-color: #ffd541;
	padding: 0 20px 70px;
	border-bottom-left-radius: 30px;
	border-bottom-right-radius: 30px;
}

.type-selector {
	display: flex;
	align-items: center;
	justify-content: center;
	gap: 4px;
	padding: 8px 10px;
}

.type-text {
	font-size: 14px;
	font-weight: 700;
	color: #0f172a;
}

.segment-control {
	background-color: rgba(255, 255, 255, 0.3);
	border-radius: 20px;
	padding: 4px;
	display: flex;
	box-sizing: border-box;
	width: 100%; 
}

.segment-item {
	flex: 1; 
	text-align: center; 
	padding: 6px 0; 
	border-radius: 16px;
	font-size: 14px;
	color: #0f172a;
	font-weight: 500;
}

.segment-item.active {
	background-color: #ffffff;
	font-weight: 700;
}

.total-display {
	text-align: center;
}

.total-label {
	font-size: 12px;
	color: rgba(0, 0, 0, 0.6);
	margin-bottom: 8px;
	display: block;
}

.total-amount {
	font-size: 32px;
	font-weight: 800;
	color: #0f172a;
	margin-bottom: 12px;
	display: block;
}

.avg-badge {
	display: inline-block;
	background-color: rgba(255, 255, 255, 0.3);
	padding: 4px 12px;
	border-radius: 12px;
}

.avg-text {
	font-size: 12px;
	color: #0f172a;
	font-weight: 600;
}

/* 内容区域 */
.content-body {
	padding: 0 20px;
	margin-top: -60px; /* 卡片上浮 */
}

.card {
	background-color: #ffffff;
	border-radius: 24px;
	padding: 20px;
	margin-bottom: 20px;
	box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
}

.card-header {
	display: flex;
	justify-content: space-between;
	align-items: flex-start;
	margin-bottom: 20px;
}

.card-title {
	font-size: 16px;
	font-weight: 700;
	color: #0f172a;
}

.card-subtitle,
.view-all {
	font-size: 12px;
	color: #94a3b8;
}

/* 环形图样式 */
.chart-row {
	display: flex;
	align-items: center;
	justify-content: space-around;
}

.donut-chart {
	width: 120px;
	height: 120px;
	border-radius: 50%;
	/* 使用 conic-gradient 模拟环形图: 蓝色40%, 橙色30%, 黄色20%, 灰色10% */
	background: conic-gradient(#3b82f6 0% 40%, #f97316 40% 70%, #facc15 70% 90%, #e2e8f0 90% 100%);
	display: flex;
	align-items: center;
	justify-content: center;
	position: relative;
}

.donut-chart::before {
	content: '';
	position: absolute;
	width: 90px;
	height: 90px;
	background-color: #ffffff;
	border-radius: 50%;
}

.donut-center {
	position: relative;
	text-align: center;
	z-index: 1;
}

.donut-label {
	font-size: 10px;
	color: #94a3b8;
	display: block;
}

.donut-value {
	font-size: 16px;
	font-weight: 700;
	color: #0f172a;
}

.legend-list {
	display: flex;
	flex-direction: column;
	gap: 12px;
}

.legend-item {
	display: flex;
	justify-content: space-between;
	align-items: center;
	width: 120px;
}

.legend-info {
	display: flex;
	align-items: center;
	gap: 8px;
}

.dot {
	width: 8px;
	height: 8px;
	border-radius: 50%;
}

.legend-name {
	font-size: 12px;
	color: #64748b;
}

.legend-percent {
	font-size: 12px;
	font-weight: 600;
	color: #0f172a;
}

/* 趋势图样式 */
.trend-subtitle {
	margin-top: 4px;
}

.trend-text {
	font-size: 12px;
	color: #94a3b8;
}

.line-chart-container {
	height: 140px;
	position: relative;
}

.line-chart-svg {
	width: 100%;
	height: 100%;
}

.float-tag {
	background-color: #0f172a;
	color: #fff;
	border-radius: 12px;
	font-size: 10px;
	text-align: center;
	line-height: 24px;
	padding: 0 8px;
}

.x-axis {
	display: flex;
	justify-content: space-between;
	padding: 0 10px;
	margin-top: -20px;
}

.x-axis text {
	font-size: 10px;
	color: #cbd5e1;
}

/* 列表样式 */
.section-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 16px;
}

.section-title {
	font-size: 14px;
	font-weight: 600;
	color: #64748b;
}

.custom-cell {
	background-color: #ffffff;
	border-radius: 16px;
	margin-bottom: 12px;
	padding: 16px !important;
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
	width: 100%;
}

.cell-main {
	display: flex;
	flex-direction: column;
}

.cell-title {
	font-size: 14px;
	font-weight: 700;
	color: #0f172a;
}

.cell-time {
	font-size: 11px;
	color: #94a3b8;
	margin-top: 2px;
}

.cell-right {
	display: flex;
	flex-direction: column;
	align-items: flex-end;
}

.cell-amount {
	font-size: 14px;
	font-weight: 700;
	color: #0f172a;
}

.cell-percent {
	font-size: 11px;
	color: #94a3b8;
}

/* 颜色类 */
.bg-blue {
	background-color: #3b82f6;
}
.bg-orange {
	background-color: #f97316;
}
.bg-yellow {
	background-color: #facc15;
}
.bg-gray {
	background-color: #e2e8f0;
}

.bg-orange-light {
	background-color: #fff7ed;
}
.bg-blue-light {
	background-color: #eff6ff;
}
</style>
