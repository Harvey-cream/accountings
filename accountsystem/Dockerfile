# 使用 Python 作为基础镜像 
FROM python:3.9-slim

# 设置工作目录 
WORKDIR /app 

# 复制 requirements.txt 并安装依赖 
COPY requirements.txt /app/ 
RUN pip install --no-cache-dir -r requirements.txt 

# 复制整个项目 
COPY . /app/ 

# 执行数据库迁移 (已移动到 docker-compose.yml 启动时执行)
ENV DJANGO_ENV=production 

# 暴露端口 
EXPOSE 8899
