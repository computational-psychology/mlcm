try:
    import rpy2  #  noqa: F401
except ModuleNotFoundError as e:
    raise Exception(
        "`mlcm` depends on R, via the rpy2 package. Make sure both are installed (in the current environment)"
    ) from e
