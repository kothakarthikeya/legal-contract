"""Contract Intelligence System - Main Package"""
__version__ = "1.0.0"

# Monkey-patch langchain.debug if missing (for newer versions)
try:
    import langchain
    if not hasattr(langchain, "debug"):
        langchain.debug = False
except ImportError:
    pass
