# 使用 Python 作为基础镜像 
FROM 47.115.79.247:5000/pyenv:v4 

# 设置工作目录 
WORKDIR /app 

# 复制 requirements.txt 并安装依赖 
COPY requirements.txt /app/ 
RUN pip install --no-cache-dir -r requirements.txt 

# 复制整个项目 
COPY . /app/ 

# 执行数据库迁移 
ENV DJANGO_ENV=production 
# 注意：在构建阶段运行迁移通常需要数据库连接，如果构建时数据库不可用，这些命令可能会失败。
# 建议在容器启动脚本中运行迁移，或者确保构建环境可以访问数据库。
RUN python manage.py makemigrations 
RUN python manage.py migrate 

# 暴露端口 
EXPOSE 8899
