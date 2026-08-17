<template>
	<view class="ai-page">
		<!-- Top Header Section (Matching save_accouting.vue) -->
		<view class="top-section">
			<view class="header-bar">
				<view class="ai-header-bubble">
					<text class="header-title">来试试AI记账吧</text>
				</view>
				<view class="manual-btn" @click="goToManual">
					<van-icon name="edit" size="16" color="#0f172a" />
					<text class="manual-text">手动记</text>
				</view>
			</view>
		</view>
		<scroll-view
			scroll-y
			class="chat-container"
			:class="{ 'chat-ready': historyReady }"
			:scroll-top="scrollTop"
			:scroll-with-animation="false"
			upper-threshold="80"
			@scrolltoupper="loadMoreHistory"
		>
			<view class="chat-list">
				<view class="top-spacer"></view>
				<view v-for="msg in messages" :key="msg.id" :class="['message-item', msg.role === 'user' ? 'user-msg' : 'ai-msg']">
					<!-- Avatar -->
					<view class="avatar">
						<image :src="msg.role === 'user' ? '/static/default_avatar.png' : '/static/logo.png'" mode="aspectFill" />
					</view>
					<view class="content-box">
						<!-- Text Message -->
						<view v-if="msg.type === 'text' || msg.type === 'text_image'" class="bubble">
							<text v-if="msg.content" class="text-content">{{ displayText(msg) }}</text>
							<text v-else-if="streamingAiId === msg.id && streamingStatus" class="streaming-hint">{{ streamingStatus }}</text>
							<view v-else-if="streamingAiId === msg.id" class="typing-bubble">
								<view class="typing-dot"></view>
								<view class="typing-dot"></view>
								<view class="typing-dot"></view>
							</view>
						</view>
						<view v-if="msg.type === 'text_image'" class="image-box">
							<image :src="msg.image" mode="widthFix" class="content-image" />
							<view class="image-overlay">鸭了个鸭?</view>
						</view>
						<view v-if="msg.type === 'transaction'" class="transaction-card">
							<view class="card-body">
								<view class="cat-icon-wrap" :style="{ backgroundColor: msg.bgColor }">
									<van-icon :name="msg.icon" :color="msg.iconColor" size="24" />
								</view>
								<view class="cat-details">
									<text class="cat-title">{{ msg.category }}</text>
									<text class="cat-sub">{{ msg.remark }}</text>
								</view>
								<text class="amount-text">{{ msg.amount }}</text>
							</view>
							<view class="card-footer">
								<text class="date-text">{{ msg.date }}</text>
								<view class="card-actions">
									<view class="action-btn-mini" @click="handleDelete(msg)">
										<van-icon name="delete-o" size="16" color="#666" />
									</view>
									<view class="action-btn-mini edit-btn" @click="openEdit(msg)">
										<van-icon name="edit" size="14" color="#333" />
										<text class="edit-text">编辑</text>
									</view>
								</view>
							</view>
						</view>
						<view v-if="msg.type === 'transaction' && msg.content" class="bubble txn-reply-bubble">
							<text class="text-content">{{ displayText(msg) }}</text>
						</view>
						<!-- 写操作确认卡片：账单/资产/发票共用，点确认/取消后回传 -->
						<view v-if="msg.type === 'confirm'" class="confirm-card">
							<text v-if="msg.content" class="confirm-title">{{ displayText(msg) }}</text>
							<view
								v-for="(item, i) in (msg.candidates || [])"
								:key="item.id || i"
								class="confirm-item"
							>
								<view class="confirm-item-main">
									<text class="confirm-item-name">{{ confirmItemName(msg, item) }}</text>
									<text class="confirm-item-meta">{{ confirmItemMeta(msg, item) }}</text>
								</view>
								<view
									v-if="!msg.resolved && !isTargetlessConfirm(msg)"
									class="confirm-btn confirm-btn-ok"
									@click="handleConfirmAction(msg, true, item)"
								>确认{{ actionLabel(msg.action) }}</view>
							</view>
							<view v-if="!msg.resolved" class="confirm-actions">
								<view
									v-if="isTargetlessConfirm(msg)"
									class="confirm-btn confirm-btn-ok"
									@click="handleConfirmAction(msg, true)"
								>确认{{ actionLabel(msg.action) }}</view>
								<view class="confirm-btn confirm-btn-cancel" @click="handleConfirmAction(msg, false)">取消</view>
							</view>
							<text v-else class="confirm-resolved">已处理</text>
						</view>
					</view>
				</view>
				<!-- Spacer for fixed bottom panel -->
				<view v-if="loading" class="message-item ai-msg">
					<view class="avatar">
						<image src="/static/logo.png" mode="aspectFill" />
					</view>
					<view class="content-box">
						<view class="bubble typing-bubble">
							<view class="typing-dot"></view>
							<view class="typing-dot"></view>
							<view class="typing-dot"></view>
						</view>
					</view>
				</view>
				<view class="bottom-spacer"></view>
			</view>
		</scroll-view>

		<!-- Bottom Interaction Area -->
		<view class="bottom-panel">
			<view class="input-container">
				<view class="voice-icon">
					<van-icon name="audio" size="24" color="#333" />
				</view>
				<input 
					type="text" 
					v-model="inputValue"
					placeholder="发送消息给福娃鸭" 
					class="main-input" 
					placeholder-style="color: #999"
					@confirm="handleSend"
				/>
				<van-icon 
					v-if="inputValue" 
					name="send-gift-o" 
					size="24" 
					color="#ffd541" 
					style="margin-left: 10px;" 
					@click="handleSend"
				/>
			</view>
		</view>

		<!-- Edit Bill Popup -->
		<van-popup v-model:show="showEdit" position="bottom" round class="edit-popup">
			<view class="popup-header">
				<text class="popup-title">修改账单</text>
				<van-icon name="cross" size="20" color="#999" @click="showEdit = false" />
			</view>
			<view class="edit-form">
				<view class="form-item">
					<text class="label">金额</text>
					<input type="digit" v-model="editForm.amount" class="edit-input" placeholder="请输入金额" />
				</view>
				<view class="form-item">
					<text class="label">备注</text>
					<input type="text" v-model="editForm.remark" class="edit-input" placeholder="请输入备注" />
				</view>
				<view class="form-item">
					<text class="label">日期</text>
					<picker mode="date" :value="editForm.date" @change="onDateChange">
						<view class="picker-val">{{ editForm.date || '请选择日期' }}</view>
					</picker>
				</view>
				<button class="save-btn" @click="handleUpdate">确认修改</button>
			</view>
		</van-popup>
	</view>
</template>

<script setup>
import { ref, onMounted, nextTick, getCurrentInstance } from 'vue';
import { getLangchainChat, sendLangchainChat, deleteBill, updateBill } from '@/api/api.js';
import { isLangchainStreamSupported, sendLangchainChatStream } from '@/utils/langchain_stream.js';

const goToManual = () => {
	uni.navigateBack();
};

const messages = ref([]);
const inputValue = ref('');
const loading = ref(false);
const streamingAiId = ref(null);
const streamingStatus = ref('');
const scrollTop = ref(0);
const historyReady = ref(false);
const hasMoreHistory = ref(false);
const loadingHistory = ref(false);
let scrollRaf = 0;
const HISTORY_PAGE_SIZE = 20;
const instance = getCurrentInstance();

const patchAiMessage = (aiId, patch) => {
	const idx = messages.value.findIndex((m) => m.id === aiId);
	if (idx < 0) return;
	messages.value[idx] = { ...messages.value[idx], ...patch };
};

const displayText = (msg) => {
	const text = msg?.content || '';
	return msg?.role === 'ai' ? text.replace(/\*\*/g, '') : text;
};

// Edit Logic
const showEdit = ref(false);
const currentMsg = ref(null);
const editForm = ref({
	amount: '',
	remark: '',
	date: ''
});

const openEdit = (msg) => {
	currentMsg.value = msg;
	// 去掉金额前面的符号
	const cleanAmount = msg.amount.replace(/[+-]/, '');
	editForm.value = {
		amount: cleanAmount,
		remark: msg.remark,
		date: msg.date.replace(/年|月/g, '-').replace(/日/g, '')
	};
	showEdit.value = true;
};

const onDateChange = (e) => {
	editForm.value.date = e.detail.value;
};

const handleUpdate = async () => {
	if (!editForm.value.amount) return uni.showToast({ title: '请输入金额', icon: 'none' });
	
	try {
		const res = await updateBill({
			id: currentMsg.value.record_id,
			amount: editForm.value.amount,
			remark: editForm.value.remark,
			date: editForm.value.date,
			type: currentMsg.value.amount.startsWith('-') ? 'expense' : 'income'
		});
		
		if (res.code === 0) {
			uni.showToast({ title: '修改成功' });
			showEdit.value = false;
			// 更新本地列表数据
			const prefix = currentMsg.value.amount.startsWith('-') ? '-' : '+';
			currentMsg.value.amount = `${prefix}${parseFloat(editForm.value.amount).toFixed(2)}`;
			currentMsg.value.remark = editForm.value.remark;
			currentMsg.value.date = editForm.value.date.replace(/-/g, (match, offset) => offset === 4 ? '年' : '月') + '日';
		}
	} catch (e) {
		uni.showToast({ title: '更新失败', icon: 'none' });
	}
};

const handleDelete = (msg) => {
	uni.showModal({
		title: '提示',
		content: '确定要删除这条账单吗？',
		success: async (res) => {
			if (res.confirm) {
				try {
					const delRes = await deleteBill({ id: msg.record_id });
					if (delRes.code === 0) {
						uni.showToast({ title: '删除成功' });
						// 这里只是从 UI 上隐藏，或者您可以重新获取列表
						messages.value = messages.value.filter(m => m.id !== msg.id);
					}
				} catch (e) {
					uni.showToast({ title: '删除失败', icon: 'none' });
				}
			}
		}
	});
};

const fetchHistory = async () => {
	try {
		const res = await getLangchainChat({ limit: HISTORY_PAGE_SIZE });
		if (res.code === 0) {
			const payload = res.data || {};
			const list = (payload.messages || []).map((msg) => formatMessage(msg));
			hasMoreHistory.value = !!payload.has_more;
			messages.value = list;
			await nextTick();
			scrollTop.value = 999999 + Math.random();
			await nextTick();
			historyReady.value = true;
		}
	} catch (e) {
		console.error('获取历史记录失败:', e);
		historyReady.value = true;
	}
};

const measureListHeight = () => new Promise((resolve) => {
	uni.createSelectorQuery()
		.in(instance.proxy)
		.select('.chat-list')
		.boundingClientRect((rect) => resolve(rect?.height || 0))
		.exec();
});

const loadMoreHistory = async () => {
	if (!hasMoreHistory.value || loadingHistory.value || !messages.value.length) return;
	const first = messages.value[0];
	if (typeof first.id !== 'number') return;

	loadingHistory.value = true;
	try {
		const oldHeight = await measureListHeight();
		const res = await getLangchainChat({ limit: HISTORY_PAGE_SIZE, before_id: first.id });
		if (res.code !== 0) return;

		const payload = res.data || {};
		const older = (payload.messages || []).map((msg) => formatMessage(msg));
		hasMoreHistory.value = !!payload.has_more;
		if (!older.length) {
			hasMoreHistory.value = false;
			return;
		}

		messages.value = [...older, ...messages.value];
		await nextTick();
		const newHeight = await measureListHeight();
		scrollTop.value = Math.max(0, newHeight - oldHeight);
	} catch (e) {
		console.error('加载更多历史失败:', e);
	} finally {
		loadingHistory.value = false;
	}
};

const formatMessage = (msg) => {
	const formatted = {
		id: msg.id,
		role: msg.role,
		type: msg.type,
		content: msg.role === 'ai' ? (msg.content || '').replace(/\*\*/g, '') : msg.content,
		image: msg.image_url
	};
	
	if ((msg.type === 'transaction' || msg.type === 'confirm') && msg.extra_data) {
		const extra = typeof msg.extra_data === 'string' ? JSON.parse(msg.extra_data) : msg.extra_data;
		Object.assign(formatted, extra);
	}
	return formatted;
};

const ACTION_LABELS = {
	update: '修改',
	delete: '删除',
	create: '新建',
	adjust_balance: '调整',
	batch_create: '记账'
};
const actionLabel = (action) => ACTION_LABELS[action] || '操作';

// 这些写操作没有既有目标对象，确认时不需要 target_id，只出一个确认按钮
const isTargetlessConfirm = (msg) => {
	const entity = msg?.entity || 'bill';
	return (entity === 'bill' && msg?.action === 'batch_create')
		|| (entity === 'asset' && msg?.action === 'create');
};

const formatMoney = (n) => (n % 1 === 0 ? String(n) : n.toFixed(2));

const formatConfirmAmount = (item) => {
	const n = Number(item?.amount);
	if (Number.isNaN(n)) return '';
	const prefix = (item?.type || item?.bill_type) === 'income' ? '+' : '-';
	return `${prefix}${formatMoney(n)}元`;
};

const confirmItemName = (msg, item) => {
	const entity = msg?.entity || 'bill';
	if (entity === 'asset') return item.name || '账户';
	if (entity === 'invoice') return item.name || '发票抬头';
	return item.remark || item.description || item.category || '账单';
};

const confirmItemMeta = (msg, item) => {
	const entity = msg?.entity || 'bill';
	if (entity === 'asset') {
		// 负债余额后端已带负号
		const n = Number(item.balance);
		return [item.asset_type, Number.isNaN(n) ? '' : `${formatMoney(n)}元`].filter(Boolean).join(' · ');
	}
	if (entity === 'invoice') return item.tax_id || '';
	return [item.date, formatConfirmAmount(item)].filter(Boolean).join(' · ');
};

const markConfirmResolved = (msg) => {
	const idx = messages.value.findIndex((m) => m.id === msg.id);
	if (idx >= 0) {
		messages.value[idx] = { ...messages.value[idx], resolved: true };
	}
};

/** 确认卡片：confirm 布尔 + entity/action/target_id + message_id 回传后端 */
const handleConfirmAction = async (msg, ok, item = null) => {
	if (loading.value || msg.resolved) return;
	const extra = ok
		? { confirm: true, entity: msg.entity || 'bill', action: msg.action, target_id: item?.id, message_id: msg.id }
		: { confirm: false, message_id: msg.id };
	if (ok && (!extra.action || (extra.target_id == null && !isTargetlessConfirm(msg)))) {
		return uni.showToast({ title: '缺少确认信息', icon: 'none' });
	}

	const content = ok ? `确认${actionLabel(msg.action)}` : '取消';
	markConfirmResolved(msg);
	messages.value.push({
		id: `local-user-${Date.now()}`,
		role: 'user',
		type: 'text',
		content
	});
	scrollToBottom();

	const loadingStart = Date.now();
	if (isLangchainStreamSupported()) {
		const aiId = `local-ai-${Date.now()}`;
		streamingAiId.value = aiId;
		streamingStatus.value = '';
		messages.value.push({ id: aiId, role: 'ai', type: 'text', content: '' });
		try {
			await sendLangchainChatStream(content, {
				onStatus: (text) => {
					if (streamingAiId.value === aiId) streamingStatus.value = text;
					scrollToBottomThrottled();
				},
				onToken: (text) => {
					const idx = messages.value.findIndex((m) => m.id === aiId);
					if (idx < 0) return;
					if (streamingStatus.value) streamingStatus.value = '';
					const prev = messages.value[idx].content || '';
					patchAiMessage(aiId, { content: prev + text.replace(/\*\*/g, '') });
					scrollToBottomThrottled();
				},
				onDone: (event) => {
					streamingAiId.value = null;
					streamingStatus.value = '';
					const aiMsg = (event.data || []).find((m) => m.role === 'ai');
					const idx = messages.value.findIndex((m) => m.id === aiId);
					if (aiMsg && idx >= 0) {
						const streamed = messages.value[idx].content;
						const formatted = formatMessage(aiMsg);
						if (formatted.type === 'text') {
							formatted.content = streamed || formatted.content;
						}
						messages.value[idx] = formatted;
					}
					scrollToBottom();
				},
				onError: () => {
					streamingAiId.value = null;
					streamingStatus.value = '';
					uni.showToast({ title: '发送失败', icon: 'none' });
				}
			}, extra);
		} catch (e) {
			streamingAiId.value = null;
			streamingStatus.value = '';
			uni.showToast({ title: '发送失败', icon: 'none' });
		}
		return;
	}

	loading.value = true;
	try {
		const res = await sendLangchainChat({ content, ...extra });
		if (res.code === 0) {
			(res.data || [])
				.filter((m) => m.role === 'ai')
				.forEach((m) => messages.value.push(formatMessage(m)));
			scrollToBottom();
		}
	} catch (e) {
		uni.showToast({ title: '发送失败', icon: 'none' });
	} finally {
		const elapsed = Date.now() - loadingStart;
		setTimeout(() => { loading.value = false; }, Math.max(0, 450 - elapsed));
	}
};

const handleSend = async () => {
	if (!inputValue.value.trim() || loading.value) return;
	
	const content = inputValue.value.trim();
	const loadingStart = Date.now();
	inputValue.value = '';
	messages.value.push({
		id: `local-user-${Date.now()}`,
		role: 'user',
		type: 'text',
		content
	});
	scrollToBottom();

	// H5：流式主路径；小程序/App：降级同步 POST
	if (isLangchainStreamSupported()) {
		const aiId = `local-ai-${Date.now()}`;
		streamingAiId.value = aiId;
		streamingStatus.value = '';
		messages.value.push({ id: aiId, role: 'ai', type: 'text', content: '' });
		try {
			await sendLangchainChatStream(content, {
				onStatus: (text) => {
					if (streamingAiId.value === aiId) streamingStatus.value = text;
					scrollToBottomThrottled();
				},
				onToken: (text) => {
					const idx = messages.value.findIndex((m) => m.id === aiId);
					if (idx < 0) return;
					if (streamingStatus.value) streamingStatus.value = '';
					const prev = messages.value[idx].content || '';
					patchAiMessage(aiId, { content: prev + text.replace(/\*\*/g, '') });
					scrollToBottomThrottled();
				},
				onDone: (event) => {
					streamingAiId.value = null;
					streamingStatus.value = '';
					const aiMsg = (event.data || []).find((m) => m.role === 'ai');
					const idx = messages.value.findIndex((m) => m.id === aiId);
					if (aiMsg && idx >= 0) {
						const streamed = messages.value[idx].content;
						const formatted = formatMessage(aiMsg);
						if (formatted.type === 'text') {
							formatted.content = streamed || formatted.content;
						}
						messages.value[idx] = formatted;
					}
					scrollToBottom();
				},
				onError: () => {
					streamingAiId.value = null;
					streamingStatus.value = '';
					uni.showToast({ title: '发送失败', icon: 'none' });
				}
			});
		} catch (e) {
			streamingAiId.value = null;
			streamingStatus.value = '';
			uni.showToast({ title: '发送失败', icon: 'none' });
		}
		return;
	}

	loading.value = true;
	scrollToBottom();

	try {
		const res = await sendLangchainChat({ content });
		if (res.code === 0) {
			res.data
				.filter(msg => msg.role === 'ai')
				.forEach(msg => {
				messages.value.push(formatMessage(msg));
			});
			scrollToBottom();
		}
	} catch (e) {
		uni.showToast({ title: '发送失败', icon: 'none' });
	} finally {
		const elapsed = Date.now() - loadingStart;
		const remain = Math.max(0, 450 - elapsed);
		setTimeout(() => {
			loading.value = false;
		}, remain);
	}
};

const scrollToBottom = () => {
	nextTick(() => {
		scrollTop.value = 999999 + Math.random();
	});
};

const scrollToBottomThrottled = () => {
	if (scrollRaf) return;
	scrollRaf = requestAnimationFrame(() => {
		scrollRaf = 0;
		scrollToBottom();
	});
};

onMounted(() => {
	fetchHistory();
});
</script>

<style scoped>
.ai-page {
	display: flex;
	flex-direction: column;
	height: 100vh;
	background: #fff; /* Main background changed to white */
	position: relative;
}

/* --- Top Section --- */
.top-section {
	position: fixed;
	top: 0;
	left: 0;
	right: 0;
	z-index: 100;
	background-color: #ffd541; /* Matching save_accouting.vue */
	padding: 14px 20px 10px; 
	display: flex;
	flex-direction: column;
}

.top-spacer {
	height: 100px; /* Fixed space for header to avoid overlap */
}

.header-bar {
	display: flex;
	justify-content: space-between;
	align-items: center;
}

.ai-header-bubble {
	position: relative;
	background-color: #ffec99;
	padding: 6px 14px;
	border-radius: 12px;
	box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
	margin-left: 10px;
}

.ai-header-bubble::after {
	content: "";
	position: absolute;
	left: -6px;
	top: 50%;
	transform: translateY(-50%);
	border-right: 8px solid #ffec99;
	border-top: 6px solid transparent;
	border-bottom: 6px solid transparent;
}

.header-title {
	font-size: 15px;
	font-weight: bold;
	color: #0f172a;
}

.manual-btn {
	display: flex;
	align-items: center;
	padding: 4px 10px;
	background-color: rgba(15, 23, 42, 0.05);
	border-radius: 20px;
	border: 1px solid rgba(15, 23, 42, 0.1);
}

.manual-text {
	font-size: 14px;
	font-weight: 500;
	color: #0f172a;
	margin-left: 4px;
}

.trial-banner {
	display: flex;
	justify-content: space-between;
	align-items: center;
	padding: 8px 15px;
	background: rgba(255, 255, 255, 0.9);
	border-radius: 12px;
	box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
}

.trial-content {
	display: flex;
	align-items: center;
}

.mini-logo {
	width: 20px;
	height: 20px;
	margin-right: 8px;
}

.trial-text {
	font-size: 13px;
	color: #333;
}

/* --- Chat Content --- */
.chat-container {
	flex: 1;
	min-height: 0;
	background-color: #fff;
	visibility: hidden;
}

.chat-container.chat-ready {
	visibility: visible;
}

.chat-list {
	padding: 15px;
	display: flex;
	flex-direction: column;
}

.message-item {
	display: flex;
	margin-bottom: 20px;
	max-width: 90%;
}

.ai-msg {
	align-self: flex-start;
}

.user-msg {
	align-self: flex-end;
	flex-direction: row-reverse;
}

.avatar {
	width: 40px;
	height: 40px;
	flex-shrink: 0;
}

.avatar image {
	width: 100%;
	height: 100%;
	border-radius: 50%;
	background-color: #f1f5f9;
}

.ai-msg .avatar {
	margin-right: 10px;
}

.user-msg .avatar {
	margin-left: 10px;
}

.content-box {
	display: flex;
	flex-direction: column;
	gap: 8px;
	max-width: 80%;
}

.bubble {
	padding: 12px 16px;
	border-radius: 18px;
	box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.ai-msg .bubble {
	background: #f1f5f9;
	border-top-left-radius: 4px;
	color: #333;
}

.user-msg .bubble {
	background: #ffd541;
	border-top-right-radius: 4px;
	color: #0f172a;
}

.text-content {
	font-size: 15px;
	line-height: 1.5;
	white-space: pre-wrap;
	word-break: break-word;
	overflow-wrap: anywhere;
}

.streaming-hint {
	font-size: 15px;
	line-height: 1.5;
	color: #94a3b8;
}

.image-box {
	position: relative;
	border-radius: 12px;
	overflow: hidden;
	box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

.content-image {
	width: 100%;
	display: block;
}

.image-overlay {
	position: absolute;
	bottom: 10px;
	left: 10px;
	background: rgba(255,255,255,0.8);
	padding: 2px 8px;
	border-radius: 4px;
	font-size: 14px;
	font-weight: bold;
}

.transaction-card {
	background: #fff;
	border-radius: 16px;
	padding: 16px;
	border: 1px solid #f1f5f9;
	box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
	min-width: 240px; /* Further increase width as requested */
	max-width: 100%;
}

.txn-reply-bubble {
	margin-top: 8px;
}

.confirm-card {
	background: #fff;
	border-radius: 16px;
	padding: 14px;
	border: 1px solid #f1f5f9;
	box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
	min-width: 240px;
	max-width: 100%;
}

.confirm-title {
	font-size: 14px;
	color: #0f172a;
	display: block;
	margin-bottom: 12px;
}

.confirm-item {
	display: flex;
	align-items: center;
	justify-content: space-between;
	gap: 10px;
	padding: 10px 0;
	border-top: 1px dashed #f1f5f9;
}

.confirm-item:first-of-type {
	border-top: none;
	padding-top: 0;
}

.confirm-item-main {
	flex: 1;
	min-width: 0;
}

.confirm-item-name {
	font-size: 14px;
	font-weight: bold;
	color: #0f172a;
	display: block;
}

.confirm-item-meta {
	font-size: 12px;
	color: #64748b;
	display: block;
	margin-top: 2px;
}

.confirm-actions {
	margin-top: 10px;
	display: flex;
	justify-content: flex-end;
}

.confirm-btn {
	padding: 6px 14px;
	border-radius: 8px;
	font-size: 13px;
	white-space: nowrap;
}

.confirm-btn-ok {
	background: #ffd541;
	color: #0f172a;
	font-weight: 600;
}

.confirm-btn-cancel {
	background: #f1f5f9;
	color: #64748b;
}

.confirm-resolved {
	display: block;
	margin-top: 8px;
	font-size: 12px;
	color: #94a3b8;
}

.card-body {
	display: flex;
	align-items: center;
	margin-bottom: 15px;
}

.cat-icon-wrap {
	width: 44px;
	height: 44px;
	border-radius: 50%;
	display: flex;
	align-items: center;
	justify-content: center;
	margin-right: 12px;
}

.cat-details {
	flex: 1;
}

.cat-title {
	font-size: 15px;
	font-weight: bold;
	color: #0f172a;
	display: block;
	white-space: nowrap; /* Avoid title wrapping */
}

.cat-sub {
	font-size: 12px;
	color: #64748b;
}

.amount-text {
	font-size: 18px;
	font-weight: bold;
	color: #0f172a;
	white-space: nowrap; /* Keep amount on one line */
	margin-left: 10px; /* Add some space between title and amount */
}

.card-footer {
	display: flex;
	justify-content: space-between;
	align-items: center;
	padding-top: 12px;
	border-top: 1px dashed #f1f5f9;
}

.date-text {
	font-size: 12px;
	color: #94a3b8;
}

.card-actions {
	display: flex;
	gap: 8px;
}

.action-btn-mini {
	background: #f8fafc;
	width: 32px;
	height: 32px;
	border-radius: 8px;
	display: flex;
	align-items: center;
	justify-content: center;
}

.edit-btn {
	width: auto;
	padding: 0 10px;
	gap: 4px;
}

.edit-text {
	font-size: 12px;
	color: #0f172a;
}


.typing-bubble {
	display: inline-flex;
	align-items: center;
	gap: 8px;
}

.typing-dot {
	width: 8px;
	height: 8px;
	border-radius: 50%;
	background: #94a3b8;
	opacity: 0.35;
	animation: typingPulse 1.1s infinite ease-in-out;
}

.typing-dot:nth-child(2) {
	animation-delay: 0.15s;
}

.typing-dot:nth-child(3) {
	animation-delay: 0.3s;
}

@keyframes typingPulse {
	0%, 80%, 100% {
		transform: translateY(0);
		opacity: 0.3;
	}
	40% {
		transform: translateY(-4px);
		opacity: 1;
	}
}

/* --- Bottom Interaction --- */
.bottom-panel {
	position: fixed;
	bottom: 0;
	left: 0;
	right: 0;
	z-index: 100;
	background: #fff;
	padding: 15px 15px calc(15px + constant(safe-area-inset-bottom));
	padding: 15px 15px calc(15px + env(safe-area-inset-bottom));
	border-top: 1px solid #f1f5f9;
}

.bottom-spacer {
	height: 120px; /* Enough space for the fixed panel */
}

.input-container {
	background: #f1f5f9;
	border-radius: 25px;
	display: flex;
	align-items: center;
	padding: 10px 18px;
	margin-bottom: 8px;
}

.voice-icon {
	margin-right: 12px;
}

.main-input {
	flex: 1;
	font-size: 15px;
}

/* Edit Popup Styles */
.edit-popup {
	padding: 20px;
}

.popup-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 20px;
}

.popup-title {
	font-size: 18px;
	font-weight: bold;
	color: #333;
}

.edit-form {
	display: flex;
	flex-direction: column;
	gap: 15px;
}

.form-item {
	display: flex;
	align-items: center;
	border-bottom: 1px solid #f5f5f5;
	padding: 10px 0;
}

.label {
	width: 60px;
	font-size: 14px;
	color: #666;
}

.edit-input {
	flex: 1;
	font-size: 16px;
}

.picker-val {
	font-size: 16px;
	color: #333;
}

.save-btn {
	margin-top: 20px;
	background-color: #ffd541;
	color: #0f172a;
	font-weight: bold;
	border-radius: 25px;
	border: none;
}

.bottom-tip {
	text-align: center;
	font-size: 11px;
	color: #94a3b8;
}
</style>
