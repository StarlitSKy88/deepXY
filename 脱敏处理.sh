#!/bin/bash

# 项目脱敏脚本
# 用于在上传到GitHub前移除敏感信息

echo "开始脱敏处理..."

# 1. 检查环境变量文件
if [ -f .env ]; then
    echo "检测到.env文件，创建安全备份并替换为示例文件"
    cp .env .env.backup
    cp .env.example .env
    echo "已创建.env备份为.env.backup，并使用示例配置替换"
fi

# 2. 检查可能包含API密钥的配置文件
CONFIG_FILES=("app/config/settings.py" "app/config/config.json")
for file in "${CONFIG_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "检测到配置文件: $file，创建备份并替换敏感信息"
        cp "$file" "${file}.backup"
        # 替换API密钥为示例值
        sed -i.bak 's/\(API_KEY=\|api_key=\|apiKey=\|"key"\s*:\s*"\)[^"]*\("\)/\1your_api_key\2/g' "$file"
        rm -f "${file}.bak"
    fi
done

# 3. 检查日志文件并清理
LOG_DIRS=("logs" "app/logs")
for dir in "${LOG_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        echo "清理日志目录: $dir"
        find "$dir" -type f -name "*.log" -exec rm -f {} \;
        touch "$dir/.gitkeep"
    fi
done

# 4. 创建.gitignore文件(如果不存在)
if [ ! -f .gitignore ]; then
    echo "创建.gitignore文件"
    cat > .gitignore << EOL
# 环境变量文件
.env
.env.*
!.env.example

# Python缓存
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
*.egg-info/
.installed.cfg
*.egg

# 日志文件
logs/
*.log
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# 系统文件
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# 开发环境
.idea/
.vscode/
*.sublime-workspace
*.swp
*.swo
EOL
fi

# 5. 检查并清理无意中保存的API密钥
echo "扫描可能包含API密钥的文件..."
find . -type f -not -path "*/\.*" -not -path "*/node_modules/*" -not -path "*/.git/*" -name "*.py" -o -name "*.js" -o -name "*.json" | xargs grep -l "api[_-]key" 2>/dev/null | while read -r file; do
    echo "警告: 可能包含API密钥的文件: $file"
    echo "请手动检查并清理该文件中的敏感信息"
done

echo "脱敏处理完成！"
echo "请在上传到GitHub前再次检查以确保所有敏感信息已移除" 