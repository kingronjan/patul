import logging
import weakref
from typing import Generator


def iter_results(results):
    if results is None:
        return []
    if not isinstance(results, Generator):
        return [results]
    return results


_handlers = weakref.WeakValueDictionary()

def get_logger(name, level='DEBUG', file_path=None):
    """
    return logger.

    :param file_path:
        if is not None, logs will save to it,
        else, logs will not save to file.
    """
    extra = {'app_name': name}
    logger = logging.getLogger(__name__)
    formatter = logging.Formatter(
        fmt='%(asctime)s [%(app_name)s] %(levelname)s %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    if 'syslog' not in _handlers:
        syslog = logging.StreamHandler()
        _handlers['syslog'] = syslog
        syslog.setFormatter(formatter)
    else:
        syslog = _handlers['syslog']

    if file_path is not None:
        file_log = _handlers.get('filelog')
        if not file_log:
            file_log = logging.FileHandler(filename=file_path, encoding='utf-8')
            _handlers['filelog'] = file_log
        file_log.setFormatter(formatter)
        logger.addHandler(file_log)

    logger.addHandler(syslog)
    logger.setLevel(level)
    logger = logging.LoggerAdapter(logger, extra)
    return logger
