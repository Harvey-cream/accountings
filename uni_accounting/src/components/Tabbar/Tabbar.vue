<template>
	<view class="tabbar-container">
		<van-tabbar v-model="active" active-color="#DC5431" inactive-color="#94a3b8" @change="onChange" class="custom-tabbar" :border="false">
			<van-tabbar-item v-for="(item, index) in tabList" :key="index" :name="index" :class="{ 'fab-item': item.isFab }">
				<template #icon="props">
					<template v-if="item.isFab">
						<view class="fab-main">
							<van-icon name="plus" class="fab-icon" />
						</view>
					</template>
					<van-icon v-else :name="props.active ? item.selectedIcon : item.icon" />
				</template>
				<text :class="['nav-name', { 'fab-label': item.isFab }]">{{ item.text }}</text>
			</van-tabbar-item>
		</van-tabbar>
	</view>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { onShow } from '@dcloudio/uni-app';

const getTabList = () => {
	let list = uni.getStorageSync('tabList');
	if (!list || list.length === 0) {
		// 如果缓存被清空了（比如退出登录时），重新初始化默认配置
		list = [
			{ text: '明细', icon: 'balance-list-o', selectedIcon: 'balance-list', path: '/pages/home/accounting_detail' },
			{ text: '图表', icon: 'chart-trending-o', selectedIcon: 'chart-trending-o', path: '/pages/chart/accounting_chart' },
			{ text: '记账', icon: 'plus', selectedIcon: 'plus', path: '/pages/page_saved/save_accouting', isFab: true },
			{ text: '发现', icon: 'eye-o', selectedIcon: 'eye', path: '/pages/discover/community' },
			{ text: '我的', icon: 'user-o', selectedIcon: 'manager', path: '/pages/setting/center' }
		];
		uni.setStorageSync('tabList', list);
	} else if (list.length > 0 && !list[0].selectedIcon) {
		// 如果缓存中是旧版列表（没有 selectedIcon 属性），强制更新
		list = [
			{ text: '明细', icon: 'balance-list-o', selectedIcon: 'balance-list', path: '/pages/home/accounting_detail' },
			{ text: '图表', icon: 'chart-trending-o', selectedIcon: 'chart-trending-o', path: '/pages/chart/accounting_chart' },
			{ text: '记账', icon: 'plus', selectedIcon: 'plus', path: '/pages/page_saved/save_accouting', isFab: true },
			{ text: '发现', icon: 'eye-o', selectedIcon: 'eye', path: '/pages/discover/community' },
			{ text: '我的', icon: 'user-o', selectedIcon: 'manager', path: '/pages/setting/center' }
		];
		uni.setStorageSync('tabList', list);
	}
	return list;
};

const tabList = ref(getTabList());

// 监听全局事件，动态更新 Tabbar 配置
uni.$on('updateTabbar', () => {
	tabList.value = getTabList();
});

// 初始化当前页面索引的逻辑封装
const getActiveIndex = () => {
	const pages = getCurrentPages();
	if (pages.length > 0) {
		const currentPage = pages[pages.length - 1];
		const path = '/' + currentPage.route;
		const index = tabList.value.findIndex((item) => item.path === path);
		return index !== -1 ? index : 0;
	}
	return 0;
};

const active = ref(getActiveIndex());

// 每次页面显示时刷新激活状态
onShow(() => {
	// console.log('Tabbar onShow, refreshing active state');
	active.value = getActiveIndex();
});

const onChange = (index) => {
	const target = tabList.value[index];

	// 特殊处理 Fab 按钮（记账）
	if (target.isFab) {
		// 立即重置 active，防止进入选中状态
		active.value = getActiveIndex();

		// 强制下一帧再次确认重置
		setTimeout(() => {
			active.value = getActiveIndex();
		}, 0);

		if (target.path) {
			uni.navigateTo({
				url: target.path,
				fail: (err) => {
					console.error('Navigation failed:', err);
					uni.switchTab({ url: target.path });
				}
			});
		}
		return;
	}

	// 普通 Tab 切换逻辑
	active.value = index;
	if (target && target.path) {
		uni.switchTab({
			url: target.path,
			fail: (err) => {
				uni.navigateTo({
					url: target.path,
					fail: (err2) => {
						uni.reLaunch({ url: target.path });
					}
				});
			}
		});
	}
};

onMounted(() => {
	// 监听更新事件
	uni.$on('updateTabbar', () => {
		tabList.value = uni.getStorageSync('tabList') || [];
		active.value = getActiveIndex();
	});
});
</script>

<style scoped>
.tabbar-container {
	position: fixed;
	bottom: 0;
	left: 0;
	right: 0;
	z-index: 999;
}

.custom-tabbar {
	height: 60px;
	background-color: #fefbf2 !important;
}

.nav-name {
	font-size: 10px;
	margin-top: 4px;
}

/* FAB Styles */
.fab-item {
	position: relative;
}

.fab-main {
	width: 50px;
	height: 50px;
	background-color: #ffd541;
	border-radius: 50%;
	display: flex;
	align-items: center;
	justify-content: center;
	margin-top: -45px;
	box-shadow: 0 4px 10px rgba(255, 213, 65, 0.4);
	border: 4px solid #fefbf2;
	transition: transform 0.15s cubic-bezier(0.34, 1.56, 0.64, 1); /* 弹性过渡效果 */
}

.fab-main:active {
	transform: scale(1.15); /* 点击时轻微放大 */
}

.fab-icon {
	font-size: 24px;
	color: #0f172a;
}

.fab-label {
	margin-top: 15px;
	color: #94a3b8;
}
</style>
