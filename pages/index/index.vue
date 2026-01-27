<template>
  <view class="container">
    <text>Redirecting...</text>
  </view>
</template>

<script setup>
import { onMounted } from 'vue';

onMounted(() => {
  uni.redirectTo({
    url: '/pages/page_details/accounting_detail'
  });
});
</script>

<style>
.container {
  padding: 20px;
  text-align: center;
}
</style>
