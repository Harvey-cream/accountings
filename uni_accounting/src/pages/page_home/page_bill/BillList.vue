<template>
  <view class="invoicePage" :class="currentThemeClass">
    <view class="header">
      <!-- 状态栏占位 -->
      <view class="status-bar"></view>
      <view class="headerTop">
        <!-- Year Selector -->
        <view class="yearSelector" @click="showYearPicker = true">
          <text class="yearText">{{ currentYear }}年</text>
          <van-icon name="arrow-down" size="12" color="#333" />
        </view>

        <!-- Segmented Control -->
        <view class="segmentControl">
          <view 
            class="segmentItem" :class="{ active: activeTab === 0 }" @click="activeTab = 0">
            <text class="segmentText">月账单</text>
          </view>
          <view 
            class="segmentItem" :class="{ active: activeTab === 1 }" @click="activeTab = 1">
            <text class="segmentText">年账单</text>
          </view>
        </view>

        <!-- Capsule Home Button -->
        <CapsuleButton />
      </view>
      <view class="chartContainer">
        <view class="chartTitle">
          <text>{{ activeTab === 0 ? '年结余' : '总结余' }}</text>
          <text class="balanceValue font-number"> ¥ {{ activeTab === 0 ? yearSummary.balance : totalSummary.balance }}</text>
        </view>
        
        <!-- Income Bar -->
        <view class="chartRow">
          <view class="chartLabelGroup">
            <text class="text-style-desc">{{ activeTab === 0 ? '年收入' : '总收入' }}</text>
            <text class="text-success text-style-number">¥ {{ activeTab === 0 ? yearSummary.income : totalSummary.income }}</text>
          </view>
          <view class="progressBarTrack">
            <view 
              class="progressBarFill incomeFill" 
              :style="{ width: displayIncomePercent + '%' }"
            ></view>
          </view>
        </view>

        <!-- Expense Bar -->
        <view class="chartRow" style="margin-top: 15px;">
          <view class="chartLabelGroup">
            <text class="text-style-desc">{{ activeTab === 0 ? '年支出' : '总支出' }}</text>
            <text class="text-danger text-style-number">¥ {{ activeTab === 0 ? yearSummary.expense : totalSummary.expense }}</text>
          </view>
          <view class="progressBarTrack">
            <view 
              class="progressBarFill expenseFill" 
              :style="{ width: displayExpensePercent + '%' }"
            ></view>
          </view>
        </view>
      </view>
    </view>

    <view class="listHeader container-padding">
      <text class="list-col text-style-desc">{{ activeTab === 0 ? '月份' : '年份' }}</text>
      <text class="list-col text-style-desc">{{ activeTab === 0 ? '月收入' : '年收入' }}</text>
      <text class="list-col text-style-desc">{{ activeTab === 0 ? '月支出' : '年支出' }}</text>
      <text class="list-col text-style-desc">{{ activeTab === 0 ? '月结余' : '年结余' }}</text>
      <view class="header-col-arrow"></view> 
    </view>

    <view class="billList">
      <template v-if="activeTab === 0">
        <view v-for="item in monthBills" :key="item.month" class="billItem container-padding">
          <text class="list-col text-style-title">{{ item.month }}月</text>
          <text class="list-col text-style-number">{{ item.income }}</text>
          <text class="list-col text-style-number">{{ item.expense }}</text>
          <text class="list-col text-style-number">{{ item.balance }}</text>
          <view class="col-arrow">
            <van-icon name="arrow" color="#ccc" size="14" />
          </view>
        </view>
      </template>
      <template v-else>
        <view v-for="item in yearBills" :key="item.year" class="billItem container-padding">
          <text class="list-col text-style-title">{{ item.year }}年</text>
          <text class="list-col text-style-number">{{ item.income }}</text>
          <text class="list-col text-style-number">{{ item.expense }}</text>
          <text class="list-col text-style-number">{{ item.balance }}</text>
          <view class="col-arrow">
            <van-icon name="arrow" color="#ccc" size="14" />
          </view>
        </view>
      </template>
    </view>

    <van-popup v-model:show="showYearPicker" position="bottom">
      <van-picker
        :columns="yearColumns"
        @confirm="onYearConfirm"
        @cancel="showYearPicker = false"
      />
    </van-popup>
  </view>
</template>

<script setup>
import { ref, onMounted, watch, nextTick } from 'vue';
import CapsuleButton from '@/components/CapsuleButton/CapsuleButton.vue';
import { getBillSummary } from '@/api/api.js';

const showYearPicker = ref(false);
const currentYear = ref(new Date().getFullYear().toString());
const activeTab = ref(0);

const yearColumns = ref([
  { text: '2026', value: '2026' },
  { text: '2025', value: '2025' },
  { text: '2024', value: '2024' },
]);

// Summary Data
const yearSummary = ref({
  balance: '0.00',
  income: '0.00',
  expense: '0.00'
});

const totalSummary = ref({
  balance: '0.00',
  income: '0.00',
  expense: '0.00'
});

const monthBills = ref([]);
const yearBills = ref([]);

// Animation Refs
const displayIncomePercent = ref(0);
const displayExpensePercent = ref(0);

// Helper to calculate percentages
const calculatePercents = () => {
  const data = activeTab.value === 0 ? yearSummary.value : totalSummary.value;
  const income = parseFloat(data.income.replace(/,/g, ''));
  const expense = parseFloat(data.expense.replace(/,/g, ''));
  const max = Math.max(income, expense);
  
  if (max === 0) return { income: 0, expense: 0 };
  return {
    income: (income / max) * 100,
    expense: (expense / max) * 100
  };
};

const animateCharts = async () => {
  // 1. Reset to 0 first
  displayIncomePercent.value = 0;
  displayExpensePercent.value = 0;
  
  // 2. Wait for DOM update to ensure width is 0
  await nextTick();
  
  // 3. Small delay to ensure the browser captures the change for transition
  setTimeout(() => {
    const { income, expense } = calculatePercents();
    displayIncomePercent.value = income;
    displayExpensePercent.value = expense;
  }, 50);
};

const fetchData = async () => {
  try {
    const res = await getBillSummary(currentYear.value);
    if (res.code === 0) {
      const data = res.data;
      yearSummary.value = data.yearSummary;
      totalSummary.value = data.totalSummary;
      monthBills.value = data.monthBills;
      yearBills.value = data.yearBills;
      
      // Update year columns based on available years
      if (data.yearBills && data.yearBills.length > 0) {
        yearColumns.value = data.yearBills.map(y => ({ text: y.year, value: y.year }));
      }
      
      animateCharts();
    }
  } catch (err) {
    console.error('获取账单汇总失败:', err);
  }
};

// Watch for tab changes to re-trigger animation
watch(activeTab, animateCharts);

// Initial data fetch
onMounted(() => {
  fetchData();
});

const onYearConfirm = ({ selectedOptions }) => {
  currentYear.value = selectedOptions[0].text;
  showYearPicker.value = false;
  fetchData();
};
</script>

<style scoped>
.invoicePage {
  min-height: 100vh;
}

.container-padding {
  padding-left: 20px;
  padding-right: 20px;
}

.header {
  padding: 10px 0; 
}

.headerTop {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  padding: 0 20px; /* Add horizontal padding only to top part */
}

.yearSelector {
  display: flex;
  align-items: center;
  gap: 4px;
}

.yearText {
  font-size: 16px;
  font-weight: bold;
}

.segmentControl {
  display: flex;
  background-color: #ffffff;
  border: 1px solid var(--primary-text-color);
  border-radius: 6px;
  overflow: hidden;
}

.segmentItem {
  padding: 4px 16px;
  cursor: pointer;
  transition: all 0.3s;
}

.segmentItem.active {
  background-color: var(--primary-text-color);
}

.segmentItem.active .segmentText {
  color: #fff;
}

.segmentText {
  font-size: 14px;
  color: var(--primary-text-color);
}

.headerIcons {
  display: flex;
  gap: 12px;
  align-items: center;
}

.headerIcon {
  color: var(--primary-text-color);
}

.chartContainer {
  width: 100%;
  margin-top: 10px;
  padding: 16px 20px; 
  box-sizing: border-box;
}

.chartTitle {
  font-size: var(--font-size-base);
  font-weight: bold;
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.balanceValue {
  font-size: var(--font-size-lg);
}

.chartRow {
  width: 100%;
}

.chartLabelGroup {
  display: flex;
  justify-content: space-between;
  margin-bottom: 6px;
}

/* .chartLabel and .chartValue removed to use global styles */

.progressBarTrack {
  height: 8px;
  background-color: #e2e8f0;
  border-radius: 4px;
  overflow: hidden;
}

.progressBarFill {
  height: 100%;
  border-radius: 4px;
  width: 0;
  transition: width 1.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.incomeFill { background-color: var(--income-color); }
.expenseFill { background-color: var(--expense-color); }

.listHeader {
  display: flex;
  padding-top: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f5f5f5;
}

.listHeaderItem {
  /* color: var(--light-text-color); handled by text-style-desc */
  /* text-align: right; handled by col classes */
}

.billItem {
  display: flex;
  padding-top: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid #f5f5f5;
  align-items: center;
}

/* Column Layout */
.list-col { flex: 1; text-align: right; }
.list-col:first-child { text-align: left; }

.col-arrow { 
  flex: 0.3; 
  display: flex;
  justify-content: flex-end;
  align-items: center; 
}
.header-col-arrow {
  flex: 0.3;
}
</style>