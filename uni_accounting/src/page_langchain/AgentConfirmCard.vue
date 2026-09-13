<template>
	<view :class="['confirm-card', { 'confirm-card-resolved': msg.resolved }]">
		<view class="confirm-card-header">
			<view class="confirm-card-heading">
				<view class="confirm-badge">{{ headerMeta.badge }}</view>
				<text class="confirm-card-title">{{ headerMeta.title }}</text>
			</view>
			<text v-if="msg.resolved" class="confirm-resolved-badge">已处理</text>
		</view>

		<view v-for="(group, gidx) in groups" :key="gidx" class="confirm-group">
			<view v-if="isMulti" class="confirm-group-head">
				<view class="confirm-badge">{{ groupMeta(group).badge }}</view>
				<text class="confirm-group-title">{{ groupMeta(group).title }}</text>
			</view>
			<template v-if="candidatesOf(group).length">
				<view v-for="(item, i) in candidatesOf(group)" :key="item.id || `${gidx}-${i}`" class="confirm-item">
					<view class="confirm-item-main">
						<text class="confirm-item-name">{{ itemName(group, item) }}</text>
						<text class="confirm-item-meta">{{ itemMeta(group, item) }}</text>
					</view>
					<text v-if="itemAmount(group, item)" :class="['confirm-item-amount', amountClass(item)]">{{ itemAmount(group, item) }}</text>
				</view>
			</template>
			<template v-else-if="payloadFields(group).length">
				<view v-for="(f, i) in payloadFields(group)" :key="`${gidx}-field-${i}`" class="confirm-field">
					<text class="confirm-field-label">{{ f.label }}</text>
					<text class="confirm-field-value">{{ f.value }}</text>
				</view>
			</template>
		</view>

		<view v-if="!msg.resolved" class="confirm-actions">
			<view class="confirm-btn confirm-btn-ok" @click="$emit('confirm')">{{ confirmButtonText }}</view>
			<view class="confirm-btn confirm-btn-cancel" @click="$emit('cancel')">取消</view>
		</view>
		<text v-else class="confirm-resolved">已处理</text>
	</view>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
	msg: { type: Object, required: true },
});
defineEmits(['confirm', 'cancel']);

// ---- entity + action → 展示元数据（Registry，未知类型兜底） ----
const CONFIRM_META = {
	'bill:create': { badge: '记账', title: '请确认这笔记账', confirmText: '确认记账' },
	'bill:batch_create': { badge: '记账', title: '请确认批量记账', confirmText: '确认记账' },
	'bill:update': { badge: '账单', title: '请确认修改账单', confirmText: '确认修改' },
	'bill:delete': { badge: '账单', title: '请确认删除账单', confirmText: '确认删除' },
	'budget:set_budget': { badge: '预算', title: '请确认调整预算', confirmText: '确认调整' },
	'budget:update': { badge: '预算', title: '请确认调整预算', confirmText: '确认调整' },
	'asset:create': { badge: '资产', title: '请确认创建资产', confirmText: '确认创建' },
	'asset:update': { badge: '资产', title: '请确认修改资产', confirmText: '确认修改' },
	'asset:delete': { badge: '资产', title: '请确认删除资产', confirmText: '确认删除' },
	'asset:adjust_balance': { badge: '资产', title: '请确认调整余额', confirmText: '确认调整' },
	'invoice:create': { badge: '发票', title: '请确认创建发票', confirmText: '确认创建' },
	'invoice:update': { badge: '发票', title: '请确认修改发票', confirmText: '确认修改' },
	'invoice:delete': { badge: '发票', title: '请确认删除发票', confirmText: '确认删除' },
};
const DEFAULT_META = { badge: '操作确认', title: '请确认这项操作', confirmText: '确认' };

const metaFor = (entity, action) =>
	CONFIRM_META[`${entity}:${action}`] || { ...DEFAULT_META, badge: entity || DEFAULT_META.badge };

const groupMeta = (group) => metaFor(group?.entity, group?.action);

// 兼容 confirmations 数组 或 单个确认
const groups = computed(() => {
	const confs = props.msg?.confirmations;
	if (Array.isArray(confs) && confs.length) {
		return confs.map((c) => ({
			entity: c?.entity || props.msg?.entity,
			action: c?.action || props.msg?.action,
			candidates: c?.candidates,
			payload: c?.payload,
		}));
	}
	return [
		{
			entity: props.msg?.entity,
			action: props.msg?.action,
			candidates: props.msg?.candidates,
			payload: props.msg?.payload,
		},
	];
});

const isMulti = computed(() => groups.value.length > 1);
const headerMeta = computed(() =>
	isMulti.value ? { badge: DEFAULT_META.badge, title: '请确认以下操作' } : groupMeta(groups.value[0])
);
const confirmButtonText = computed(() => (isMulti.value ? DEFAULT_META.confirmText : headerMeta.value.confirmText));

// ---- 数值 / 字符串小工具 ----
const formatMoney = (v) => {
	const n = Number(v);
	if (Number.isNaN(n)) return '';
	return n % 1 === 0 ? String(n) : n.toFixed(2);
};
const money = (v) => {
	const s = formatMoney(v);
	return s ? `${s}元` : '';
};
const signedMoney = (v, billType) => {
	const s = formatMoney(v);
	return s ? `${billType === 'income' ? '+' : '-'}${s}元` : '';
};
const budgetTypeLabel = (t) => (t === 'year' ? '年预算' : t === 'month' ? '月预算' : '');

const candidatesOf = (group) => {
	const c = group?.candidates;
	if (Array.isArray(c)) return c;
	if (!c || typeof c !== 'object') return [];
	if (Array.isArray(c.item)) return c.item;
	return Object.values(c).find(Array.isArray) || [];
};

// ---- 候选列表字段：entity → { name, meta, amount } ----
const CANDIDATE_FIELDS = {
	bill: {
		name: (i) => i?.remark || i?.description || i?.category || '账单',
		meta: (i) => [i?.date].filter(Boolean).join(' · '),
		amount: (i) => signedMoney(i?.amount, i?.type || i?.bill_type),
	},
	budget: {
		name: (i) => i?.category || '预算',
		meta: (i) => [i?.period, budgetTypeLabel(i?.budget_type), money(i?.amount)].filter(Boolean).join(' · '),
		amount: () => '',
	},
	asset: {
		name: (i) => i?.name || '账户',
		meta: (i) => [i?.asset_type, money(i?.balance)].filter(Boolean).join(' · '),
		amount: () => '',
	},
	invoice: {
		name: (i) => i?.name || '发票抬头',
		meta: (i) => i?.tax_id || '',
		amount: () => '',
	},
};

// ---- payload 兜底字段：entity → (payload) => [{ label, value }] ----
const PAYLOAD_FIELDS = {
	bill: (p) => [
		p.amount != null && { label: '金额', value: signedMoney(p.amount, p.bill_type) },
		p.category && { label: '分类', value: p.category },
		p.date && { label: '日期', value: p.date },
		p.description && { label: '备注', value: p.description },
	].filter(Boolean),
	budget: (p) => [
		p.category && { label: '分类', value: p.category },
		p.amount != null && { label: '金额', value: money(p.amount) },
		p.period && { label: '周期', value: p.period },
	].filter(Boolean),
	asset: (p) => [
		p.name && { label: '名称', value: p.name },
		p.asset_type && { label: '类型', value: p.asset_type },
		p.balance != null && { label: '余额', value: money(p.balance) },
	].filter(Boolean),
	invoice: (p) => [
		p.name && { label: '抬头', value: p.name },
		p.tax_id && { label: '税号', value: p.tax_id },
		p.amount != null && { label: '金额', value: money(p.amount) },
	].filter(Boolean),
};

const pick = (registry, entity) => registry[entity] || registry.bill;
const itemName = (group, item) => pick(CANDIDATE_FIELDS, group?.entity).name(item);
const itemMeta = (group, item) => pick(CANDIDATE_FIELDS, group?.entity).meta(item);
const itemAmount = (group, item) => pick(CANDIDATE_FIELDS, group?.entity).amount(item);
const amountClass = (item) => ((item?.type || item?.bill_type) === 'income' ? 'amount-income' : 'amount-expense');
const payloadFields = (group) =>
	group?.payload && typeof group.payload === 'object'
		? pick(PAYLOAD_FIELDS, group?.entity)(group.payload)
		: [];
</script>

<style scoped>
.confirm-card {
	background: #fffdf7;
	border: 1px solid #fde7a4;
	border-radius: 16px;
	padding: 16px;
	box-shadow: 0 4px 15px rgba(245, 158, 11, 0.08);
	min-width: 240px;
	max-width: 100%;
}

.confirm-card-resolved {
	background: #fafafa;
	border-color: #e2e8f0;
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

.confirm-group + .confirm-group {
	margin-top: 12px;
	padding-top: 12px;
	border-top: 1px dashed #f8edc5;
}

.confirm-group-head {
	display: flex;
	align-items: center;
	gap: 8px;
	margin-bottom: 6px;
}

.confirm-group-title {
	font-size: 13px;
	font-weight: 700;
	color: #0f172a;
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
	padding-top: 4px;
}

.confirm-item-main {
	flex: 1;
	min-width: 0;
}

.confirm-item-name {
	display: block;
	font-size: 15px;
	font-weight: bold;
	color: #0f172a;
	overflow-wrap: anywhere;
}

.confirm-item-meta {
	display: block;
	font-size: 12px;
	color: #64748b;
	overflow-wrap: anywhere;
}

.confirm-item-amount {
	flex: 0 0 auto;
	font-size: 15px;
	font-weight: 700;
	white-space: nowrap;
}

.amount-expense { color: #c2413b; }
.amount-income { color: #16805b; }

.confirm-field {
	display: flex;
	align-items: center;
	justify-content: space-between;
	gap: 10px;
	padding: 8px 0;
	border-top: 1px dashed #f1f5f9;
}

.confirm-field:first-of-type {
	border-top: none;
	padding-top: 4px;
}

.confirm-field-label {
	font-size: 13px;
	color: #64748b;
	flex: 0 0 auto;
}

.confirm-field-value {
	font-size: 14px;
	font-weight: 600;
	color: #0f172a;
	text-align: right;
	overflow-wrap: anywhere;
}

.confirm-actions {
	display: flex;
	justify-content: space-between;
	align-items: center;
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

.confirm-btn {
	padding: 6px 14px;
	border-radius: 8px;
	font-size: 13px;
	white-space: nowrap;
}

.confirm-btn-ok {
	order: 2;
	background: #ffd541;
	color: #0f172a;
	font-weight: 600;
	box-shadow: 0 3px 8px rgba(245, 158, 11, 0.16);
}

.confirm-btn-cancel {
	order: 1;
	background: #f1f5f9;
	color: #64748b;
}

.confirm-resolved {
	font-size: 12px;
	color: #64748b;
}
</style>
