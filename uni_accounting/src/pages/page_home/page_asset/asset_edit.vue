<template>
	<view class="edit-container">
		<view :style="{ height: statusBarHeight + 'px' }" class="status-bar"></view>
		<view class="nav-bar">
			<view class="nav-title">添加{{ accountType?.name || '资产' }}</view>
			<view class="nav-right">
				<CapsuleButton />
			</view>
		</view>
		<view class="form-container">
			<!-- 名称输入 -->
			<view class="form-item">
				<text class="label">名称</text>
				<input 
					v-if="Number(accountType?.id) === 8"
					class="input" 
					v-model="form.name" 
					placeholder="请输入自定义账户" 
					placeholder-class="placeholder" 
				/>
				<text v-else class="input readonly-text">{{ form.name }}</text>
			</view>
			<view class="form-item">
				<text class="label">备注</text>
				<input class="input" v-model="form.remark" placeholder="(选填)" placeholder-class="placeholder" />
			</view>
			<view class="form-item no-border">
				<text class="label">余额</text>
				<view class="amount-input-wrap">
					<input class="amount-input" type="digit" v-model="form.balance" placeholder="0.00" placeholder-class="placeholder" focus />
				</view>
			</view>
			<view class="btn-wrap">
				<button class="save-btn" @click="handleSave">保存</button>
			</view>
		</view>
		<view class="keyboard-placeholder">

		</view>
	</view>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import { onLoad } from '@dcloudio/uni-app';
import CapsuleButton from '@/components/CapsuleButton/CapsuleButton.vue';
import { saveAssetAccount } from '@/api/api.js';

const statusBarHeight = ref(20);
const accountType = ref(null);
const form = reactive({
	name: '',
	remark: '',
	balance: '',
	is_included_in_total: true
});

onMounted(() => {
	const sysInfo = uni.getSystemInfoSync();
	statusBarHeight.value = sysInfo.statusBarHeight || 20;
});

onLoad((options) => {
	if (options.type) {
		try {
			accountType.value = JSON.parse(decodeURIComponent(options.type));
			// 如果是自定义资产(ID 8)，将名称初始化为空，方便用户输入新名字
			if (Number(accountType.value.id) === 8) {
				form.name = '';
			} else {
				form.name = accountType.value.name;
			}
		} catch (e) {
			console.error('解析参数失败', e);
		}
	}
});

const goBack = () => {
	uni.navigateBack();
};

const handleSave = async () => {
	if (!form.name && Number(accountType.value?.id) === 8) {
		uni.showToast({ title: '请输入账户名称', icon: 'none' });
		return;
	}
	if (!form.balance) {
		uni.showToast({ title: '请输入余额', icon: 'none' });
		return;
	}
	
	uni.showLoading({ title: '保存中' });
	
	try {
		// 根据 ID 自动判断是资产还是负债
		// 3: 信用卡, 6: 负债
		const isDebt = [3, 6].includes(Number(accountType.value.id));
		
		const params = {
			name: form.name || accountType.value.name,
			asset_type_id: accountType.value.id,
			balance: form.balance,
			type: isDebt ? 'debt' : 'asset',
			is_included_in_total: form.is_included_in_total,
			remark: form.remark
		};
		
		const res = await saveAssetAccount(params);
		
		if (res.code === 0) {
			uni.showToast({ title: '保存成功', icon: 'success' });
			setTimeout(() => {
				uni.navigateBack({ delta: 2 }); // 返回到资产首页
			}, 1500);
		}
	} catch (e) {
		console.error('保存资产失败:', e);
	} finally {
		uni.hideLoading();
	}
};
</script>

<style scoped>
.edit-container {
	min-height: 100vh;
	background-color: #fff;
	display: flex;
	flex-direction: column;
}

.status-bar {
	width: 100%;
	background-color: #ffd541;
}

/* 导航栏样式 */
.nav-bar {
	padding: 14px 0;
	background-color: #ffd541;
	display: flex;
	align-items: center;
	padding: 0 12px;
	position: relative;
}

.nav-title {
	font-size: 17px;
	font-weight: 500;
	color: #333;
	position: absolute;
	left: 50%;
	transform: translateX(-50%);
	white-space: nowrap;
	pointer-events: none;
}

.nav-right {
	flex: 1;
	display: flex;
	justify-content: flex-end;
	margin-bottom: 10px;
}

/* 表单样式 */
.form-container {
	padding: 0px 16px;
}

.form-item {
	display: flex;
	align-items: center;
	padding: 16px 0;
	border-bottom: 0.5px solid #eee;
}

.no-border {
	border-bottom: none;
}

.label {
	width: 60px;
	font-size: 15px;
	color: #333;
}

.input {
	flex: 1;
	font-size: 15px;
	color: #333;
	text-align: right;
	height: 24px;
	line-height: 24px;
}

.readonly-text {
	color: #666;
}

.amount-input-wrap {
	flex: 1;
	display: flex;
	justify-content: flex-end;
}

.amount-input {
	font-size: 18px;
	color: #333;
	text-align: right;
	width: 100%;
}

.placeholder {
	color: #ccc;
}

/* 按钮样式 */
.btn-wrap {
	margin-top: 40px;
}

.save-btn {
	background-color: #ffd541;
	color: #333;
	border-radius: 8px;
	font-size: 16px;
	height: 44px;
	line-height: 44px;
	border: none;
}

.save-btn:active {
	opacity: 0.8;
}

.keyboard-placeholder {
	flex: 1;
	background-color: #f8f8f8;
	margin-top: 20px;
}
</style>
