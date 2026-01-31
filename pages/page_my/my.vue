<template>
  <view class="my-container">
    <text>我的页面</text>
    <custom-tabbar />
  </view>
</template>

<script setup>
import CustomTabbar from '@/components/Tabbar/Tabbar.vue';
</script>

<style scoped>
.my-container {
  padding: 20px;
  text-align: center;
  padding-bottom: 70px;
}
</style>
