try:
    import pandas
    print(f"Pandas version: {pandas.__version__}")
    print("Pandas OK")
except ImportError as e:
    print(f"Pandas FAIL: {e}")
