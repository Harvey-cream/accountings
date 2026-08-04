import { API_URL } from '@/config/index.js';

function _streamAuthHeaders() {
	const sessionInfo = uni.getStorageSync('session');
	const token = sessionInfo?.token_info?.token;
	if (!token) throw new Error('未登录');
	const headers = {
		'Content-Type': 'application/json',
		'Accept': 'text/event-stream',
		'Authorization': 'Bearer ' + token,
	};
	const userId = sessionInfo?.user_info?.userId;
	if (userId) headers['X-User-ID'] = userId;
	return headers;
}

function _dispatchEvent(event, handlers) {
	const { onStatus, onToken, onDone, onError } = handlers;
	if (event.type === 'status') onStatus?.(event.text);
	else if (event.type === 'token') onToken?.(event.text);
	else if (event.type === 'done') onDone?.(event);
	else if (event.type === 'error') onError?.(event);
}

function _parseBuffer(buffer, handlers) {
	const parts = buffer.split('\n\n');
	const rest = parts.pop() || '';
	for (const part of parts) {
		const line = part.trim();
		if (!line.startsWith('data: ')) continue;
		_dispatchEvent(JSON.parse(line.slice(6)), handlers);
	}
	return rest;
}

/** H5 SSE 流式对话：onStatus / onToken / onDone / onError */
export async function sendLangchainChatStream(content, handlers = {}) {
	if (!isLangchainStreamSupported()) {
		throw new Error('当前环境不支持流式（需要浏览器 fetch + ReadableStream）');
	}
	const response = await fetch(API_URL + '/api/account/langchain/chat/stream/', {
		method: 'POST',
		headers: _streamAuthHeaders(),
		body: JSON.stringify({ content }),
	});
	if (!response.ok) {
		handlers.onError?.({ message: '请求失败' });
		throw new Error('stream failed');
	}
	const reader = response.body.getReader();
	const decoder = new TextDecoder();
	let buffer = '';
	while (true) {
		const { done, value } = await reader.read();
		if (done) break;
		buffer += decoder.decode(value, { stream: true });
		buffer = _parseBuffer(buffer, handlers);
	}
	buffer = _parseBuffer(buffer + '\n\n', handlers);
}

/** 是否支持 H5 SSE 流式（浏览器 fetch + ReadableStream） */
export const isLangchainStreamSupported = () => {
	if (typeof window === 'undefined' || typeof fetch !== 'function') return false;
	return typeof ReadableStream !== 'undefined';
};
