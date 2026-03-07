import { sendRequest, sendReleaseRequest } from './request.js';

// --- 公开接口 (不需要登录) ---

// 登录
export const login = (params) => sendReleaseRequest("/api/user/login/", 'POST', params);

// 注册
export const register = (params) => sendReleaseRequest("/api/user/register/", 'POST', params);

// 获取所有图标列表 (公开接口)
export const getAllIcons = () => sendReleaseRequest("/api/account/icons/", 'GET');


// --- 受保护接口 (需要登录) ---

// 用户信息 
export const getUserInfo = () => sendRequest("/api/user/info/", 'GET');

// 获取账单列表
export const getBills = (data) => sendRequest("/api/account/bill/list/", 'GET', data);

// 保存账单
export const saveBill = (params) => sendRequest("/api/account/bill/save/", 'POST', params);

// 删除账单
export const deleteBill = (id) => sendRequest("/api/account/bill/delete/", 'POST', { id });

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
