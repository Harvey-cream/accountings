import { ref } from 'vue';
import { getAllIcons } from '@/api/api.js';

const allIcons = ref([]);

export const useIconStore = () => {
    const fetchIcons = async () => {
        if (allIcons.value.length > 0) return allIcons.value;
        
        try {
            const res = await getAllIcons();
            if (res.code === 0) {
                allIcons.value = res.data;
                return res.data;
            }
        } catch (e) {
            console.error('获取全局图标失败:', e);
        }
        return [];
    };

    const getIcons = () => {
        return allIcons.value;
    };

    return {
        allIcons,
        fetchIcons,
        getIcons
    };
};
