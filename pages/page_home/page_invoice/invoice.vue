<template>
	<view class="page-container">
		<!-- 顶部导航栏 -->
		<view class="nav-header" :style="{ paddingTop: statusBarHeight + 'px' }">
			<view class="nav-content">
				<view class="nav-left"></view>
				<text class="nav-title">发票助手</text>
				<view class="nav-right">
					<CapsuleButton />
				</view>
			</view>
		</view>

		<!-- 主要内容区 -->
		<scroll-view scroll-y class="main-content" >
			<view class="content-wrapper">
				<!-- 空状态 -->
				<view class="empty-state" v-if="invoices.length === 0">
					<view class="empty-icon-bg">
						<van-icon name="description" size="48" color="#cbd5e1" />
					</view>
					<text class="empty-text">暂无发票信息</text>
				</view>

				<!-- 发票列表 -->
				<view class="invoice-list" v-else>
					<view class="invoice-card" v-for="item in invoices" :key="item.id">
						<view class="card-header">
							<text class="company-name">{{ item.name }}</text>
							<van-icon name="edit" color="#94a3b8" size="18" @click="onEditInvoice(item)" />
						</view>
						<view class="card-body">
							<view class="info-row">
								<text class="label">税号</text>
								<text class="value">{{ item.taxId }}</text>
							</view>
							<view class="info-row" v-if="item.address">
								<text class="label">地址</text>
								<text class="value">{{ item.address }}</text>
							</view>
							<view class="info-row" v-if="item.bank">
								<text class="label">开户行</text>
								<text class="value">{{ item.bank }}</text>
							</view>
							<view class="info-row" v-if="item.account">
								<text class="label">账号</text>
								<text class="value">{{ item.account }}</text>
							</view>
						</view>
					</view>
				</view>
			</view>
		</scroll-view>

		<!-- 底部按钮 -->
		<view class="bottom-bar">
			<view class="add-button" @click="onAddInvoice">
				<van-icon name="plus" size="18" color="#0f172a" />
				<text class="add-text">添加发票</text>	
			</view>
		</view>
	</view>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import CapsuleButton from '@/components/CapsuleButton/CapsuleButton.vue';

const statusBarHeight = ref(20);
const invoices = ref([]);

onMounted(() => {
	const sysInfo = uni.getSystemInfoSync();
	statusBarHeight.value = sysInfo.statusBarHeight || 20;
	
	// 加载模拟数据或从本地存储加载
	loadInvoices();
});

const loadInvoices = () => {
		const stored = uni.getStorageSync('invoice_list');
		if (stored) {
			const parsedInvoices = JSON.parse(stored);
			if (parsedInvoices && parsedInvoices.length > 0) {
				invoices.value = parsedInvoices;
			} else {
				// 如果本地存储是空的或无效的，加载模拟数据
				loadMockInvoices();
			}
		} else {
			// 如果本地没有数据，加载模拟数据
			loadMockInvoices();
		}
	};

	const loadMockInvoices = () => {
		invoices.value = [
			{
				id: 1,
				name: '深圳市腾讯计算机系统有限公司',
				taxId: '91440300708461136T',
				address: '深圳市南山区高新区科技中一路腾讯大厦35层',
				phone: '0755-86013388',
				bank: '招商银行深圳威盛大厦支行',
				account: '817282292910201'
			},
			{
				id: 2,
				name: '北京字节跳动科技有限公司',
				taxId: '911101085923662400',
				address: '北京市海淀区北三环西路43号院2号楼',
				phone: '010-58341888',
				bank: '中国银行北京中关村支行',
				account: '340256025688'
			},
			{
				id: 3,
				name: '阿里巴巴（中国）网络技术有限公司',
				taxId: '91330100799655058B',
				address: '杭州市滨江区网商路699号',
				phone: '0571-85022088',
				bank: '招商银行杭州分行',
				account: '571906688810601'
			}
		];
		uni.setStorageSync('invoice_list', JSON.stringify(invoices.value));
	};

const onAddInvoice = () => {
	uni.navigateTo({
		url: '/pages/page_home/page_invoice/invoice_add'
	});
};

const onEditInvoice = (item) => {
	uni.navigateTo({
		url: `/pages/page_home/page_invoice/invoice_add?id=${item.id}`
	});
};
</script>

<style scoped>
.page-container {
	min-height: 100vh;
	background-color: #f8fafc;
	display: flex;
	flex-direction: column;
}

/* 导航栏 */
.nav-header {
	z-index: 100;
	background-color: #fcd34d; 
}

.nav-content {
	height: 34px;
	display: flex;
	align-items: center;
	justify-content: space-between;
	padding: 0 16px;
}

.nav-left, .nav-right {
	width: 80px;
	display: flex;
	align-items: center;
	padding-bottom: 15px;
}

.nav-right {
	justify-content: flex-end;
}

.nav-title {
	font-size: 17px;
	font-weight: 600;
	color: #0f172a;
	padding-bottom: 15px;
}

/* 内容区 */
.main-content {
	flex: 1;
	box-sizing: border-box;
}

.content-wrapper {
	padding: 6px;
	padding-bottom: 40px; 
}

/* 空状态 */
.empty-state {
	margin-top: 100px;
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
}

.empty-icon-bg {
	width: 80px;
	height: 80px;
	background-color: #fff;
	border-radius: 50%;
	display: flex;
	align-items: center;
	justify-content: center;
	margin-bottom: 10px;
	box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);
}

.empty-text {
	font-size: 15px;
	color: #94a3b8;
}

/* 发票列表 */
.invoice-card {
	background: #fff;
	border-radius: 16px;
	padding: 20px;
	margin-bottom: 10px;
	box-shadow: 0 2px 8px rgba(0, 0, 0, 0.02);
}

.card-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 16px;
	padding-bottom: 12px;
	border-bottom: 1px solid #f1f5f9;
}

.company-name {
	font-size: 16px;
	font-weight: 600;
	color: #0f172a;
}

.info-row {
	display: flex;
	margin-bottom: 8px;
}

.info-row:last-child {
	margin-bottom: 0;
}

.label {
	width: 60px;
	font-size: 13px;
	color: #64748b;
	flex-shrink: 0;
}

.value {
	font-size: 13px;
	color: #334155;
	flex: 1;
	word-break: break-all;
}

/* 底部按钮 */
.bottom-bar {
	position: fixed;
	bottom: 0;
	left: 0;
	right: 0;
	background-color: #fff;
	padding: 12px 16px 30px;
	box-shadow: 0 -4px 16px rgba(0, 0, 0, 0.05);
	z-index: 10;
}

.add-button {
	height: 15px;
	display: flex;
	justify-content: center;
	align-items: center;
	gap: 8px;
}

.add-text {
	font-size: 16px;
	font-weight: 500;
	color: #0f172a;
}
</style>