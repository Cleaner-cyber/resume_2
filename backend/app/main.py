import os
import shutil

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.init_db import init_db
from app.api.resume_routes import router as resume_router

def setup_database_file():
    """
    【Zeabur 部署专用】
    在程序启动前，检查并自动将代码包自带的初始数据库同步到云端的持久化硬盘中。
    """
    target_db_path = "/data/resume.db"  # Zeabur 云端硬盘路径 (DATABASE_URL 中 4 个斜杠指向的终点)
    source_db_path = "data/resume.db"   # 本地项目中的初始数据库 (相对于 backend 根目录)

    # 如果云端持久化目录里没有数据库文件
    if not os.path.exists(target_db_path):
        print(f"⚠️ 未在持久化硬盘找到 {target_db_path}，正在执行初始化迁移...")
        # 确认代码包里确实带了初始数据库
        if os.path.exists(source_db_path):
            try:
                # 确保 /data 目录存在
                os.makedirs(os.path.dirname(target_db_path), exist_ok=True)
                # 执行复制搬家
                shutil.copy2(source_db_path, target_db_path)
                print("✅ 初始数据库 (resume.db) 已成功同步到云端硬盘！")
            except Exception as e:
                print(f"❌ 复制数据库失败，错误详情: {e}")
        else:
            print(f"⚠️ 代码包中未找到初始数据库({source_db_path})，SQLAlchemy 将稍后创建空表。")
    else:
        print("✅ 识别到云端持久化数据库，读取已有数据...")

def create_app() -> FastAPI:
    # 1. 在正式启动应用和连接数据库之前，先确保持久化数据库文件已就位
    setup_database_file()

    app = FastAPI(title="Resume Optimizer API", version="1.0.0")

    # 2. CORS 配置
    # 为了防止填错，兼容 ALLOWED_ORIGINS 和 CORS_ALLOW_ORIGINS 两个环境变量名
    raw_origins = os.getenv("ALLOWED_ORIGINS") or os.getenv("CORS_ALLOW_ORIGINS", "*")
    allowed_origins = raw_origins.split(",")
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[o.strip() for o in allowed_origins if o.strip()],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 3. 初始化数据库连接 (此时 /data/resume.db 已经存在)
    init_db()
    
    # 4. 挂载路由
    app.include_router(resume_router, prefix="/api")
    
    return app

app = create_app()