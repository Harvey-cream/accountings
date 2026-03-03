# 使用 Python 作为基础镜像 
FROM python:3.9-slim

# 设置工作目录 
WORKDIR /app 

# 安装系统依赖（包含 mysql-client 以便在启动脚本中检查数据库状态）
RUN apt-get update && apt-get install -y \
    default-mysql-client \
    gcc \
    libmariadb-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# 复制 requirements.txt 并安装依赖 
COPY requirements.txt /app/ 
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 复制整个项目 
COPY . /app/ 

# 环境设置
ENV DJANGO_ENV=production 

# 暴露端口 
EXPOSE 8899
