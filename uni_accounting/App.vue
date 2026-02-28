<script>
import { initRouterInterceptor, checkInitialPath } from '@/utils/navigate.js';

export default {
	onLaunch: function () {
		console.log('App Launch');
		// 1. 初始化路由拦截器
		initRouterInterceptor();
		// 2. 针对首次加载的 H5/APP 初始页面进行拦截
		let currentPath = '';
		currentPath = window.location.hash || window.location.pathname;
		currentPath = this.$scope?.route || '';
		checkInitialPath(currentPath);
		// 3. 其它初始化逻辑
		uni.hideTabBar().catch(() => {});

		// 定义初始 TabBar 列表
		const initialTabList = [
			{ text: '明细', icon: 'balance-list-o', selectedIcon: 'balance-list', path: '/pages/home/accounting_detail' },
			{ text: '图表', icon: 'chart-trending-o', selectedIcon: 'chart-trending-o', path: '/pages/chart/accounting_chart' },
			{ text: '记账', icon: 'plus', selectedIcon: 'plus', path: '/pages/page_saved/save_accouting', isFab: true },
			{ text: '发现', icon: 'eye-o', selectedIcon: 'eye', path: '/pages/discover/community' },
			{ text: '我的', icon: 'user-o', selectedIcon: 'user', path: '/pages/setting/center' }
		];

		// 将配置存入本地缓存
		uni.setStorageSync('tabList', initialTabList);
		// 发出全局事件通知 Tabbar 组件更新
		uni.$emit('updateTabbar');
	},
	onShow: function () {
		// console.log('App Show');
	},
	onHide: function () {
		// console.log('App Hide');
	}
};
</script>

<style lang="scss">
/* 每个页面公共css */
@import './static/css/common.css';
</style>
