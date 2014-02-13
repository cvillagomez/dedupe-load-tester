import os
import time
import requests
from multiprocessing import Pool

def runit(url):
    s = requests.Session()
    f = {'input_file': open('csv_example_messy_input.csv', 'rb')}
    r = s.post(url, files=f)
    fields = {'Site name': 'on', 'Phone': 'on', 'Address': 'on', 'Zip': 'on'}
    start = time.time()
    select = s.post('%s/select_fields/' % url, data=fields)
    end = time.time()
    print 'Select fields took %s seconds' % (str(end - start))
    for i in range(12):
        s.get('%s/mark-pair/' % url, params={'action': 'yes'})
        s.get('%s/get-pair/' % url)
        time.sleep(2)
    for i in range(12):
        s.get('%s/mark-pair/' % url, params={'action': 'no'})
        s.get('%s/get-pair/' % url)
        time.sleep(2)
    s.get('%s/mark-pair/' % url, params={'action': 'finish'})
    start = time.time()
    while True:
        if s.get('%s/working/' % url).json().get('ready'):
            end = time.time()
            break
        else:
            time.sleep(3)
            continue
    print 'Dedupe Took %s seconds' % (str(end - start))
    return None

if __name__ == '__main__':
    pool = Pool(processes=4)
    args = 'http://dedupe.datamade.us'
    args_map = []
    for i in range(4):
        args_map.append(args)
    print pool.map(runit, args_map)
