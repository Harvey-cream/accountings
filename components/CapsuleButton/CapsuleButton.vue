<template>
	<view class="capsule-container">
		<view class="capsule-box" @click="handleBack">
			<van-icon :name="isFirstPage ? 'wap-home-o' : 'wap-home-o'" size="20" color="#000" />
		</view>
	</view>
</template>

<script setup>
import { ref, onMounted } from 'vue';

const statusBarHeight = ref(0);
const isFirstPage = ref(false);

onMounted(() => {
	const sysInfo = uni.getSystemInfoSync();
	statusBarHeight.value = sysInfo.statusBarHeight || 20;
	// 判断是否是当前页面栈的第一页
	const pages = getCurrentPages();
	if (pages.length <= 1) {
		isFirstPage.value = true;
	}
});

const handleBack = () => {
	const pages = getCurrentPages();
	
	if (pages.length > 1) {
		uni.navigateBack({
			delta: 1
		});
	} else {
		uni.switchTab({
			url: '/pages/index/index'
		});
	}
};
</script>

<style scoped>
.capsule-container {
	display: flex;
	align-items: center;
	height: 32px;
}

.capsule-box {
	width: 34px;
	height: 32px;
	display: flex;
	align-items: center;
	justify-content: center;
	background-color: rgba(255, 255, 255, 0.6);
	border: 0.5px solid rgba(0, 0, 0, 0.1);
	border-radius: 50%;
	backdrop-filter: blur(10px);
	cursor: pointer;
}

.capsule-box:active {
	background-color: rgba(0, 0, 0, 0.05);
}
</style>
