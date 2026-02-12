<template>
	<view class="capsule-container">
		<view class="capsule-box" @click="handleHome">
			<van-icon name="wap-home-o" size="20" color="#000" />
		</view>
	</view>
</template>

<script setup>
import { ref, onMounted } from 'vue';

const statusBarHeight = ref(0);

onMounted(() => {
	const sysInfo = uni.getSystemInfoSync();
	statusBarHeight.value = sysInfo.statusBarHeight || 20;
});

const handleHome = () => {
	uni.navigateTo({
		url: '/pages/index/index'
	});
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
