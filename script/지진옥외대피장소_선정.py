"""
Author: NY.Kim
Date : 2019-12-23
이 프로그램은 지진옥외대피장소 AHP 스코어 산정 모델
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
from sklearn.preprocessing import StandardScaler

"""
AHP 격자 불러오기
"""
path = "C:/earthquake/result/Earthquake-EMERGENCY_ASSEMBLY_AREA/AHP.shp"  # 격자 경로 설정
shape_file = gpd.read_file(path, encoding="cp949")  # 격자 Data 불러오기
df_grid = shape_file.copy()


"""
데이터 전처리
"""
geo = df_grid["geometry"]
del df_grid["geometry"]
df_grid["lbl"] = df_grid["lbl"].replace("N/A", 0)
df_grid = df_grid.fillna(0)
df_grid["geometry"] = geo

landuse = df_grid["landuse"] == 1  # 주용도코드 활용 격자 선택
collapse = df_grid["collapse"] == 0  # 붕괴위험지구 제거
disaster = df_grid["disaster"] == 0  # 자연재해위험지구 제거
val5 = df_grid['val'] > 5
df_grid_a5 = df_grid[landuse & collapse & disaster & val5]
df_grid_a5.reset_index(drop=True,inplace=True)

loc_refuge = df_grid_a5.groupby("adm_dr_nm", as_index=False)["refuge_sum"].sum()
df_grid_a5 = pd.merge(df_grid_a5, loc_refuge, how="left", on="adm_dr_nm")
po_rate= df_grid_a5.groupby("adm_dr_nm", as_index=False)["val", "po_sum"].sum()
po_rate["rate"] = po_rate["po_sum"] / po_rate["val"]
df_grid_a5 = pd.merge(df_grid_a5, po_rate[["adm_dr_nm", "rate"]], how="left", on="adm_dr_nm")
df_grid_a5["loc_refuge"] = - df_grid_a5["refuge_sum_y"]
df_grid_a5["rate"] = - df_grid_a5["rate"]


"""
AHP 요소 별 변수 분류 & 모델 작성
"""
ahp = [0.185, 0.328, 0.192, 0.134]  # 기존 지진긴급해일대피장소 가중치
ahp_a = [i * 1.192 for i in ahp]
ahp_a = [round(x, 2) for x in ahp_a]

pop = ["val", "exceed_sum", "rate"]  # 요소 별 변수 분류
time = ["value", "loc_refuge"]
condition = ["danger_sum", "chem_sum"]
appointed = ["school", "park"]

ahp_scale = df_grid_a5.copy()
ahp_scale.drop(
    ["gid", "landuse", "sido_cd", "sido_nm", "sigungu_cd", "sigungu_nm", "base_year", "adm_dr_cd", "height_sum",
     "adm_dr_nm", "geometry", "atomic", "child", "old", "disaster", "collapse", "lbl"],
    axis=1, inplace=True)

ss = StandardScaler()
ahp_result = pd.DataFrame(ss.fit_transform(ahp_scale), columns=ahp_scale.columns)  # 데이터 표준화 작업

df_grid_a5["score"] = 0.22 * ahp_result[pop].sum(axis=1) + 0.39 * ahp_result[time].sum(axis=1) - \
                      0.23 * ahp_result[condition].sum(axis=1) + 0.16 * ahp_result["school"] + \
                      0.16/1.5 * ahp_result["park"]

location1 = (df_grid_a5["school"] == 0) & (df_grid_a5["park"] == 0) & (
            df_grid_a5["score"] > df_grid_a5["score"].quantile(.7))  # score 상위30%
location2 = ((df_grid_a5["school"] == 1) | (df_grid_a5["park"] == 1)) & (
            df_grid_a5["score"] > df_grid_a5["score"].quantile(.5))

df_grid_a5["location"] = 99  # score 하위 70% & 지정대상 존재 50% 격자
df_grid_a5.loc[location1, "location"] = 0  # 대피장소 지정대상 X
df_grid_a5.loc[location2, "location"] = 1  # 대피장소 지정대상 존재

df_grid_loc99 = df_grid_a5[df_grid_a5["location"] == 99]
df_grid_loc0 = df_grid_a5[df_grid_a5["location"] == 0]
df_grid_loc1 = df_grid_a5[df_grid_a5["location"] == 1]


df_grid_loc99.to_file("C:/earthquake/result/Earthquake-EMERGENCY_ASSEMBLY_AREA/AHP_99.shp", encoding="cp949")  # Shapefile로 저장
df_grid_loc0.to_file("C:/earthquake/result/Earthquake-EMERGENCY_ASSEMBLY_AREA/2.지진옥외대피장소_위치후보지(기타).shp", encoding="cp949")
df_grid_loc1.to_file("C:/earthquake/result/Earthquake-EMERGENCY_ASSEMBLY_AREA/1.지진옥외대피장소_위치후보지(학교_공원).shp", encoding="cp949")

sys.path.remove(PACK_DIR)

layer0 = iface.addVectorLayer("C:/earthquake/result/Earthquake-EMERGENCY_ASSEMBLY_AREA/2.지진옥외대피장소_위치후보지(기타).shp", "", "ogr")    # 레이어로 불러와서 띄우기
layer1 = iface.addVectorLayer("C:/earthquake/result/Earthquake-EMERGENCY_ASSEMBLY_AREA/1.지진옥외대피장소_위치후보지(학교_공원).shp", "", "ogr")
