import { sendRequest, sendReleaseRequest, sendUploadRequest } from './request.js';

// --- 公开接口 (不需要登录) ---

// 登录
export const login = (params) => sendReleaseRequest("/api/user/login/", 'POST', params);

// 注册
export const register = (params) => sendReleaseRequest("/api/user/register/", 'POST', params);

// 获取所有图标列表 (公开接口)
export const getAllIcons = () => sendReleaseRequest("/api/account/icons/", 'GET');


// --- 受保护接口 (需要登录) ---

// 用户信息 
export const getUserInfo = (userId = 'self') => sendRequest(`/api/user/info/?userId=${userId}`, 'GET');

// 修改用户信息
export const updateUserInfo = (data) => sendRequest("/api/user/info/update/", 'POST', data);

// 通用上传文件 (OSS)
export const uploadFile = (filePath, folder = 'others') => sendUploadRequest("/api/user/info/avatar/", filePath, 'file', { folder });

// 上传用户头像
export const uploadAvatar = (filePath) => sendUploadRequest("/api/user/info/avatar/", filePath);

// 获取账单列表
export const getBills = (data) => sendRequest("/api/account/bill/list/", 'GET', data);

// 保存或更新账单
export const saveBill = (params) => sendRequest("/api/account/bill/save/", 'POST', params);
export const updateBill = saveBill; // 别名，方便语义化

// 删除账单
export const deleteBill = (id) => {
	const params = typeof id === 'object' ? id : { id };
	return sendRequest("/api/account/bill/delete/", 'POST', params);
};

// 获取账单汇总统计
export const getBillSummary = (params) => sendRequest("/api/account/bill/summary/", 'GET', params);

// --- 预算相关接口 ---

// 获取预算详情 (总预算 + 分类预算列表)
export const getBudgets = (params) => sendRequest("/api/account/budget/get/", 'GET', params);

// 保存或更新预算
export const saveBudget = (params) => sendRequest("/api/account/budget/save/", 'POST', params);

// --- 资产相关接口 ---

// 保存或更新资产账户
export const saveAssetAccount = (params) => sendRequest("/api/account/asset/save/", 'POST', params);

// 获取资产账户列表
export const getAssetList = () => sendRequest("/api/account/asset/list/", 'GET');

// --- 发票相关接口 ---

// 获取发票列表
export const getInvoiceList = () => sendRequest("/api/account/invoice/list/", 'GET');

// 保存或更新发票
export const saveInvoice = (params) => sendRequest("/api/account/invoice/save/", 'POST', params);

// 删除发票
export const deleteInvoice = (id) => sendRequest("/api/account/invoice/delete/", 'POST', { id });

// --- 用户统计与打卡相关接口 ---

// 用户打卡
export const userCheckIn = () => sendRequest("/api/user/checkin/", 'POST');

// 获取用户统计数据
export const getUserStats = () => sendRequest("/api/user/stats/", 'GET');

// 获取用户积分数据
export const getUserPoints = () => sendRequest("/api/user/points/", 'GET');

// 用户签到领积分
export const userPointSignIn = () => sendRequest("/api/user/points/signin/", 'POST');

// 获取勋章列表
export const getMedalList = () => sendRequest("/api/user/medal/list/", 'GET');

// --- 系统消息接口 ---

// 获取系统消息列表
export const getSystemMessages = () => sendRequest("/api/system/message/list/", 'GET');

// 标记消息为已读
export const markMessageRead = (id) => sendRequest("/api/system/message/read/", 'POST', { id });

// 获取未读消息数量
export const getUnreadMessageCount = () => sendRequest("/api/system/message/unread/count/", 'GET');

// 获取邀请二维码
export const getInviteQR = () => sendRequest("/api/user/invite/qr/", 'GET');

// --- 社区动态接口 ---

// AI 记账对话：GET 历史；Agent 请求一律走 SSE 流式接口 /langchain/chat/stream/
export const getLangchainChat = (params = {}) => sendRequest("/api/account/langchain/chat/", 'GET', params);

// 发布帖子
export const publishPost = (data) => sendRequest("/api/comment/post/publish/", 'POST', data);

// 删除帖子
export const deletePost = (postId) => sendRequest("/api/comment/post/delete/", 'POST', { postId });

// 获取帖子列表
export const getPostList = (params) => sendRequest("/api/comment/post/list/", 'GET', params);

// 获取帖子详情
export const getPostDetail = (postId) => sendRequest("/api/comment/post/detail/", 'GET', { postId });

// 发表评论
export const publishComment = (data) => sendRequest("/api/comment/publish/", 'POST', data);

// 删除评论
export const deleteComment = (commentId) => sendRequest("/api/comment/delete/", 'POST', { commentId });

// 点赞/取消点赞帖子
export const likePost = (postId, isLiked) => sendRequest("/api/comment/post/like/", 'POST', { postId, isLiked });

// 关注/取消关注用户
export const toggleFollow = (followedUserId, isFollow) => sendRequest("/api/comment/follow/toggle/", 'POST', { followedUserId, isFollow });

// 获取关注/粉丝列表
export const getFollowList = (userId, type) => sendRequest("/api/comment/follow/list/", 'GET', { userId, type });
