import hashlib
import xxhash


def calc_checksum(algorithm, data):
    """
    Calculate checksum for a binary data
    """

    if algorithm == "xxh3_64":
        checksum = xxhash.xxh3_64(data).hexdigest()
    elif algorithm == "md5":
        checksum = hashlib.md5(data).hexdigest()
    else:
        checksum = None

    return checksum
