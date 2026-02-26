import { sendReleaseRequest } from './request.js';

// 登录接口
export const login = (params) => sendReleaseRequest("/api/user/login/", 'POST', params);

// 注册接口
export const register = (params) => sendReleaseRequest("/api/user/register/", 'POST', params);
