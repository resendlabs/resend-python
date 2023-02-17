import random
import time

import requests


class BackoffStrategy:
    initial_interval: int
    max_interval: int
    exponent: float
    max_elapsed_time: int

    def __init__(self, initial_interval: int, max_interval: int, exponent: float, max_elapsed_time: int):
        self.initial_interval = initial_interval
        self.max_interval = max_interval
        self.exponent = exponent
        self.max_elapsed_time = max_elapsed_time


class RetryConfig:
    strategy: str
    backoff: BackoffStrategy
    retry_connection_errors: bool

    def __init__(self, strategy: str, retry_connection_errors: bool):
        self.strategy = strategy
        self.retry_connection_errors = retry_connection_errors


class Retries:
    config: RetryConfig
    status_codes: list[str]

    def __init__(self, config: RetryConfig, status_codes: list[str]):
        self.config = config
        self.status_codes = status_codes


class TemporaryError(Exception):
    response: requests.Response

    def __init__(self, response: requests.Response):
        self.response = response


class PermanentError(Exception):
    inner: Exception

    def __init__(self, inner: Exception):
        self.inner = inner


def retry(fn, retries: Retries):
    if retries.config.strategy == 'backoff':
        def do_request():
            res: requests.Response
            try:
                res = fn()

                for code in retries.status_codes:
                    if "X" in code.upper():
                        codeRange = int(code[0])

                        s = res.status_code / 100

                        if s >= codeRange and s < codeRange + 1:
                            raise TemporaryError(res)
                    else:
                        parsed_code = int(code)

                        if res.status_code == parsed_code:
                            raise TemporaryError(res)
            except requests.exceptions.ConnectionError as e:
                if not retries.config.config.retry_connection_errors:
                    raise
                else:
                    raise PermanentError(e)
            except requests.exceptions.Timeout as e:
                if not retries.config.config.retry_connection_errors:
                    raise
                else:
                    raise PermanentError(e)
            except TemporaryError:
                raise
            except Exception as e:
                raise PermanentError(e)

            return res

        return retry_with_backoff(do_request, retries.config.backoff.initial_interval, retries.config.backoff.max_interval, retries.config.backoff.exponent, retries.config.backoff.max_elapsed_time)
    else:
        fn()


def retry_with_backoff(fn, initial_interval=500, max_interval=60000, exponent=1.5, max_elapsed_time=3600000):
    start = round(time.time()*1000)
    x = 0

    while True:
        try:
            return fn()
        except PermanentError as e:
            raise e.inner
        except Exception as e:
            now = round(time.time()*1000)
            if now - start > max_elapsed_time:
                if isinstance(e, TemporaryError):
                    return e.response
                else:
                    raise
            sleep = ((initial_interval/1000) *
                     exponent**x + random.uniform(0, 1))
            if sleep > max_interval/1000:
                sleep = max_interval/1000
            time.sleep(sleep)
            x += 1
