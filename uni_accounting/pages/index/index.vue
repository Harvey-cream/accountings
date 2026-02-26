<template>
  <view class="container">
    <text>Redirecting...</text>
  </view>
</template>

<script setup>
import { onMounted } from 'vue';

onMounted(() => {
  uni.reLaunch({
    url: '/pages/home/accounting_detail'
  });
});
</script>

<style>
.container {
  padding: 20px;
  text-align: center;
}
</style>
