import logging


def setup_logger(logger_name):
    """Setup logging to log output to both a file and stderr

    :param logger_name: the name of the logger & the name of the \n
        logger file with ".log" appended
    :return: the logger with the handlers added
    """
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "[%(name)s] - %(levelname)s - %(asctime)s -\n\t%(message)s")

    # stream handler
    sh = logging.StreamHandler()  # std.err
    sh.setLevel(logging.WARNING)
    sh.setFormatter(formatter)

    # file handler
    fh = logging.FileHandler(logger_name + '.log')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)

    logger.addHandler(sh)
    logger.addHandler(fh)
    return logger