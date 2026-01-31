<template>
  <view class="discover-container">
    <text>发现页面</text>
    <custom-tabbar />
  </view>
</template>

<script setup>
import CustomTabbar from '@/components/Tabbar/Tabbar.vue';
</script>

<style scoped>
.discover-container {
  padding: 20px;
  text-align: center;
  padding-bottom: 70px;
}
</style>
