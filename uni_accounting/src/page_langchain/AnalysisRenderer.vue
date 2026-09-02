<template>
	<view class="analysis-renderer">
		<view v-if="summaryText" class="analysis-summary">
			<view class="analysis-summary-label">分析结论</view>
			<text class="analysis-summary-text">{{ summaryText }}</text>
		</view>

		<view v-for="(section, index) in normalizedSections" :key="`${section.title || 'section'}-${index}`" class="analysis-section">
			<view class="analysis-section-header">
				<text class="analysis-section-title">{{ section.title }}</text>
			</view>

			<text v-if="section.content" class="analysis-section-content">{{ section.content }}</text>

			<view v-if="section.items.length" class="analysis-items">
				<view v-for="(item, itemIndex) in section.items" :key="`${index}-${itemIndex}`" class="analysis-item">
					<text class="analysis-item-label">{{ item.label || item.text || `项${itemIndex + 1}` }}</text>
					<text v-if="item.value" class="analysis-item-value">{{ item.value }}</text>
				</view>
			</view>
		</view>
	</view>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
	analysisView: {
		type: Object,
		default: () => ({})
	},
	fallbackText: {
		type: String,
		default: ''
	}
});

const summaryText = computed(() => String(props.analysisView?.summary?.text || '').trim());

const normalizedSections = computed(() => {
	const rawSections = Array.isArray(props.analysisView?.sections) ? props.analysisView.sections : [];
	return rawSections
		.map((section) => {
			const title = String(section?.title || '').trim();
			const content = String(section?.content || '').trim();
			const items = Array.isArray(section?.items)
				? section.items.map((item) => {
					if (typeof item === 'string') return { text: item.trim() };
					if (item && typeof item === 'object') {
						return {
							label: String(item.label || item.name || '').trim(),
							value: String(item.value || item.amount || '').trim(),
							text: String(item.text || '').trim(),
						};
					}
					return { text: '' };
				}).filter((item) => item.text || item.label || item.value)
				: [];
			return { title, content, items };
		})
		.filter((section) => section.title || section.content || section.items.length);
});
</script>

<style scoped>
.analysis-renderer {
	display: flex;
	flex-direction: column;
	gap: 14px;
}

.analysis-summary {
	padding: 14px 16px;
	background: #fffef7;
	border: 1px solid #f4e2a2;
	border-radius: 14px;
}

.analysis-summary-label {
	display: block;
	margin-bottom: 8px;
	font-size: 12px;
	font-weight: 700;
	color: #b45309;
	letter-spacing: 0.04em;
}

.analysis-summary-text {
	display: block;
	font-size: 15px;
	line-height: 1.8;
	color: #1f2937;
	word-break: break-word;
	overflow-wrap: anywhere;
}

.analysis-section {
	display: flex;
	flex-direction: column;
	gap: 10px;
	padding-top: 4px;
}

.analysis-section + .analysis-section {
	padding-top: 14px;
	border-top: 1px solid #e2e8f0;
}

.analysis-section-header {
	display: flex;
	align-items: center;
	justify-content: space-between;
}

.analysis-section-title {
	display: block;
	font-size: 15px;
	font-weight: 700;
	line-height: 1.4;
	color: #0f172a;
}

.analysis-section-content {
	display: block;
	font-size: 14px;
	line-height: 1.8;
	color: #334155;
	word-break: break-word;
	overflow-wrap: anywhere;
}

.analysis-items {
	display: flex;
	flex-direction: column;
	gap: 8px;
}

.analysis-item {
	display: flex;
	align-items: flex-start;
	justify-content: space-between;
	gap: 12px;
	padding: 8px 0;
}

.analysis-item + .analysis-item {
	border-top: 1px dashed #e2e8f0;
}

.analysis-item-label {
	flex: 1;
	min-width: 0;
	font-size: 14px;
	line-height: 1.7;
	color: #334155;
	word-break: break-word;
	overflow-wrap: anywhere;
}

.analysis-item-value {
	flex: 0 0 auto;
	font-size: 14px;
	line-height: 1.7;
	font-weight: 700;
	color: #0f172a;
	white-space: nowrap;
}
</style>
