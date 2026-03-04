# 使用自定义基础镜像
# FROM 47.115.79.247:5000/pyenv:v4
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 配置 PyPI 镜像源以加速安装（如果基础镜像未配置）
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 复制 requirements.txt 并安装依赖
COPY requirements.txt /app/
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 复制整个项目代码
COPY . /app/

# 设置生产环境标识（由 docker-compose 覆盖或此处指定默认）
ENV DJANGO_ENV=production

# 暴露端口
EXPOSE 8899
