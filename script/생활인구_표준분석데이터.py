"""
Author: NY.Kim
Date : 2019-12-23
생활인구 Data 백분위수 적용 Program
"""

"""
패키지 불러오기
"""
import sys
import platform

if platform.architecture()[0]=='32bit':
    PACK_DIR ='C:/earthquake/package/32bit/site-packages'
else:
    PACK_DIR ='C:/earthquake/package/64bit/site-packages'
sys.path.append(PACK_DIR)


import pandas as pd
import glob
import csv

'''
csv 구분자 탐색 후 읽기 함수
'''
def read_file(read):
    global li

    dialect = csv.Sniffer().sniff(read)
    df = pd.read_csv(filename, index_col=None, header=0, sep=dialect.delimiter)
    li.append(pd.DataFrame(df))


path = "C:/earthquake/data/생활인구"
all_files = glob.glob(path + "/*.csv")

li = []

for filename in all_files:
    try:
        with open(filename,'r',encoding='cp949') as f:
            read_file(f.read())
    except UnicodeDecodeError:
        with open(filename,'r',encoding='UTF-8') as f:
            read_file(f.read())

df_living = pd.concat(li, axis=0, ignore_index=True)  # 생활인구 DATA 불러오기


living_index_amax = df_living.groupby("INDEX_ID", as_index=False)["A_MAX_POP"].quantile(.95)  # 상위 5% 제거
living_index_amax.columns = ["INDEX_ID", "A_MAX"]
living_index_amax["A_MAX"] = round(living_index_amax["A_MAX"]).astype("int")

living_index_amax.set_index('INDEX_ID',inplace = True)
living_index_amax.to_csv("C:/earthquake/result/living_pop_max.csv", encoding="cp949")

sys.path.remove(PACK_DIR)

layer = iface.addVectorLayer("C:/earthquake/result/living_pop_max.csv", "", "ogr")