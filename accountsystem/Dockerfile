# 使用自定义基础镜像
# FROM 47.115.79.247:5000/pyenv:v4
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app
# 替换为阿里云 Debian 镜像源（适配 Trixie 版本）
RUN if [ -f /etc/apt/sources.list ]; then \
    echo "deb http://mirrors.aliyun.com/debian/ trixie main contrib non-free non-free-firmware" > /etc/apt/sources.list && \
    echo "deb http://mirrors.aliyun.com/debian/ trixie-updates main contrib non-free non-free-firmware" >> /etc/apt/sources.list && \
    echo "deb http://mirrors.aliyun.com/debian-security/ trixie-security main contrib non-free non-free-firmware" >> /etc/apt/sources.list; \
fi && \
apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# 复制 requirements.txt 并安装依赖
COPY requirements.txt /app/

# 🌟 关键修改：合并安装命令，保留阿里云源，取消单独 config 层
RUN pip install --no-cache-dir -i http://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com \
    --upgrade pip \
    -r requirements.txt

# 复制整个项目代码
COPY . /app/

# 启动脚本：等待数据库 + 自动迁移
RUN chmod +x /app/docker-entrypoint.sh

# 设置生产环境标识（由 docker-compose 覆盖或此处指定默认）
ENV DJANGO_ENV=production

ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["gunicorn", "accountsystem.wsgi:application", "--workers", "4", "--bind", "0.0.0.0:8899", "--timeout", "300", "--access-logfile", "-", "--log-level", "info"]

# 暴露端口
EXPOSE 8899
