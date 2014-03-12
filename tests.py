import requests
from requests.exceptions import Timeout, ConnectionError
from multiprocessing import Pool
import time
import csv
from cStringIO import StringIO

def stack(fname, pile_size):
    with open(fname, 'rb') as guts:
        reader = csv.reader(guts)
        stuff = list(reader)
    body = []
    for thing in range(pile_size):
        body.extend(stuff)
    pile = StringIO()
    writer = csv.writer(pile)
    writer.writerows(body)
    pile.seek(0)
    return pile

def full_run(args):
    url, pile_size, file_type = args
    s = requests.Session()
    if file_type != 'csv' and pile_size > 1:
        return 'Can\'t stack non-csv files'
    elif file_type == 'csv':
        pile = stack('csv_example_messy_input.csv', pile_size)
        f = {'input_file': ('test.csv', pile.getvalue())}
    else:
        f = {'input_file': open('csv_example_messy_input.%s' % file_type, 'rb')}
    r = s.post(url, files=f)
    fields = {'Site name': 'on', 'Phone': 'on', 'Address': 'on', 'Zip': 'on'}
    start = time.time()
    select = s.post('%s/select_fields/' % url, data=fields)
    end = time.time()
    print 'Select fields took %s seconds' % (str(end - start))
    yes = 0
    no = 0
    timeout = 120
    resp = s.get('%s/get-pair/' % url)
    for i in range(12):
        try:
            s.get('%s/mark-pair/' % url, params={'action': 'yes'}, timeout=timeout)
            s.get('%s/get-pair/' % url, timeout=timeout)
            yes += 1
            print 'Training: %s yes %s no' % (yes, no)
            time.sleep(2)
        except (Timeout, ConnectionError):
            return 'Marking pair #%s failed' % yes
    for i in range(12):
        try:
            s.get('%s/mark-pair/' % url, params={'action': 'no'}, timeout=timeout)
            s.get('%s/get-pair/' % url, timeout=timeout)
            no += 1
            print 'Training: %s yes %s no' % (yes, no)
            time.sleep(2)
        except (Timeout, ConnectionError):
            return 'Marking pair #%s failed' % (yes + no)
    try:
        s.get('%s/mark-pair/' % url, params={'action': 'finish'}, timeout=timeout)
        start = time.time()
        print 'Deduplication started...'
    except (Timeout, ConnectionError):
        return 'Training finish failed'
    try:
        while True:
            work = s.get('%s/working/' % url, timeout=timeout)
            try:
                if work.json().get('ready'):
                    end = time.time()
                    break
                else:
                    time.sleep(3)
                    continue
            except ValueError:
                print work.content
                if work.status_code is 504:
                    time.sleep(3)
                    continue
                else:
                    return 'The app seems to have crashed'
    except (Timeout, ConnectionError):
        return 'Failed while waiting for results'
    print 'Dedupe Took %s seconds' % (str(end - start))
    try:
        s.get('%s/adjust_threshold/' % url, params={'recall_weight': 8}, timeout=timeout)
        start = time.time()
        print 'Adjusting threshold...'
    except (TimeoutError, ConnectionError):
        return 'Failed while adjusting threshold'
    try:
        while True:
            work = s.get('%s/working/' % url, timeout=timeout)
            try:
                if work.json().get('ready'):
                    end = time.time()
                    break
                else:
                    time.sleep(3)
                    continue
            except ValueError:
                print work.content
                if work.status_code is 504:
                    time.sleep(3)
                    continue
                else:
                    return 'The app seems to have crashed'
    except (Timeout, ConnectionError):
        return 'Failed while waiting for adjusted dedupe session'
    print 'Adjusted recall weight in %s seconds' % (str(end - start))
    return work.json()['result']

def trained_run(args):
    url, pile_size, file_type = args
    s = requests.Session()
    f = {'input_file': open('csv_example_messy_input.csv', 'rb')}
    r = s.post(url, files=f)
    fields = {'Site name': 'on', 'Phone': 'on', 'Address': 'on', 'Zip': 'on'}
    start = time.time()
    select = s.post('%s/select_fields/' % url, data=fields)
    end = time.time()
    print 'Select fields took %s seconds' % (str(end - start))
    f = {'training_data': open('csv_example_training.json', 'rb')}
    r = s.post('%s/trained_dedupe/' % url, files=f)
    s.get('%s/mark-pair/' % url, params={'action': 'finish'})
    start = time.time()
    print 'Deduplication started...'
    while True:
        work = s.get('%s/working/' % url)
        if work.json().get('ready'):
            print work.json()
            end = time.time()
            break
        else:
            time.sleep(3)
            continue
    print 'Adjusting threshold...'
    s.get('%s/adjust_threshold/' % url, params={'recall_weight': 8})
    while True:
        work = s.get('%s/working/' % url)
        if work.json().get('ready'):
            print work.json()
            end = time.time()
            break
        else:
            time.sleep(3)
            continue
    print 'Adjusting threshold...again...'
    s.get('%s/adjust_threshold/' % url, params={'recall_weight': 0.25})
    while True:
        work = s.get('%s/working/' % url)
        if work.json().get('ready'):
            print work.json()
            end = time.time()
            break
        else:
            time.sleep(3)
            continue
    print 'Dedupe Took %s seconds' % (str(end - start))

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(
      formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('-c', '--count', type=int, 
        help='Number of concurrent requests',
        default=1)
    parser.add_argument('-u', '--url', type=str, 
        help='Number of concurrent requests',
        default='http://dedupe.datamade.us')
    parser.add_argument('-s', '--size', type=int, 
        help='Number of times to duplicate input file to mimic large file.',
        default=1)
    parser.add_argument('-t', '--type', type=str, 
        help='Type of dedupe session. Either trained or full',
        default='full', choices=['full', 'trained'])
    parser.add_argument('-f', '--file_type', type=str, 
        help='Type of file to upload for training. xls, xlsx, or csv',
        default='csv', choices=['csv', 'xls', 'xlsx'])
    args = parser.parse_args()
    pool = Pool(processes=args.count)
    args_map = []
    for i in range(args.count):
        args_map.append([args.url, args.size, args.file_type])
    if args.type == 'full': 
        print pool.map(full_run, args_map)
    elif args.type == 'trained':
        print pool.map(trained_run, args_map)
