<template>
	<view class="medal-page" :class="currentThemeClass">
		<!-- 导航栏 -->
		<view class="nav-header">
			<view class="nav-left" @click="goBack">
				<van-icon name="arrow-left" size="20" color="#333" />
			</view>
			<text class="nav-title">我的勋章</text>
			<view class="nav-right"></view>
		</view>

		<!-- 统计总览 -->
		<view class="summary-card">
			<view class="summary-info">
				<text class="total-label">已解锁勋章</text>
				<text class="total-count">{{ unlockedCount }}</text>
			</view>
			<view class="summary-icon">
				<van-icon name="medal-o" size="48" color="#ffd541" />
			</view>
		</view>

		<!-- 勋章列表 -->
		<view class="medal-sections">
			<view v-for="(category, catIndex) in medalCategories" :key="catIndex" class="category-section">
				<view class="category-header">
					<text class="category-title">{{ category.title }}</text>
					<text class="category-progress">已获 {{ category.items.filter(m => m.unlocked).length }}/{{ category.items.length }}</text>
				</view>
				
				<view class="medal-grid">
					<view 
						v-for="(medal, medalIndex) in category.items" 
						:key="medalIndex" 
						class="medal-item"
						:class="{ 'unlocked': medal.unlocked }"
						@click="showMedalDetail(medal)"
					>
						<view class="medal-icon-wrapper">
							<van-icon :name="medal.icon" size="28" :color="medal.unlocked ? '#fff' : '#94a3b8'" />
						</view>
						<text class="medal-name">{{ medal.name }}</text>
						<text class="medal-desc" v-if="medal.unlocked">{{ medal.description }}</text>
						<text class="medal-desc locked-text" v-else>未获得</text>
					</view>
				</view>
			</view>
		</view>

		<!-- 详情弹窗 (模拟) -->
		<!-- 实际可以使用 van-popup 或 uni.showModal -->
	</view>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { getMedalList } from '@/api/api.js';

const goBack = () => {
	uni.navigateBack();
};

const medalCategories = ref([]);

const fetchMedals = async () => {
	try {
		const res = await getMedalList();
		if (res.code === 0) {
			medalCategories.value = res.data;
		}
	} catch (e) {
		console.error('获取勋章失败:', e);
	}
};

onMounted(() => {
	fetchMedals();
});

// 计算已解锁总数
const unlockedCount = computed(() => {
	let count = 0;
	medalCategories.value.forEach(cat => {
		count += cat.items.filter(m => m.unlocked).length;
	});
	return count;
});

const showMedalDetail = (medal) => {
	const title = medal.unlocked ? `恭喜获得【${medal.name}】` : `未获得【${medal.name}】`;
	let content = medal.unlocked ? medal.description : `解锁条件：${medal.description}`;
	
	// 如果未解锁且有进度数据，显示具体进度
	if (!medal.unlocked && medal.progress) {
		content += `\n当前进度：${medal.progress.current}/${medal.progress.total}`;
	}
	
	uni.showModal({
		title: title,
		content: content,
		showCancel: false,
		confirmText: '知道了',
		confirmColor: '#ffd541'
	});
};
</script>

<style scoped>
.medal-page {
	min-height: 100vh;
	background-color: #f8fafc;
	padding-bottom: 40px;
}

/* 导航栏 */
.nav-header {
	display: flex;
	align-items: center;
	justify-content: space-between;
	padding: 10px 16px 12px;
	background-color: #fff;
	position: sticky;
	top: 0;
	z-index: 100;
}
.nav-left {
	width: 60px;
	display: flex;
	align-items: center;
}
.nav-title {
	flex: 1;
	text-align: center;
	font-size: 17px;
	font-weight: 600;
	color: #333;
}
.nav-right { 
	width: 60px; 
}

/* 统计卡片 */
.summary-card {
	margin: 16px;
	padding: 24px;
	background: linear-gradient(135deg, #333 0%, #4b5563 100%);
	border-radius: 16px;
	display: flex;
	align-items: center;
	justify-content: space-between;
	color: #fff;
	box-shadow: 0 8px 16px rgba(0,0,0,0.1);
}
.summary-info {
	display: flex;
	flex-direction: column;
}
.total-label {
	font-size: 14px;
	opacity: 0.8;
	margin-bottom: 4px;
}
.total-count {
	font-size: 32px;
	font-weight: bold;
	color: #ffd541;
}

/* 勋章分类 */
.category-section {
	margin: 0 16px 20px;
	background-color: #fff;
	border-radius: 12px;
	padding: 16px;
}
.category-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 16px;
	padding-bottom: 8px;
	border-bottom: 1px solid #f1f5f9;
}
.category-title {
	font-size: 16px;
	font-weight: 600;
	color: #1e293b;
}
.category-progress {
	font-size: 12px;
	color: #64748b;
}

/* 勋章网格 */
.medal-grid {
	display: grid;
	grid-template-columns: repeat(3, 1fr);
	gap: 16px;
}
.medal-item {
	display: flex;
	flex-direction: column;
	align-items: center;
	text-align: center;
}

/* 勋章图标容器 */
.medal-icon-wrapper {
	width: 56px;
	height: 56px;
	border-radius: 50%;
	background-color: #f1f5f9;
	display: flex;
	align-items: center;
	justify-content: center;
	margin-bottom: 8px;
	transition: all 0.3s ease;
	border: 2px solid transparent;
}

/* 未解锁状态 */
.medal-item .medal-name {
	font-size: 13px;
	color: #94a3b8;
	font-weight: 500;
	margin-bottom: 2px;
}
.medal-item .medal-desc {
	font-size: 10px;
	color: #cbd5e1;
}

/* 已解锁状态 */
.medal-item.unlocked .medal-icon-wrapper {
	background: linear-gradient(135deg, #ffd541 0%, #f59e0b 100%);
	box-shadow: 0 4px 10px rgba(245, 158, 11, 0.3);
	transform: translateY(-2px);
}
.medal-item.unlocked .medal-name {
	color: #333;
	font-weight: 600;
}
.medal-item.unlocked .medal-desc {
	color: #f59e0b;
}

.locked-text {
	color: #cbd5e1;
}
</style>