import signal
import sys
from multiprocessing import Pool

import requests

signal.signal(signal.SIGINT, signal.SIG_IGN)


def request(i):
    path = sys.argv[1]
    files = {"file": open(path, "rb")}
    data = {"update": True}
    res = requests.post("http://localhost:3000", files=files, data=data, stream=True)
    if res.status_code != 200:
        print(res.status_code, res.text)
    # with open(f'{i}.zip', 'wb') as f:
    #     for chunk in res.iter_content(chunk_size=1 << 16):
    #         f.write(chunk)


pool = Pool(20)
try:
    pool.map(request, range(100))
except KeyboardInterrupt:
    pool.terminate()
    pool.join()
