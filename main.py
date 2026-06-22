# 尝试从 .env 文件加载环境变量
import os
from dotenv import load_dotenv

# 💡 优化 1：不要用 os.path.exists 锁死。
# load_dotenv 自身非常智能：如果找不到 .env 文件，它会自动忽略，不会报错。
# override=False 可以确保：如果 GitHub 系统中已经有了同名环境变量，不会被本地的空配置覆盖。
load_dotenv(dotenv_path=".env", override=False)

# 💡 优化 2：在运行任务前，加一个核心环境变量的“强校验”
# 这样如果 GitHub Secrets 没配置对，能立刻在日志里报错，而不是等到浏览器打开了才莫名其妙崩溃。
if not os.environ.get("DOUYIN_COOKIE") and not os.environ.get("VARS_JSON"):
    print("⚠️ 警告: 未检测到本地 .env 文件或 GitHub 环境变量(DOUYIN_COOKIE / VARS_JSON)！")
    print("请检查本地配置或 GitHub 仓库的 Settings -> Secrets and variables。")

from core.tasks import runTasks

# 执行任务
runTasks()
