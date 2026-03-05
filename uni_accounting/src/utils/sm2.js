import { sm2 } from 'sm-crypto';
export const SM2Utils = {
    encrypt(data, publicKey) {
        return sm2.doEncrypt(data, publicKey, 1);
    },
    decrypt(encryptData, privateKey) {
        return sm2.doDecrypt(encryptData, privateKey, 1);
    }
};

// --- 密钥配置 ---
// PAIR 1: 前端请求后端 (公钥请求加密)
export const BACK_PUBLIC_KEY = "040f7b69db681310cf0c56ea8f853eaf2164b274bcfb178850547d45235861ecc729378da575b33d3badd2060a26593cfca227be3a3c837e106cb1a4aac32a823b";

// PAIR 2: 后端响应前端 (私钥响应解密)
export const FRONT_PRIVATE_KEY = "a543b37a621e06ef3ce89eca78a79f2296c0415d009df2ff3ceb688cdf1fa8e8";
