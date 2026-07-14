import os

PORT = int(os.getenv("PORT", "3000"))
WECHAT_USE_MOCK = os.getenv("WECHAT_USE_MOCK", "true").lower() == "true"
WECHAT_APPID = os.getenv("WECHAT_APPID", "")
WECHAT_SECRET = os.getenv("WECHAT_SECRET", "YOUR_APP_SECRET_HERE")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
