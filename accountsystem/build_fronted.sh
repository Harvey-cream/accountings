#!/bin/bash

# --- 配置区域 ---
# 服务器前端项目的根目录 (源码位置)
PROJECT_DIR="/www/wwwroot/accounting/uni_accounting"
# 构建产物存放目录 (uni-app H5 默认路径)
BUILD_DIST="$PROJECT_DIR/dist/build/h5"
# Nginx 实际托管的宿主机静态文件目录 (映射到容器内的 /app/static)
WEB_ROOT="/www/wwwroot/accounting/accountsystem/static"

echo "======= 开始部署 uni_accounting ======="

# 1. 进入项目目录
cd $PROJECT_DIR || { echo "错误: 找不到目录 $PROJECT_DIR"; exit 1; }
# 3. 安装依赖
echo ">>> 正在安装依赖..."
# 使用 npm install，如果服务器网络慢建议使用 npm install --registry=https://registry.npmmirror.com
npm install || { echo "错误: npm install 失败"; exit 1; }

# 4. 执行构建
echo ">>> 正在执行构建 (H5)..."
npm run build:h5 || { echo "错误: 编译失败"; exit 1; }

# 5. 发布到 Web 目录
if [ -d "$BUILD_DIST" ]; then
    echo ">>> 正在发布产物到 $WEB_ROOT..."
    # 如果 WEB_ROOT 不存在则创建
    mkdir -p $WEB_ROOT
    # 清空旧文件并复制新文件
    rm -rf $WEB_ROOT/*
    cp -r $BUILD_DIST/* $WEB_ROOT/
    echo "======= 部署完成！======="
    echo "构建产物已同步至: $WEB_ROOT"
else
    echo "错误: 未找到构建产物目录 $BUILD_DIST"
    exit 1
fi
