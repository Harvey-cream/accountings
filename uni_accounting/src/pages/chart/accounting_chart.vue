<template>
	<view class="chart-container" :class="currentThemeClass">
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
		<scroll-view scroll-y class="scroll-view-content">
			<view class="header-section">
				<view class="total-display">
					<view class="display-row">
						<view class="display-group">
							<text class="display-label">总{{ currentType }}:</text>
							<text class="display-value ">{{ chartData.total }}</text>
						</view>
						<view class="display-group">
							<text class="display-label">均值:</text>
							<text class="display-value ">{{ chartData.average }}</text>
						</view>
					</view>
				</view>
			</view>

			<view class="content-body">
				<view class="trend-section">
					<!-- 简易 SVG 曲线图 -->
				<view class="line-chart-container" @touchstart="onTouchStart" @touchmove.stop.prevent="onTouchMove">
					<svg viewBox="0 0 300 150" class="line-chart-svg">
						<!-- 顶部封顶线 (动态贴合最高点) -->
						<line x1="10" :y1="maxPointY" x2="290" :y2="maxPointY" stroke="#e2e8f0" stroke-width="0.5" />
						<text :x="290" :y="maxPointY - 5" text-anchor="end" font-size="8" fill="#94a3b8" class="font-number">{{ maxValue.toFixed(2) }}</text>
						
						<!-- 底部基准线 -->
						<line x1="10" y1="130" x2="290" :y2="130" stroke="#e2e8f0" stroke-width="0.5" />
						
						<!-- 中间均分线 (极细虚线) -->
						<line x1="10" :y1="midLineY" x2="290" :y2="midLineY" stroke="#e2e8f0" stroke-width="0.5" stroke-dasharray="2,2" />
						
						<!-- 起伏线（垂线） -->
						<g v-for="(point, index) in chartPoints" :key="'line-' + index">
							<line :x1="point.x" :y1="point.y" :x2="point.x" :y2="130" stroke="#f1f5f9" stroke-width="0.5" />
						</g>
						
						<path :d="chartPath" fill="none" stroke="#0f172a" stroke-width="0.5" stroke-linecap="round" stroke-linejoin="round" />
						
						<!-- 所有数据点的触摸区域和高亮 -->
						<g v-for="(point, index) in chartPoints" :key="index" @click="selectPoint(index)">
							<!-- 触摸热区 (透明大圆) -->
							<circle :cx="point.x" :cy="point.y" r="12" fill="transparent" />
							<!-- 选中点的高亮效果 (实心) -->
							<circle v-if="selectedIndex === index" :cx="point.x" :cy="point.y" r="2.5" fill="#0f172a" />
							<!-- 未选中点的小圆点 (空心) -->
							<circle v-else :cx="point.x" :cy="point.y" r="2" fill="#fff" stroke="#0f172a" stroke-width="0.5" />
						</g>

						<!-- 浮动标签 (增加边界检测) -->
						<foreignObject v-if="selectedPoint" :x="tagX" :y="selectedPoint.y - 35" width="80" height="30">
							<div class="float-tag font-number" xmlns="http://www.w3.org/1999/xhtml">¥ {{ selectedPoint.value }}</div>
						</foreignObject>
					</svg>
					<view class="x-axis">
						<text 
							v-for="(label, index) in currentLabels" 
							:key="index" 
							:class="['font-number', { active: selectedIndex === index }]"
							:style="{ left: chartPoints[index] ? (chartPoints[index].x / 300 * 100 + '%') : '0', visibility: shouldShowLabel(index) ? 'visible' : 'hidden' }"
						>{{ label }}</text>
					</view>
				</view>
			</view>

			<!-- 支出明细列表 -->
			<view class="detail-section">
				<view class="section-header">
					<text class="section-title">{{ currentType }}排行榜</text>
					<text class="view-all">查看全部</text>
				</view>

				<view class="list-container">
					<van-cell v-for="item in expenseList" :key="item.id" center class="custom-cell flat-cell">
						<template #icon>
							<view class="list-icon-wrap" :style="{ backgroundColor: getIconColors(item.icon_id).bg }">
								<van-icon :name="item.icon" :color="getIconColors(item.icon_id).icon" size="20" />
							</view>
						</template>
						<template #title>
							<view class="cell-content">
								<view class="cell-main">
									<view class="title-row">
										<text class="text-style-title">{{ item.name }}</text>
										<text class="cell-percent text-style-desc">{{ item.percent }}%</text>
									</view>
									<view class="progress-bar-track">
										<view 
											class="progress-bar-fill" 
											:style="{ width: (item.displayPercent || 0) + '%', backgroundColor: getIconColors(item.icon_id).icon }"
										></view>
									</view>
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
import { ref, computed, getCurrentInstance, onMounted, watch } from 'vue';
import CustomTabbar from '@/components/Tabbar/Tabbar.vue';
import { getBillSummary } from '@/api/api.js';
import { colorPairs } from '@/utils/color.js';

const periods = ['周', '月', '年'];
const currentPeriod = ref(0);

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
};

// 图表数据
const chartData = ref({
	labels: [],
	values: [],
	total: '¥ 0.00',
	average: '¥ 0.00'
});

const expenseList = ref([]);

const currentLabels = computed(() => chartData.value.labels);
const currentValues = computed(() => chartData.value.values);

const getIconColors = (iconId) => {
	const colorIndex = Number(iconId) % colorPairs.length;
	return colorPairs[colorIndex];
};

const fetchChartData = async () => {
	try {
		const periodMap = { 0: 'week', 1: 'month', 2: 'year' };
		const params = {
			period: periodMap[currentPeriod.value],
			type: currentType.value === '支出' ? 'expense' : 'income'
		};
		const res = await getBillSummary(params);
		if (res.code === 0) {
			chartData.value = res.data.chartData;
			// 1. 初始化列表，将 displayPercent 设为 0
			expenseList.value = res.data.categoryStats.map(item => ({
				...item,
				displayPercent: 0
			}));
			
			// 2. 延迟触发动画效果
			setTimeout(() => {
				expenseList.value = expenseList.value.map(item => ({
					...item,
					displayPercent: item.percent
				}));
			}, 100);
		}
	} catch (e) {
		console.error('Failed to fetch chart data:', e);
	}
};

onMounted(() => {
	fetchChartData();
});

watch([currentPeriod, () => currentType.value], () => {
	selectedIndex.value = -1;
	fetchChartData();
});

// 图表常量与工具函数
const CHART = { width: 300, height: 150, paddingTop: 40, paddingBottom: 20, paddingX: 10 };

// 计算当前视图的最大值
const maxValue = computed(() => {
	const values = currentValues.value;
	if (!values || values.length === 0) return 0;
	return Math.max(...values);
});

// 计算中间均分线的高度
const midLineY = computed(() => {
	const availableHeight = CHART.height - CHART.paddingTop - CHART.paddingBottom;
	return CHART.height - CHART.paddingBottom - availableHeight / 2;
});

const selectedIndex = ref(-1); // 当前选中的索引，-1 表示未选中
let hideTimer = null; // 隐藏标签的定时器

// 自动隐藏逻辑
const startHideTimer = () => {
	if (hideTimer) clearTimeout(hideTimer);
	hideTimer = setTimeout(() => {
		selectedIndex.value = -1;
		hideTimer = null;
	}, 3000);
};

// 计算所有点的坐标
const chartPoints = computed(() => {
	const values = currentValues.value;
	if (!values || values.length === 0) return [];
	
	const width = 300;
	const height = 150; 
	const paddingX = 13; 
	const paddingTop = 40; // 为顶部标签留足空间
	const paddingBottom = 20; // 调整为 20，使得 150 - 20 = 130，与基准线完美重合
	const availableWidth = width - paddingX * 2;
	const availableHeight = height - paddingTop - paddingBottom;
	
	const min = 0; 
	const max = Math.max(...values) * 1.05;
	const range = max - min || 1; 
	
	return values.map((val, index) => {
		const x = paddingX + (index / (values.length - 1)) * availableWidth;
		const y = height - paddingBottom - ((val - min) / range) * availableHeight;
		return { x, y, value: val };
	});
});

// 当前选中的点
const selectedPoint = computed(() => {
	if (selectedIndex.value === -1 || !chartPoints.value[selectedIndex.value]) return null;
	return chartPoints.value[selectedIndex.value];
});

// 计算浮动标签的 X 坐标，防止超出屏幕
const tagX = computed(() => {
	if (!selectedPoint.value) return 0;
	let x = selectedPoint.value.x - 40; // 默认居中 (标签宽80)
	const minX = 5; // 左边距
	const maxX = 300 - 80 - 5; // 右边距 (容器宽300 - 标签宽80 - 边距5)
	
	if (x < minX) x = minX;
	if (x > maxX) x = maxX;
	return x;
});

// 计算最高点的 Y 坐标，用于顶部封顶线
const maxPointY = computed(() => {
	if (!chartPoints.value.length) return 15;
	return Math.min(...chartPoints.value.map(p => p.y));
});

// 点击选择点
const selectPoint = (index) => {
	selectedIndex.value = index;
	startHideTimer();
};

// 触摸交互逻辑
const instance = getCurrentInstance();
const chartRect = ref(null);

const updateChartRect = () => {
	const query = uni.createSelectorQuery().in(instance);
	query.select('.line-chart-container').boundingClientRect(data => {
		if (data) {
			chartRect.value = data;
		}
	}).exec();
};

const onTouchStart = (e) => {
	updateChartRect();
	handleTouch(e);
};

const onTouchMove = (e) => {
	handleTouch(e);
};

const handleTouch = (e) => {
	// 如果没有获取到容器尺寸或没有数据点，直接返回
	if (!chartRect.value || !chartPoints.value.length) return;
	
	const touch = e.touches[0];
	const clientX = touch.clientX;
	
	// 计算相对于容器的 X 坐标
	let relativeX = clientX - chartRect.value.left;
	
	// 限制范围
	if (relativeX < 0) relativeX = 0;
	if (relativeX > chartRect.value.width) relativeX = chartRect.value.width;
	
	// 计算比例
	const percent = relativeX / chartRect.value.width;
	
	// 计算最近的索引
	const count = chartPoints.value.length;
	let index = Math.round(percent * (count - 1));
	
	if (index < 0) index = 0;
	if (index >= count) index = count - 1;
	
	selectedIndex.value = index;
	startHideTimer();
};

// 生成折线路径（直线连接）
const chartPath = computed(() => {
	const points = chartPoints.value;
	if (points.length < 2) return '';
	
	let d = `M ${points[0].x},${points[0].y}`;
	for (let i = 1; i < points.length; i++) {
		d += ` L ${points[i].x},${points[i].y}`;
	}
	return d;
});

// 控制标签显示的逻辑
const shouldShowLabel = (index) => {
	const total = currentValues.value.length;
	// 年视图 (12个点): 显示 1, 4, 7, 10, 12月 (对应索引 0, 3, 6, 9, 11)
	if (currentPeriod.value === 2) {
		return [0, 3, 6, 9, 11].includes(index);
	}
	// 月视图 (30个点): 显示 1, 10, 20, 30号 (对应索引 0, 9, 19, 29)
	if (currentPeriod.value === 1) {
		return [0, 9, 19, 29].includes(index);
	}
	// 周视图 (7个点): 显示首尾和中间 (0, 3, 6)
	if (currentPeriod.value === 0) {
		return [0, 3, 6].includes(index);
	}
	return false;
};
</script>

<style scoped>
.chart-container {
	height: 100vh;
	display: flex;
	flex-direction: column;
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
	gap: 10px; 
	margin-bottom: 8px;
}

/* 滚动区域调整 */
.scroll-view-content {
	flex: 1;
	overflow-y: auto;
	padding-bottom: 50px;
}

/* 顶部展示区域 (随页面滑动的部分) */
.header-section {
	padding: 0 0 70px;
}

.type-selector {
	display: flex;
	align-items: center;
	justify-content: center;
	gap: 4px;
	padding: 1px;
}

.type-text {
	font-size: var(--font-size-number);
	font-weight: 700;
}

.segment-control {
	background-color: rgba(255, 255, 255, 0.3);
	border-radius: 20px;
	padding: 2px; 
	display: flex;
	box-sizing: border-box;
	width: 100%; 
}

.segment-item {
	flex: 1; 
	text-align: center; 
	padding: 4px 0;
	border-radius: 16px;
	font-size: var(--font-size-sm);
	font-weight: 500;
}

.segment-item.active {
	background-color: #ffffff;
	font-weight: 700;
}

.total-display {
	display: flex;
	flex-direction: column;
	gap: 8px;
	padding: 10px 20px;
}

.display-row {
	display: flex;
	align-items: center;
	justify-content: space-between;
}

.display-group {
	display: flex;
	align-items: center;
	gap: 4px;
}

.display-label,
.display-value {
	font-size: var(--font-size-number);
	font-weight: 300;
	color: rgba(0, 0, 0, 0.6);
}

/* 内容区域 */
.content-body {
	padding: 0;
	margin-top: -130px;
}

.card-title {
	font-size: 16px;
	font-weight: 700;
}

.card-subtitle,
.view-all {
	font-size: 12px;
	color: var(--light-text-color);
}

/* 趋势图样式 */
.trend-subtitle {
	margin-top: 4px;
}

.trend-text {
	font-size: 12px;
	color: var(--light-text-color);
}

.line-chart-container {
	height: 220px;
	position: relative;
}

.line-chart-svg {
	width: 100%;
	height: 100%;
}

.float-tag {
	background-color: var(--primary-text-color);
	color: #fff;
	border-radius: 12px;
	font-size: var(--font-size-xs);
	text-align: center;
	line-height: 24px;
	padding: 0 8px;
}

.x-axis {
	position: absolute;
	bottom: 10px;
	left: 0;
	width: 100%;
	height: 20px;
}

.x-axis text {
	position: absolute;
	font-size: var(--font-size-xs);
	color: #cbd5e1;
	transform: translateX(-50%);
	white-space: nowrap;
	transition: color 0.3s;
}

.x-axis text.active {
	color: var(--primary-text-color);
	font-weight: 700;
	visibility: visible !important;
}

/* 列表样式 */
.section-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 16px;
	padding: 0 20px;
}

.section-title {
	font-size: var(--font-size-number);
	color: var(--secondary-text-color);
}

.custom-cell {
	background-color: transparent;
	border-radius: 0;
	margin-bottom: 0;
	padding: 16px 20px !important;
	border-bottom: 1px solid #f1f5f9;
}

.custom-cell:last-child {
	border-bottom: none;
}

.flat-cell {
	background-color: transparent !important;
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
	flex: 1;
	display: flex;
	flex-direction: column;
	margin-right: 16px;
}

.title-row {
	display: flex;
	align-items: center;
	justify-content: space-between;
	margin-bottom: 6px;
}

.cell-percent {
	font-size: var(--font-size-desc);
	color: var(--light-text-color);
}

.progress-bar-track {
	height: 6px;
	background-color: #f1f5f9;
	border-radius: 3px;
	overflow: hidden;
	width: 100%;
}

.progress-bar-fill {
	height: 100%;
	border-radius: 3px;
	transition: width 0.6s ease;
}

.cell-right {
	display: flex;
	flex-direction: column;
	align-items: flex-end;
	min-width: 80px;
}
/* 颜色类 */
.bg-orange-light, .bg-blue-light, .bg-green-light, .bg-red-light, .bg-indigo-light, .bg-yellow-light, .bg-cyan-light {
	background-color: var(--secondary-bg-color);
}
</style>
