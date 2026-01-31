<script>
	export default {
		onLaunch: function() {
			console.log('App Launch')
			uni.hideTabBar();
			
			// 定义初始 TabBar 列表
			const initialTabList = [
				{ text: '明细', icon: 'balance-list-o', selectedIcon: 'balance-list', path: '/pages/page_details/accounting_detail' },
				{ text: '图表', icon: 'chart-trending-o', selectedIcon: 'chart-trending-o', path: '/pages/page_data/accounting_chart' },
				{ text: '记账', icon: 'plus', selectedIcon: 'plus', path: '/pages/page_saved/save_accouting', isFab: true },
				{ text: '发现', icon: 'eye-o', selectedIcon: 'eye', path: '/pages/page_discover/discover' },
				{ text: '我的', icon: 'user-o', selectedIcon: 'user', path: '/pages/page_my/my' }
			];
			
			// 将配置存入本地缓存
			uni.setStorageSync('tabList', initialTabList);
			// 发出全局事件通知 Tabbar 组件更新
			uni.$emit('updateTabbar');
		},
		onShow: function() {
			console.log('App Show')
		},
		onHide: function() {
			console.log('App Hide')
		}
	}
</script>

<style>
	/*每个页面公共css */
</style>
