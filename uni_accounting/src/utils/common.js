/**
 * 通用路由工具
 */

/**
 * 统一返回逻辑
 * 一行代码搞定：如果有上一页则返回，否则跳转到传入的 url
 * @param {string} url 兜底跳转地址
 */
export const goBack = (url = '/pages/home/accounting_detail') => {
	const pages = getCurrentPages();
	if (pages.length > 1) {
		uni.navigateBack();
	} else {
		uni.switchTab({ url });
	}
};

export default {
	goBack
};
