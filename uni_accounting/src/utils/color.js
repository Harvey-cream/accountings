/**
 * 图标颜色池配置
 */
export const colorPairs = [
	{ bg: '#fffbeb', icon: '#d97706' },
	{ bg: '#eff6ff', icon: '#3b82f6' },
	{ bg: '#ecfdf5', icon: '#10b981' },
	{ bg: '#f3e8ff', icon: '#9333ea' },
	{ bg: '#fee2e2', icon: '#ef4444' },
	{ bg: '#ffedd5', icon: '#f97316' },
	{ bg: '#ecfeff', icon: '#06b6d4' },
	{ bg: '#f1f5f9', icon: '#64748b' }
];

/**
 * 为图标数据自动分配颜色 (固定颜色分配，基于 ID 或图标名)
 * @param {Array} iconData 图标数据列表
 * @returns {Array} 带有颜色属性的图标列表
 */
export const assignDefaultColors = (iconData) => {
	if (!Array.isArray(iconData)) return [];
	
	return iconData.map((item) => {
		let colorIndex = 0;
		if (item.id) {
			colorIndex = Number(item.id) % colorPairs.length;
		} else if (item.icon) {
			// 简单的哈希逻辑：累加字符编码
			const charSum = item.icon.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
			colorIndex = charSum % colorPairs.length;
		}
		
		const colors = colorPairs[colorIndex];
		return {
			...item,
			colorBg: colors.bg,
			colorIcon: colors.icon
		};
	});
};

/**
 * 根据图标 ID 获取颜色配对
 * @param {number|string} iconId 
 * @returns {object} { bg, icon }
 */
export const getIconColors = (iconId) => {
	const colorIndex = Number(iconId) % colorPairs.length;
	return colorPairs[colorIndex] || colorPairs[0];
};

export default {
	colorPairs,
	assignDefaultColors,
	getIconColors
};
