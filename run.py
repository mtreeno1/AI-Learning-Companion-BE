import uvicorn
import os
from app.config import settings

if __name__ == "__main__":
    # Railway provides PORT environment variable
    port = int(os.environ.get("PORT", settings.API_PORT))
    
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=port,
        reload=False  # Disable reload in production
    )