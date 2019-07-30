import os
import sys
import requests
import csv
import argparse
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

parser = argparse.ArgumentParser(description='Get path to TXT file containing names of CSVs to be downloaded.')
parser.add_argument('txt_file', help='Path to TXT file.')
parser.add_argument('save_path', help='Path to folder where to save PARQUET files.')
args = parser.parse_args()
header = ['zoneID', 'time', 'cx', 'cy', 'cz', 'x', 'y', 'xa', 'ya', 'q', 'xi', 'eta', 'ra', 'dec', 'flag']

if __name__ == '__main__':
    with open(args.txt_file) as txt_file:
        file_names = list(filter(lambda x: len(x), txt_file.read().split('\n')))
    for file_name in file_names:
        print('\nDownloading content from:', file_name)
        # ----- lazy -----
        downloaded_csv = requests.get(file_name, stream=True)
        lines = (line.decode('utf-8') for line in downloaded_csv.iter_lines())
        reader = csv.reader(lines, delimiter='|')
        # ----- lazy -----
        content_length = int(downloaded_csv.headers['Content-Length'])
        max_size = int(content_length/np.ceil(content_length/1e+7))
        collected_data = []
        msg_len = 0
        inc = 0
        for cnt, row in enumerate(reader):
            if sys.getsizeof(collected_data) >= max_size:
                path = os.path.join(args.save_path, file_name.split('/')[-1].replace('csv', '') + str(inc).zfill(2) + '.parquet')
                print('\nGenerating DataFrame and writing Parquet file to {}'.format(path))
                df = pd.DataFrame(collected_data, columns=header)
                tbl = pa.Table.from_pandas(df)
                pq.write_table(tbl, path, compression='snappy')
                collected_data = []
                inc += 1
            else:
                msg = '\rReading row #{:,}'.format(cnt)
                buffer = msg_len - len(msg)
                buffer = buffer if buffer > 0 else 0
                print(msg, end=' '*buffer, flush=True)
                msg_len = len(msg)
                collected_data.append(row)