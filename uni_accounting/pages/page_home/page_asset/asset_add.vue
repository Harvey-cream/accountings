<template>
	<view class="add-container" :class="currentThemeClass">
		<!-- 顶部导航 -->
		<!-- <view class="nav-bar">
			<view class="nav-left" @click="goBack">
				<van-icon name="arrow-left" size="20" color="#333" />
			</view>
		</view> -->

		<!-- 账户类型列表 -->
		<scroll-view scroll-y class="type-list">
			<van-cell-group>
				<van-cell v-for="item in accountTypes" :key="item.id" :title="item.name" :label="item.desc" is-link center @click="onTypeClick(item)">
					<template #icon>
						<view :class="['list-icon-wrap', item.bgClass]">
							<van-icon :name="item.icon" color="#fff" size="20" />
						</view>
					</template>
				</van-cell>
			</van-cell-group>
		</scroll-view>

		<!-- 输入金额弹窗 -->
		<van-dialog
			use-slot
			title="输入金额"
			:show="showAmountDialog"
			show-cancel-button
			@confirm="onConfirmAmount"
			@cancel="showAmountDialog = false"
		>
			<view class="amount-input-wrap">
				<view class="input-row">
					<text class="currency-symbol">¥</text>
					<input type="digit" v-model="inputAmount" class="amount-input" placeholder="0.00" focus />
				</view>
			</view>
		</van-dialog>
	</view>
</template>

<script setup>
import { ref } from 'vue';

const showAmountDialog = ref(false);
const inputAmount = ref('');
const currentType = ref(null);

const accountTypes = [
	{ id: 1, name: '现金', desc: '', icon: 'gold-coin', bgClass: 'bg-green' },
	{ id: 2, name: '储蓄卡', desc: '', icon: 'card', bgClass: 'bg-yellow' },
	{ id: 3, name: '信用卡', desc: '信用卡/蚂蚁花呗/京东白条', icon: 'credit-pay', bgClass: 'bg-orange' },
	{ id: 4, name: '虚拟账户', desc: '支付宝/微信', icon: 'gold-coin-o', bgClass: 'bg-yellow-dark' },
	{ id: 5, name: '投资账户', desc: '股票/基金/P2P', icon: 'chart-trending-o', bgClass: 'bg-orange-dark' },
	{ id: 6, name: '负债', desc: '贷款/借入', icon: 'info', bgClass: 'bg-red' },
	{ id: 7, name: '债权', desc: '应收/借出', icon: 'manager', bgClass: 'bg-blue' },
	{ id: 8, name: '自定义资产', desc: '', icon: 'points', bgClass: 'bg-purple' }
];

const goBack = () => {
	uni.navigateBack();
};

const onTypeClick = (item) => {
	currentType.value = item;
	inputAmount.value = '';
	showAmountDialog.value = true;
};

const onConfirmAmount = () => {
	if (!inputAmount.value) {
		uni.showToast({ title: '请输入金额', icon: 'none' });
		return;
	}
	
	// 这里可以添加保存逻辑，例如调用 API 或更新本地存储
	// 为了演示，直接提示成功并返回上一页
	uni.showToast({ title: '添加成功', icon: 'success' });
	
	setTimeout(() => {
		// 返回资产页面
		// 实际项目中这里应该更新上一页的数据
		uni.navigateBack();
	}, 1500);
};
</script>

<style scoped>
.add-container {
	height: 100vh;
	display: flex;
	flex-direction: column;
	background-color: #f8f8f8;
}

/* 顶部导航 */
.nav-bar {
	background-color: #ffd541;
	padding: 10px 10px 20px;
	display: flex;
	justify-content: space-between;
	align-items: center;
}

.nav-left {
	display: flex;
	align-items: center;
	gap: 4px;
}

.back-text {
	font-size: 16px;
	color: #333;
}

.nav-title {
	font-size: 18px;
	font-weight: 500;
	color: #333;
}

/* 列表样式 */
.type-list {
	flex: 1;
	overflow-y: auto;
	margin-top: 10px;
}

.list-icon-wrap {
	width: 36px;
	height: 36px;
	border-radius: 50%;
	display: flex;
	align-items: center;
	justify-content: center;
	margin-right: 12px;
}

/* 颜色类 */
.bg-green { background-color: #10b981; }
.bg-yellow { background-color: #f59e0b; }
.bg-orange { background-color: #f97316; }
.bg-yellow-dark { background-color: #d97706; }
.bg-orange-dark { background-color: #ea580c; }
.bg-red { background-color: #ef4444; }
.bg-blue { background-color: #3b82f6; }
.bg-purple { background-color: #8b5cf6; }

/* 弹窗输入框 */
.amount-input-wrap {
	padding: 20px 24px;
}

.input-row {
	display: flex;
	align-items: center;
	border-bottom: 1px solid #e2e8f0;
	padding-bottom: 8px;
}

.currency-symbol {
	font-size: 24px;
	font-weight: bold;
	color: #333;
	margin-right: 8px;
}

.amount-input {
	flex: 1;
	font-size: 24px;
	height: 36px;
}
</style>