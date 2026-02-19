import os

class WebConfig:
    ADS_ENABLED = os.environ.get("ADS_ENABLED", "true").lower() == "true"
    ADSENSE_APP_ID = "ca-app-pub-8537336585034121~9051476313"
    ADSENSE_UNIT_ID = "ca-app-pub-8537336585034121/9758043587"
    
    # Policy URLs
    PRIVACY_URL = "/privacy"
    TERMS_URL = "/terms"
    DOCS_URL = "/docs"
