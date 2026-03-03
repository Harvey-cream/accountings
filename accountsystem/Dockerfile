# 使用 Python slim 镜像以减少内存占用 
FROM python:3.9-slim 

# 设置工作目录 
WORKDIR /app 

# 配置清华大学 APT 镜像源以加速系统依赖安装
RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list && \
    sed -i 's/security.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

# 只装必需的 MySQL 客户端（用于启动时检查状态），并清理缓存以减少体积
RUN apt-get update && apt-get install -y --no-install-recommends \ 
    default-mysql-client \ 
    && rm -rf /var/lib/apt/lists/* 

# 配置清华大学 PyPI 镜像源并安装依赖
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
COPY requirements.txt /app/ 
RUN pip install --no-cache-dir -r requirements.txt 

# 复制项目代码 
COPY . /app/ 

# 设置生产环境标识
ENV DJANGO_ENV=production 

# 暴露端口 
EXPOSE 8899
