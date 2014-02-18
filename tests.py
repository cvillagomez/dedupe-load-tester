import requests
from multiprocessing import Pool
import time

def runit(url):
    s = requests.Session()
    f = {'input_file': open('csv_example_messy_input.csv', 'rb')}
    r = s.post(url, files=f)
    fields = {'Site name': 'on', 'Phone': 'on', 'Address': 'on', 'Zip': 'on'}
    start = time.time()
    select = s.post('%s/select_fields/' % url, data=fields)
    end = time.time()
    print 'Select fields took %s seconds' % (str(end - start))
    yes = 0
    no = 0
    timeout = 15
    resp = s.get('%s/get-pair/' % url)
    print resp
    for i in range(12):
        try:
            s.get('%s/mark-pair/' % url, params={'action': 'yes'}, timeout=timeout)
            s.get('%s/get-pair/' % url, timeout=timeout)
            yes += 1
            print 'Training: %s yes %s no' % (yes, no)
            time.sleep(2)
        except requests.exceptions.Timeout:
            return 'Marking pair #%s failed' % yes
    for i in range(12):
        try:
            s.get('%s/mark-pair/' % url, params={'action': 'no'}, timeout=timeout)
            s.get('%s/get-pair/' % url, timeout=timeout)
            no += 1
            print 'Training: %s yes %s no' % (yes, no)
            time.sleep(2)
        except requests.exceptions.Timeout:
            return 'Marking pair #%s failed' % (yes + no)
    try:
        s.get('%s/mark-pair/' % url, params={'action': 'finish'}, timeout=timeout)
        start = time.time()
        print 'Deduplication started...'
    except requests.exceptions.Timeout:
        return 'Training finish failed'
    try:
        while True:
            if s.get('%s/working/' % url, timeout=timeout).json().get('ready'):
                end = time.time()
                break
            else:
                time.sleep(3)
                continue
    except requests.exceptions.Timeout:
        return 'Failed while waiting for results'
    print 'Dedupe Took %s seconds' % (str(end - start))
    return None

if __name__ == '__main__':
    import sys
    count = int(sys.argv[1])
    pool = Pool(processes=count)
    args = 'http://127.0.0.1:9999'
    args_map = []
    for i in range(count):
        args_map.append(args)
    print pool.map(runit, args_map)
