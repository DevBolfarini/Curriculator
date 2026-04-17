def get_display(text, **kwargs):
    """Shim for python-bidi to avoid ModuleNotFoundError when compilers are missing."""
    return text
