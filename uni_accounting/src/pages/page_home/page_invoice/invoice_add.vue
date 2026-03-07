<template>
	<view class="page-container" :class="currentThemeClass">
		<!-- 导航栏 -->
		<view class="nav-header" >
			<view class="nav-content">
				<view class="nav-left" @click="onBack">
					<van-icon name="arrow-left" size="20" color="#0f172a" />
					<text class="back-text">返回</text>
				</view>
				<text class="nav-title">{{ isEdit ? '编辑发票' : '添加发票' }}</text>
				<view class="nav-right">
				</view>
			</view>
		</view>

		<scroll-view scroll-y class="main-content">
			<view class="form-wrapper">
				<view class="form-group">
					<van-field
						v-model="form.name"
						label="名称"
						placeholder="公司名称 (必填)"
						input-align="right"
						:border="true"
					/>
					<van-field
						v-model="form.amount"
						label="金额"
						placeholder="0.00"
						input-align="right"
						type="digit"
						:border="true"
					/>
					<van-field
						v-model="form.taxId"
						label="税号"
						placeholder="15-20位 (企业报销时必填)"
						input-align="right"
						:border="true"
					/>
					<van-field
						v-model="form.address"
						label="单位地址"
						placeholder="公司地址"
						input-align="right"
						:border="true"
					/>
					<van-field
						v-model="form.phone"
						label="电话号码"
						placeholder="公司电话"
						input-align="right"
						:border="true"
					/>
					<van-field
						v-model="form.bank"
						label="开户银行"
						placeholder="开户银行"
						input-align="right"
						:border="true"
					/>
					<van-field
						v-model="form.account"
						label="银行账号"
						placeholder="银行账号"
						input-align="right"
						:border="false"
					/>
				</view>

				<view class="submit-box">
					<van-button 
						block 
						round 
						color="#fcd34d" 
						custom-class="submit-btn"
						@click="onSave"
						:disabled="!form.name"
					>
						<text class="btn-text">保存</text>
					</van-button>
					
					<view class="delete-btn" v-if="isEdit" @click="onDelete">
						<text class="delete-text">删除此发票信息</text>
					</view>
				</view>
			</view>
		</scroll-view>
	</view>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { onLoad } from '@dcloudio/uni-app';
import { saveInvoice, deleteInvoice, getInvoiceList } from '@/api/api.js';

const statusBarHeight = ref(20);
const isEdit = ref(false);
const form = ref({
	id: '',
	name: '',
	amount: '',
	taxId: '',
	address: '',
	phone: '',
	bank: '',
	account: ''
});

onMounted(() => {
	const sysInfo = uni.getSystemInfoSync();
	statusBarHeight.value = sysInfo.statusBarHeight || 20;
});

onLoad((options) => {
	if (options.id) {
		isEdit.value = true;
		loadInvoiceDetail(options.id);
	}
});

const loadInvoiceDetail = async (id) => {
	try {
		const res = await getInvoiceList();
		if (res.code === 0) {
			const item = res.data.find(i => i.id == id);
			if (item) {
				form.value = { 
					...item,
					// 后端返回的金额带千分位，保存时需要去掉
					amount: item.amount.replace(/,/g, '')
				};
			}
		}
	} catch (e) {
		console.error('获取发票详情失败:', e);
	}
};

const onBack = () => {
	uni.navigateBack();
};

const onSave = async () => {
	if (!form.value.name) return;

	try {
		const params = { ...form.value };
		const res = await saveInvoice(params);
		
		if (res.code === 0) {
			uni.showToast({ title: '保存成功', icon: 'success' });
			setTimeout(() => {
				uni.navigateBack();
			}, 1500);
		} else {
			uni.showToast({ title: res.msg || '保存失败', icon: 'none' });
		}
	} catch (e) {
		console.error('保存发票异常:', e);
		uni.showToast({ title: '网络异常，请稍后重试', icon: 'none' });
	}
};

const onDelete = () => {
	uni.showModal({
		title: '提示',
		content: '确定要删除这条发票信息吗？',
		success: async (res) => {
			if (res.confirm) {
				try {
					const result = await deleteInvoice(form.value.id);
					if (result.code === 0) {
						uni.showToast({ title: '删除成功', icon: 'success' });
						setTimeout(() => {
							uni.navigateBack();
						}, 1500);
					} else {
						uni.showToast({ title: result.msg || '删除失败', icon: 'none' });
					}
				} catch (e) {
					console.error('删除发票异常:', e);
					uni.showToast({ title: '网络异常，请稍后重试', icon: 'none' });
				}
			}
		}
	});
};
</script>

<style scoped>
.page-container {
	min-height: 100vh;
	background-color: #ffffff;
	display: flex;
	flex-direction: column;
}

.nav-header {
	z-index: 100;
	background-color: #fcd34d;
	padding-top: 15px;
}

.nav-content {
	height: 44px;
	display: flex;
	align-items: center;
	justify-content: space-between;
	padding: 0 16px;
}

.nav-left {
	display: flex;
	align-items: center;
	gap: 4px;
	width: 80px;
}

.back-text {
	font-size: 16px;
	color: #0f172a;
}

.nav-title {
	font-size: 17px;
	font-weight: 600;
	color: #0f172a;
}

.nav-right {
	width: 80px;
	display: flex;
	justify-content: flex-end;
}

.form-wrapper {
}

.form-group {
	background-color: #fff;
	border-radius: 12px;
	overflow: hidden;
	margin-bottom: 24px;
}

.submit-box {
	padding: 0 26px;
}

.submit-btn {
	color: #0f172a !important;
	font-weight: 600 !important;
}

.btn-text {
	color: #0f172a;
	font-weight: 600;
}

.delete-btn {
	margin-top: 16px;
	text-align: center;
	padding: 10px;
}

.delete-text {
	font-size: 14px;
	color: #ef4444;
}

/* 覆盖 Vant 样式 */
:deep(.van-cell) {
	padding: 16px !important;
}
</style>