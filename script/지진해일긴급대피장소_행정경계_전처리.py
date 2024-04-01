"""
Author: JJ.Kang
Date : 2021-02-18
이 프로그램은 지진해일긴급대피장소 행정경계 컬럼 전처리
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
import geopandas as gpd
import os

#원본 백업 함수
def Move_file(nm):
    global base_path
    
    try:
        os.mkdir(base_path + 'bak/')
    except:
        pass
    
    for file in os.listdir(base_path):
        file_nm = file.split('.')[0]
        if file_nm == nm:
            os.rename(base_path + file, base_path + 'bak/' + file)
"""
bak폴더가 있는지 확인
"""
if os.path.isdir('C:/earthquake/data/지진해일긴급대피장소/행정경계/bak'):
    pass
else:
    """
    행정경계 불러오기
    """
    base_path = "C:/earthquake/data/지진해일긴급대피장소/행정경계/"  # 기본 경로 설정
    bnd_sido = gpd.read_file(base_path + 'bnd_sido.shp', encoding="cp949")  # 격자 Data 불러오기
    bnd_sigungu = gpd.read_file(base_path + 'bnd_sigungu.shp', encoding="cp949")
    bnd_dong = gpd.read_file(base_path + 'bnd_dong.shp', encoding="cp949")

    #원본파일 백업
    Move_file('bnd_sido')
    Move_file('bnd_sigungu')
    Move_file('bnd_dong')
    
    
bnd_sido.rename(columns = {'BASE_DATE':'base_year','SIDO_CD':'sido_cd','SIDO_NM':'sido_nm'},inplace= True) #컬럼명 변경
bnd_sigungu.rename(columns = {'BASE_DATE':'base_year','SIGUNGU_CD':'sigungu_cd','SIGUNGU_NM':'sigungu_nm'},inplace= True)
bnd_dong.rename(columns = {'BASE_DATE':'base_year','ADM_DR_CD':'adm_dr_cd','ADM_DR_NM':'adm_dr_nm'},inplace= True)



bnd_sido.to_file(base_path + 'bnd_sido.shp',encoding='cp949')      # 데이터 덮어쓰기
bnd_sigungu.to_file(base_path + 'bnd_sigungu.shp',encoding='cp949')
bnd_dong.to_file(base_path + 'bnd_dong.shp',encoding='cp949')

sys.path.remove(PACK_DIR)