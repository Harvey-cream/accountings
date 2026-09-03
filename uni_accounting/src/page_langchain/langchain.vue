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
			@scroll="handleChatScroll"
		>
			<view class="chat-list">
				<view class="top-spacer"></view>
				<view v-for="msg in messages" :key="msg.id" :class="['message-item', msg.role === 'user' ? 'user-msg' : 'ai-msg']">
					<view class="avatar">
						<image :src="msg.role === 'user' ? '/static/default_avatar.png' : '/static/logo.png'" mode="aspectFill" />
					</view>
					<view class="content-box">
													<view v-if="msg.id === streamingAiId && taskProgressVisible" class="task-progress-card">
								<view class="progress-heading"><view class="progress-heading-main"><view class="assistant-mark">鸭</view><text>正在处理你的请求</text></view><text class="progress-count">{{ completedTaskCount }}/{{ taskStates.length }}</text></view>
								<view v-for="task in taskStates" :key="task.id" class="task-row"><view :class="['task-status-icon', `task-${task.status}`]">{{ taskStatusIcon(task.status) }}</view><text class="task-label">{{ taskLabel(task) }}</text><text :class="['task-status-text', `status-${task.status}`]">{{ taskStatusText(task.status) }}</text></view>
							</view>
							<view v-if="msg.resultSummary" class="result-summary"><view class="result-summary-title"><text>✨ 本次处理完成</text><text class="result-summary-count">{{ msg.resultSummary.count }} 项任务</text></view></view>
										<view v-if="msg.type === 'text' || msg.type === 'text_image'" class="bubble">
										<AnalysisRenderer
							v-if="msg.analysis_view && hasAnalysisView(msg.analysis_view)"
							:analysis-view="msg.analysis_view"
							:fallback-text="displayText(msg)"
						/>
						<view v-else-if="msg.content" class="ai-text-renderer">
							<template v-for="(block, bidx) in renderAIBlocks(msg)" :key="`${msg.id}-block-${bidx}`">
								<view v-if="block.type === 'paragraph'" class="ai-paragraph">
									<text class="ai-paragraph-text">{{ block.text }}</text>
								</view>
								<view v-else-if="block.type === 'section'" class="ai-section">
									<text v-if="block.title" class="ai-section-title">{{ block.title }}</text>
									<view v-for="(item, i) in block.items" :key="i" class="ai-section-item">
										<text class="ai-section-index">{{ item.index }}</text>
										<text class="ai-section-text">{{ item.text }}</text>
									</view>
								</view>
								<view v-else-if="block.type === 'list'" class="ai-list">
									<view v-for="(item, i) in block.items" :key="i" class="ai-list-item">
										<text class="ai-list-bullet">{{ item.bullet }}</text>
										<text class="ai-list-text">{{ item.text }}</text>
									</view>
								</view>
							</template>
						</view>
						<text v-if="!msg.content && streamingAiId === msg.id && streamingStatus && !taskProgressVisible" class="streaming-hint">{{ streamingStatus }}<text class="processing-dots">{{ processingDots }}</text></text>
						<view v-else-if="!msg.content && streamingAiId === msg.id && !taskProgressVisible" class="typing-bubble">
							<view class="typing-dot"></view>
							<view class="typing-dot"></view>
							<view class="typing-dot"></view>
						</view>
					</view>
<view v-if="msg.type === 'text_image'" class="image-box">
							<image :src="msg.image" mode="widthFix" class="content-image" />
							<view class="image-overlay">鸭了个鸭?</view>
						</view>
						<view v-if="msg.type === 'transaction'" class="transaction-card result-card">
								<view class="result-card-label">🍜 账单</view>
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
						<view v-if="false" class="bubble txn-reply-bubble">
							<text class="text-content">{{ displayText(msg) }}</text>
						</view>
						<view v-if="msg.type === 'budget'" class="budget-card">
								<view class="result-card-label">💰 本月预算</view>
							<view class="budget-head">
								<text class="budget-title">预算已更新</text>
								<text class="budget-type">{{ msg.budget_type }}</text>
							</view>
							<view class="budget-amount-row">
								<text class="budget-amount">{{ msg.amount }} 元</text>
							</view>
							<view class="budget-meta-row">
								<text class="budget-meta">{{ msg.category }}</text>
								<text class="budget-meta">{{ msg.period }}</text>
							</view>
							<view v-if="false" class="bubble txn-reply-bubble">
								<text class="text-content">{{ displayText(msg) }}</text>
							</view>
						</view>
						<view v-if="msg.type === 'confirm'" :class="['confirm-card', { 'confirm-card-resolved': msg.resolved }]">
							<view class="confirm-card-header">
								<view class="confirm-card-heading"><view class="confirm-badge">记账</view><text class="confirm-card-title">请确认这笔记账</text></view>
								<text v-if="msg.resolved" class="confirm-resolved-badge">已处理</text>
							</view>
							<text v-if="msg.content" class="confirm-title">{{ displayText(msg) }}</text>
							<template v-if="msg.confirmations && msg.confirmations.length">
								<view v-for="(conf, cidx) in msg.confirmations" :key="`${msg.id}-conf-${cidx}`" class="confirm-group">
									<text class="confirm-group-title">{{ confirmationGroupTitle(conf) }}</text>
									<template v-if="confirmCandidates(conf.candidates).length">
										<view v-for="(item, i) in confirmCandidates(conf.candidates)" :key="item.id || `${cidx}-${i}`" class="confirm-item">
											<view class="confirm-item-main">
												<text class="confirm-item-name">{{ confirmItemName(conf, item) }}</text>
												<text class="confirm-item-meta">{{ confirmItemMeta(conf, item) }}</text>
											</view>
											<text v-if="confirmItemAmount(conf, item)" :class="['confirm-item-amount', confirmAmountClass(item)]">{{ confirmItemAmount(conf, item) }}</text>
										</view>
									</template>
									<view v-else-if="conf.payload" class="confirm-item budget-preview-item">
										<view class="confirm-item-main">
											<text class="confirm-item-name">{{ confirmBudgetName(conf.payload) }}</text>
											<text class="confirm-item-meta">{{ confirmBudgetMeta(conf.payload) }}</text>
										</view>
									</view>
								</view>
							</template>
							<template v-else>
								<view
									v-for="(item, i) in confirmCandidates(msg.candidates)"
									:key="item.id || i"
									class="confirm-item"
								>
									<view class="confirm-item-main">
										<text class="confirm-item-name">{{ confirmItemName(msg, item) }}</text>
										<text class="confirm-item-meta">{{ confirmItemMeta(msg, item) }}</text>
									</view>
								</view>
							</template>
							<view v-if="!msg.resolved" class="confirm-actions">
								<view class="confirm-btn confirm-btn-ok" @click="handleConfirmAction(msg, true)">确认{{ actionLabel(confirmPrimaryAction(msg)) }}</view>
								<view class="confirm-btn confirm-btn-cancel" @click="handleConfirmAction(msg, false)">取消</view>
							</view>
							<text v-else class="confirm-resolved">已处理</text>
						</view>
					</view>
				</view>
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
import { ref, computed, onMounted, onBeforeUnmount, nextTick, getCurrentInstance } from 'vue';
import { getLangchainChat, sendLangchainChat, deleteBill, updateBill } from '@/api/api.js';
import { isLangchainStreamSupported, sendLangchainChatStream } from '@/utils/langchain_stream.js';
import AnalysisRenderer from './AnalysisRenderer.vue';

const goToManual = () => {
	uni.navigateBack();
};

const messages = ref([]);
const inputValue = ref('');
const loading = ref(false);
const streamingAiId = ref(null);
const streamingStatus = ref('');
const processingDots = ref('');
let processingTimer = null;
const startProcessingDots = () => {
	if (processingTimer) clearInterval(processingTimer);
	let count = 0;
	processingDots.value = '';
	processingTimer = setInterval(() => {
		count = (count + 1) % 4;
		processingDots.value = '.'.repeat(count);
	}, 420);
};
const stopProcessingDots = () => {
	if (processingTimer) clearInterval(processingTimer);
	processingTimer = null;
	processingDots.value = '';
};
const taskStates = ref([]);
const userNearBottom = ref(true);
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

const taskProgressVisible = computed(() => taskStates.value.length > 0);
const completedTaskCount = computed(() => taskStates.value.filter((task) => task.status === 'success').length);
const TASK_LABELS = { bill: '账单', budget: '本月预算', asset: '资产账户', invoice: '发票信息', open_planning: '消费分析' };
const taskLabel = (task) => TASK_LABELS[task?.kind] || TASK_LABELS[task?.id] || '当前任务';
const taskStatusIcon = (status) => ({ pending: '○', running: '◌', success: '✓', failed: '!' }[status] || '○');
const taskStatusText = (status) => ({ pending: '等待处理', running: '处理中…', success: '已完成', failed: '处理失败' }[status] || '等待处理');

const updateTaskState = (event) => {
	const taskId = event?.task_id;
	if (!taskId || !event?.event_type?.startsWith('task.')) return;
	const status = { 'task.started': 'running', 'task.completed': 'success', 'task.failed': 'failed' }[event.event_type];
	if (!status) return;
	const index = taskStates.value.findIndex((task) => task.id === taskId);
	if (index < 0) taskStates.value.push({ id: taskId, kind: event.agent || taskId, status });
	else taskStates.value[index] = { ...taskStates.value[index], kind: event.agent || taskStates.value[index].kind, status };
};

const resetRequestState = () => {
	taskStates.value = [];
	userNearBottom.value = true;
};

const isLongText = (msg) => (msg?.content || '').length > 420;
const toggleExpanded = (msg) => { msg.expanded = !msg.expanded; };

const handleChatScroll = (event) => {
	const detail = event?.detail || {};
	userNearBottom.value = detail.scrollHeight - detail.scrollTop - detail.clientHeight < 100;
};

const getMessageText = (msg) => {
	const text = msg?.content || '';
	return String(text);
};

const normalizeLines = (text) => String(text || '').replace(/\r\n/g, '\n').replace(/\r/g, '\n');

const normalizeBulletText = (line) => String(line || '').replace(/^[-*•·]\s*/, '').trim();

const isSectionTitle = (line) => {
	const value = String(line || '').trim();
	if (!value) return false;
	if (/^[一二三四五六七八九十]+[、\.．]\s*.+/.test(value)) return true;
	if (/^[A-Za-z][\w\s-]{1,28}:?$/.test(value) && /[A-Za-z]/.test(value)) return true;
	return /^[一-龥]{2,12}$/.test(value) && !/[。！？；：,，]/.test(value);
};

const hasAnalysisView = (value) => {
	if (!value || typeof value !== 'object') return false;
	const summary = value.summary && typeof value.summary === 'object' ? String(value.summary.text || '').trim() : '';
	const sections = Array.isArray(value.sections) ? value.sections : [];
	return Boolean(summary || sections.length);
};

const parseAIText = (input) => {
	const text = normalizeLines(input).trim();
	if (!text) return [];
	return [{ type: 'paragraph', text }];
};

const toChineseOrdinal = (n) => {
	const map = ['①', '②', '③', '④', '⑤', '⑥', '⑦', '⑧', '⑨', '⑩'];
	return map[n - 1] || `${n}.`;
};

const renderAIBlocks = (msg) => {
	const text = getMessageText(msg);
	const blocks = parseAIText(text);
	return blocks.length ? blocks : [{ type: 'paragraph', text }];
};

const displayText = (msg) => getMessageText(msg);

const applyDoneMessages = (aiId, event) => {
	const aiMsgs = (event.data || []).filter((m) => m.role === 'ai');
	const idx = messages.value.findIndex((m) => m.id === aiId);
	if (idx < 0) return;
	const streamed = messages.value[idx].content;
	const [primary, ...rest] = aiMsgs;
	if (primary) {
		const formatted = formatMessage(primary);
		if (formatted.type === 'text' || formatted.type === 'text_image') {
			formatted.content = streamed || formatted.content;
		}
		messages.value[idx] = formatted;
	} else {
		messages.value.splice(idx, 1);
	}
	rest.forEach((m, offset) => {
		messages.value.splice(idx + 1 + offset, 0, formatMessage(m));
	});
};

const showEdit = ref(false);
const currentMsg = ref(null);
const editForm = ref({
	amount: '',
	remark: '',
	date: ''
});

const openEdit = (msg) => {
	currentMsg.value = msg;
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
		content: msg.content || '',
		image: msg.image_url
	};

	if (msg.extra_data) {
		const extra = typeof msg.extra_data === 'string'
			? (() => {
				try { return JSON.parse(msg.extra_data); } catch (e) { return {}; }
			})()
			: (msg.extra_data || {});
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

const confirmPrimaryAction = (msg) => {
	if (msg?.action) return msg.action;
	if (msg?.confirmations?.length) return msg.confirmations[0]?.action || 'update';
	return 'update';
};

const isTargetlessConfirm = (msg) => {
	const entity = msg?.entity || 'bill';
	return (entity === 'bill' && msg?.action === 'batch_create')
		|| (entity === 'asset' && msg?.action === 'create')
		|| entity === 'budget';
};

const formatMoney = (n) => (n % 1 === 0 ? String(n) : n.toFixed(2));

const formatConfirmAmount = (item) => {
	const n = Number(item?.amount);
	if (Number.isNaN(n)) return '';
	const prefix = (item?.type || item?.bill_type) === 'income' ? '+' : '-';
	return `${prefix}${formatMoney(n)}元`;
};

const confirmationGroupTitle = (conf) => {
	if (conf?.entity === 'budget') return '预算调整';
	if (conf?.entity === 'asset') return '资产变更';
	if (conf?.entity === 'invoice') return '发票操作';
	return '账单确认';
};

const confirmCandidates = (candidates) => {
	if (Array.isArray(candidates)) return candidates;
	if (!candidates || typeof candidates !== 'object') return [];
	if (Array.isArray(candidates.item)) return candidates.item;
	return Object.values(candidates).find(Array.isArray) || [];
};

const confirmItemName = (msg, item) => {
	const entity = msg?.entity || 'bill';
	if (entity === 'asset') return item.name || '账户';
	if (entity === 'invoice') return item.name || '发票抬头';
	if (entity === 'budget') return item.category || '预算';
	return item.remark || item.description || item.category || '账单';
};

const confirmItemMeta = (msg, item) => {
	const entity = msg?.entity || 'bill';
	if (entity === 'asset') {
		const n = Number(item.balance);
		return [item.asset_type, Number.isNaN(n) ? '' : `${formatMoney(n)}元`].filter(Boolean).join(' · ');
	}
	if (entity === 'invoice') return item.tax_id || '';
	if (entity === 'budget') {
		const amount = Number(item.amount);
		return [item.period, item.budget_type, Number.isNaN(amount) ? '' : `${formatMoney(amount)}元`].filter(Boolean).join(' · ');
	}
	return [item.date].filter(Boolean).join(' · ');
};

const confirmItemAmount = (msg, item) => {
	const entity = msg?.entity || 'bill';
	if (entity !== 'bill') return '';
	return formatConfirmAmount(item);
};
const confirmAmountClass = (item) => (item?.type || item?.bill_type) === 'income' ? 'amount-income' : 'amount-expense';
const confirmTotal = (msg) => {
	const groups = msg?.confirmations?.length ? msg.confirmations : [{ candidates: msg?.candidates || [], entity: msg?.entity }];
	const amounts = groups.flatMap((group) => confirmCandidates(group.candidates).map((item) => Number(item?.amount)))
		.filter((amount) => Number.isFinite(amount));
	if (!amounts.length || (msg?.entity || 'bill') !== 'bill') return '';
	return `-${formatMoney(amounts.reduce((sum, amount) => sum + amount, 0))}元`;
};

const confirmBudgetName = (payload) => payload?.category || (payload?.is_total ? '总预算' : '预算');
const confirmBudgetMeta = (payload) => {
	const amount = Number(payload?.amount);
	return [payload?.period, payload?.budget_type === 'year' ? '年预算' : '月预算', Number.isNaN(amount) ? '' : `${formatMoney(amount)}元`].filter(Boolean).join(' · ');
};

const markConfirmResolved = (msg) => {
	const idx = messages.value.findIndex((m) => m.id === msg.id);
	if (idx >= 0) {
		messages.value[idx] = { ...messages.value[idx], resolved: true };
	}
};

const handleConfirmAction = async (msg, ok) => {
	if (loading.value || msg.resolved) return;
	const primary = msg?.confirmations?.[0] || msg;
	const extra = ok
		? {
			confirm: true,
			entity: primary?.entity || msg.entity || 'bill',
			action: primary?.action || msg.action,
			message_id: msg.id
		}
		: { confirm: false, message_id: msg.id };
	if (ok && !extra.action) {
		return uni.showToast({ title: '缺少确认信息', icon: 'none' });
	}

	const content = ok ? `确认${actionLabel(extra.action)}` : '取消';
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
		resetRequestState();
		streamingAiId.value = aiId;
		streamingStatus.value = '';
		startProcessingDots();
		messages.value.push({ id: aiId, role: 'ai', type: 'text', content: '' });
		try {
			await sendLangchainChatStream(content, {
				onStatus: (text) => {
					if (streamingAiId.value === aiId) streamingStatus.value = text;
					scrollToBottomThrottled();
				},
				onAgentEvent: (event) => {
					updateTaskState(event);
					if (streamingAiId.value === aiId && event?.message) streamingStatus.value = event.message;
					scrollToBottomThrottled();
				},
				onToken: (text) => {
					const idx = messages.value.findIndex((m) => m.id === aiId);
					if (idx < 0) return;
					if (streamingStatus.value) streamingStatus.value = '';
					const prev = messages.value[idx].content || '';
					patchAiMessage(aiId, { content: prev + text });
					scrollToBottomThrottled();
				},
				onDone: (event) => {
					streamingAiId.value = null;
					streamingStatus.value = '';
					stopProcessingDots();
					applyDoneMessages(aiId, event);
					scrollToBottom();
				},
				onError: () => {
					streamingAiId.value = null;
					streamingStatus.value = '';
					stopProcessingDots();
					uni.showToast({ title: '发送失败', icon: 'none' });
				}
			}, extra);
		} catch (e) {
			streamingAiId.value = null;
			streamingStatus.value = '';
			stopProcessingDots();
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

	if (isLangchainStreamSupported()) {
		const aiId = `local-ai-${Date.now()}`;
		resetRequestState();
		streamingAiId.value = aiId;
		streamingStatus.value = '';
		startProcessingDots();
		messages.value.push({ id: aiId, role: 'ai', type: 'text', content: '' });
		try {
			await sendLangchainChatStream(content, {
				onStatus: (text) => {
					if (streamingAiId.value === aiId) streamingStatus.value = text;
					scrollToBottomThrottled();
				},
				onAgentEvent: (event) => {
					updateTaskState(event);
					if (streamingAiId.value === aiId && event?.message) streamingStatus.value = event.message;
					scrollToBottomThrottled();
				},
				onToken: (text) => {
					const idx = messages.value.findIndex((m) => m.id === aiId);
					if (idx < 0) return;
					if (streamingStatus.value) streamingStatus.value = '';
					const prev = messages.value[idx].content || '';
					patchAiMessage(aiId, { content: prev + text });
					scrollToBottomThrottled();
				},
				onDone: (event) => {
					streamingAiId.value = null;
					streamingStatus.value = '';
					stopProcessingDots();
					applyDoneMessages(aiId, event);
					scrollToBottom();
				},
				onError: () => {
					streamingAiId.value = null;
					streamingStatus.value = '';
					stopProcessingDots();
					uni.showToast({ title: '发送失败', icon: 'none' });
				}
			});
		} catch (e) {
			streamingAiId.value = null;
			streamingStatus.value = '';
			stopProcessingDots();
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
	if (!userNearBottom.value) return;
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

onBeforeUnmount(() => {
	stopProcessingDots();
	if (scrollRaf) cancelAnimationFrame(scrollRaf);
});

onMounted(() => {
	fetchHistory();
});
</script>

<style scoped>
.ai-page {
	display: flex;
	flex-direction: column;
	height: 100vh;
	background: #fff;
	position: relative;
}

.top-section {
	position: fixed;
	top: 0;
	left: 0;
	right: 0;
	z-index: 100;
	background-color: #ffd541;
	padding: 14px 20px 10px;
	display: flex;
	flex-direction: column;
}

.top-spacer {
	height: 100px;
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


.ai-text-renderer {
	display: flex;
	flex-direction: column;
	gap: 10px;
}

.ai-paragraph {
	display: block;
}

.ai-paragraph-text {
	display: block;
	font-size: 15px;
	line-height: 1.7;
	color: #334155;
	white-space: pre-wrap;
	word-break: break-word;
	overflow-wrap: anywhere;
}

.ai-section {
	display: flex;
	flex-direction: column;
	gap: 8px;
	padding: 4px 0;
}

.ai-section + .ai-section {
	margin-top: 4px;
	padding-top: 12px;
	border-top: 1px solid #e2e8f0;
}

.ai-section-title {
	display: block;
	font-size: 16px;
	font-weight: 700;
	line-height: 1.45;
	color: #0f172a;
}

.ai-section-item,
.ai-list-item {
	display: flex;
	align-items: flex-start;
	gap: 8px;
}

.ai-section-index {
	flex: 0 0 auto;
	min-width: 22px;
	font-size: 14px;
	line-height: 1.7;
	font-weight: 700;
	color: #f59e0b;
}

.ai-section-text,
.ai-list-text {
	flex: 1;
	min-width: 0;
	font-size: 14px;
	line-height: 1.7;
	color: #334155;
	word-break: break-word;
	overflow-wrap: anywhere;
}

.ai-list {
	display: flex;
	flex-direction: column;
	gap: 6px;
}

.ai-list-bullet {
	flex: 0 0 auto;
	min-width: 16px;
	font-size: 16px;
	line-height: 1.6;
	color: #64748b;
}

.expand-action {
	display: flex;
	align-items: center;
	justify-content: center;
	gap: 4px;
	margin-top: 12px;
	padding-top: 10px;
	border-top: 1px solid #e2e8f0;
	font-size: 13px;
	color: #64748b;
}

.streaming-hint {
	font-size: 15px;
	line-height: 1.5;
	color: #94a3b8;
}

.processing-dots {
	display: inline-block;
	min-width: 18px;
	color: #f0b429;
	letter-spacing: 2px;
}

.task-progress-card {
	padding: 14px 16px;
	margin-bottom: 8px;
	background: #fff;
	border: 1px solid #e2e8f0;
	border-radius: 16px;
	box-shadow: 0 5px 18px rgba(15, 23, 42, 0.06);
	animation: taskFadeIn 0.25s ease-out;
}

.progress-heading, .progress-heading-main, .task-row, .streaming-label, .result-summary-title {
	display: flex;
	align-items: center;
}

.progress-heading { justify-content: space-between; margin-bottom: 12px; }
.progress-heading-main { gap: 8px; font-size: 14px; font-weight: 600; color: #1e293b; }
.assistant-mark { width: 24px; height: 24px; display: flex; align-items: center; justify-content: center; border-radius: 8px; background: #fff2b8; color: #8a6500; font-size: 12px; }
.progress-count { font-size: 12px; color: #94a3b8; }
.task-row { min-height: 28px; gap: 9px; }
.task-status-icon { width: 18px; height: 18px; display: flex; align-items: center; justify-content: center; border-radius: 50%; font-size: 12px; font-weight: 600; }
.task-pending { color: #94a3b8; background: #f1f5f9; }
.task-running { color: #b7791f; background: #fff7db; animation: softPulse 1.8s ease-in-out infinite; }
.task-success { color: #16805b; background: #dcfce7; animation: taskDone 0.25s ease-out; }
.task-failed { color: #c2413b; background: #fee2e2; }
.task-label { flex: 1; font-size: 13px; color: #334155; }
.task-status-text { font-size: 12px; }
.status-pending { color: #94a3b8; }
.status-running { color: #b7791f; }
.status-success { color: #16805b; }
.status-failed { color: #c2413b; }
.streaming-label { gap: 7px; color: #64748b; font-size: 14px; }
.status-pulse { width: 7px; height: 7px; border-radius: 50%; background: #f0b429; animation: softPulse 1.6s ease-in-out infinite; }
.result-summary { padding: 13px 15px; margin-bottom: 8px; border-radius: 14px; background: #f0fdf4; border: 1px solid #bbf7d0; }
.result-summary-title { justify-content: space-between; color: #166534; font-size: 15px; font-weight: 600; }
.result-summary-count { color: #4d7c5c; font-size: 12px; font-weight: 400; }

@keyframes taskFadeIn { from { opacity: 0; transform: translateY(5px); } to { opacity: 1; transform: translateY(0); } }
@keyframes taskDone { from { transform: scale(0.85); } to { transform: scale(1); } }
@keyframes softPulse { 0%, 100% { opacity: .65; } 50% { opacity: 1; } }

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

.budget-card,
.transaction-card,
.confirm-card {
	background: #fff;
	border-radius: 16px;
	padding: 16px;
	border: 1px solid #f1f5f9;
	box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
	min-width: 240px;
	max-width: 100%;
}

.result-card-label {
	padding-bottom: 11px;
	margin-bottom: 12px;
	border-bottom: 1px solid #f1f5f9;
	font-size: 14px;
	font-weight: 600;
	color: #334155;
}

.budget-card {
	background: linear-gradient(180deg, #fffdf5 0%, #fff7db 100%);
	border-color: #fde7a4;
	box-shadow: 0 4px 15px rgba(245, 158, 11, 0.08);
}

.budget-head,
.card-footer,
.confirm-actions {
	display: flex;
	justify-content: space-between;
	align-items: center;
}

.budget-head {
	margin-bottom: 10px;
}

.budget-title,
.cat-title,
.confirm-item-name,
.confirm-group-title {
	font-size: 15px;
	font-weight: bold;
	color: #0f172a;
}

.budget-title {
	color: #92400e;
}

.budget-type {
	font-size: 12px;
	color: #b45309;
	background: rgba(245, 158, 11, 0.12);
	padding: 3px 8px;
	border-radius: 999px;
}

.budget-amount-row,
.txn-reply-bubble {
	margin-top: 8px;
}

.budget-amount {
	font-size: 24px;
	font-weight: bold;
	color: #111827;
}

.budget-meta-row {
	display: flex;
	gap: 10px;
	flex-wrap: wrap;
}

.budget-meta,
.confirm-item-meta,
.date-text,
.confirm-resolved {
	font-size: 12px;
	color: #64748b;
}

.confirm-card {
	background: #fffdf7;
	border-color: #fde7a4;
}

.confirm-card-header {
	display: flex;
	align-items: flex-start;
	justify-content: space-between;
	gap: 10px;
	padding-bottom: 12px;
	margin-bottom: 4px;
	border-bottom: 1px solid #f8edc5;
}

.confirm-card-heading {
	display: flex;
	align-items: flex-start;
	gap: 10px;
	min-width: 0;
}

.confirm-badge {
	flex: 0 0 auto;
	padding: 5px 8px;
	border-radius: 8px;
	background: #ffd541;
	color: #6b4f00;
	font-size: 12px;
	font-weight: 700;
}

.confirm-card-title {
	display: block;
	margin-bottom: 4px;
	color: #1e293b;
	font-size: 15px;
	font-weight: 700;
}

.confirm-resolved-badge {
	flex: 0 0 auto;
	padding: 4px 8px;
	border-radius: 999px;
	background: #dcfce7;
	color: #16805b;
	font-size: 12px;
}

.confirm-card-resolved {
	background: #fafafa;
	border-color: #e2e8f0;
}

.confirm-item-amount,
.confirm-total-amount {
		flex: 0 0 auto;
		font-size: 15px;
		font-weight: 700;
		white-space: nowrap;
}

.amount-expense { color: #c2413b; }
.amount-income { color: #16805b; }

.confirm-total {
	display: flex;
	align-items: center;
	justify-content: space-between;
	margin-top: 8px;
	padding-top: 12px;
	border-top: 1px solid #f8edc5;
	color: #64748b;
	font-size: 13px;
}

.confirm-actions {
	gap: 10px;
	margin-top: 14px;
}

.confirm-actions .confirm-btn {
	min-height: 40px;
	flex: 1;
	display: flex;
	align-items: center;
	justify-content: center;
	box-sizing: border-box;
}

.confirm-btn-ok { order: 2; }
.confirm-btn-cancel { order: 1; }

.confirm-item-main,
.cat-details {
	flex: 1;
	min-width: 0;
}

.confirm-item-name,
.confirm-item-meta {
	display: block;
	overflow-wrap: anywhere;
}

.confirm-title {
	font-size: 14px;
	color: #0f172a;
	display: block;
	margin-bottom: 12px;
}

.confirm-group + .confirm-group {
	margin-top: 12px;
	padding-top: 12px;
	border-top: 1px dashed #f1f5f9;
}

.confirm-group-title {
	display: block;
	font-size: 13px;
	margin-bottom: 8px;
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

.confirm-item-main,
.cat-details {
	flex: 1;
	min-width: 0;
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
	box-shadow: 0 3px 8px rgba(245, 158, 11, 0.16);
}

.confirm-btn-cancel {
	background: #f1f5f9;
	color: #64748b;
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

.cat-sub {
	font-size: 12px;
	color: #64748b;
}

.amount-text {
	font-size: 18px;
	font-weight: bold;
	color: #0f172a;
	white-space: nowrap;
	margin-left: 10px;
}

.card-footer {
	padding-top: 12px;
	border-top: 1px dashed #f1f5f9;
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
	height: 120px;
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

@media (max-width: 375px) {
	.chat-list { padding: 12px 10px; }
	.message-item { max-width: 96%; margin-bottom: 16px; }
	.content-box { max-width: calc(100% - 46px); }
	.bubble, .budget-card, .transaction-card, .confirm-card { padding: 13px; min-width: 0; }
	.amount-text { font-size: 16px; }
	.confirm-actions { gap: 8px; }
	.confirm-btn { flex: 1; text-align: center; padding-left: 8px; padding-right: 8px; }
	.confirm-item { align-items: flex-start; }
	.confirm-item-amount { font-size: 14px; }
}

.save-btn {
	margin-top: 20px;
	background-color: #ffd541;
	color: #0f172a;
	font-weight: bold;
	border-radius: 25px;
	border: none;
}

@media (prefers-reduced-motion: reduce) {
	.task-progress-card, .task-success, .task-running, .status-pulse, .typing-dot { animation: none; }
}
</style>
