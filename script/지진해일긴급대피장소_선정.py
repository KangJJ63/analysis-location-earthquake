"""
Author: NY.Kim
Date : 2019-12-23
이 프로그램은 지진긴급해일대피장소 AHP 스코어 산정 모델
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
path = "C:/earthquake/result/Tsunami-EMERGENCY_ASSEMBLY_AREA/AHP.shp"  # 격자 경로 설정
shape_file2 = gpd.read_file(path, encoding="cp949")  # 격자 Data 불러오기
df_grid_t = shape_file2.copy()

"""
데이터 전처리
"""
geo = df_grid_t["geometry"]
del df_grid_t["geometry"]
df_grid_t["lbl"] = df_grid_t["lbl"].replace("N/A", 0)
df_grid_t = df_grid_t.fillna(0)
df_grid_t["geometry"] = geo

landuse = df_grid_t["landuse"] == 1  # 주용도코드 활용 격자 선택
collapse = df_grid_t["collapse"] == 0  # 붕괴위험지구 제거
disaster = df_grid_t["disaster"] == 0  # 자연재해위험지구 제거
height = (df_grid_t["DN_max"] >= 10) | (((df_grid_t["hotel"] == 1) | (df_grid_t["public"] == 1)) & (
        df_grid_t["DN_max"] < 10))  # DEM max 10m이상 또는 10m이하 공공건물, 호텔 존재
coast = df_grid_t["coast"] == 1  # 해안선 600m이내 격자 선택

df_grid_ta = df_grid_t[landuse & collapse & disaster & height & coast]

df_grid_ta5 = df_grid_ta[df_grid_ta["val"] > 5]  # 인구 5미만 격자 제거
df_grid_ta5["DN_mean"] = df_grid_ta5["DN_mean"].apply(lambda x: 40 if x >= 40 else x)
df_grid_ta5 = df_grid_ta5[df_grid_ta5["refuge_sum"] == 0]
po_rate= df_grid_ta5.groupby("adm_dr_nm", as_index=False)["val", "po_sum"].sum()
po_rate["rate"] = po_rate["po_sum"] / po_rate["val"]
df_grid_ta5 = pd.merge(df_grid_ta5, po_rate[["adm_dr_nm", "rate"]], how="left", on="adm_dr_nm")
df_grid_ta5["rate"] = - df_grid_ta5["rate"]
df_grid_ta5.reset_index(drop = True, inplace = True)

more = (df_grid_ta5["HubDist"] > 1300)
less2 = (df_grid_ta5["HubDist"] > 500) & (df_grid_ta5["HubDist"] <= 1300)
less1 = (df_grid_ta5["HubDist"] > 0) & (df_grid_ta5["HubDist"] <= 500)
zero = (df_grid_ta5["HubDist"] == 0)

df_grid_ta5.loc[zero, "HubDist"] = 2
df_grid_ta5.loc[less1, "HubDist"] = 0
df_grid_ta5.loc[less2, "HubDist"] = 1  # 500~1300m 범주화
df_grid_ta5.loc[more, "HubDist"] = 2  # 1300m기준 거리 범주화


"""
AHP 요소 별 변수 분류 & 모델 작성
"""
ahp = [0.161, 0.185, 0.328, 0.192, 0.134]  # 기존 지진긴급해일대피장소 가중치

height = ["DN_mean"]  # 요소 별 변수 분류
pop = ["val", "exceed_sum", "rate"]
time = ["HubDist"]
condition = ["atomic"]
appointed = ["school", "park", "hotel", "public"]

ahp_scale_t = df_grid_ta5.copy()
ahp_scale_t.drop(
    ["gid", "landuse", "sido_cd", "sido_nm", "sigungu_cd", "sigungu_nm", "base_year", "adm_dr_cd", "coast", "DN",
     "DN_max", "coast_2", "adm_dr_nm", "geometry", "child", "old", "disaster", "collapse", "lbl"],
    axis=1, inplace=True)

ss = StandardScaler()
ahp_result_t = pd.DataFrame(ss.fit_transform(ahp_scale_t), columns=ahp_scale_t.columns)

df_grid_ta5["score"] = 0.161 * ahp_result_t[height].sum(axis=1) + 0.185 * ahp_result_t[pop].sum(axis=1) + 0.328 * \
                       ahp_result_t[time].sum(axis=1)
- 0.192 * ahp_result_t[condition].sum(axis=1) + 0.134 / 2 * ahp_result_t[appointed].sum(axis=1)

df_grid_ta5["score"] = df_grid_ta5["score"] + 1  # score 스케일 조정

location1 = (df_grid_ta5["school"] == 0) & (df_grid_ta5["park"] == 0) & (df_grid_ta5["hotel"] == 0) & (
        df_grid_ta5["public"] == 0) & \
            (df_grid_ta5["score"] > df_grid_ta5["score"].quantile(.7))  # score 상위30%기준
location2 = ((df_grid_ta5["school"] == 1) | (df_grid_ta5["park"] == 1) | (df_grid_ta5["hotel"] == 1) | (
        df_grid_ta5["public"] == 1))

df_grid_ta5["location"] = 99  # score 하위70%격자
df_grid_ta5.loc[location1, "location"] = 0  # 대피장소 지정대상 X(상위30%)
df_grid_ta5.loc[location2, "location"] = 1  # 대피장소 지정대상 존재

df_grid_ta5 = df_grid_ta5[df_grid_ta5["coast_2"] != 1]  # 해안선 1열 격자 제외

df_grid_loc99 = df_grid_ta5[df_grid_ta5["location"] == 99]
df_grid_loc0 = df_grid_ta5[df_grid_ta5["location"] == 0]
df_grid_loc1 = df_grid_ta5[df_grid_ta5["location"] == 1]

df_grid_loc99.to_file("C:/earthquake/result/Tsunami-EMERGENCY_ASSEMBLY_AREA/AHP_tsunami_99.shp", encoding="cp949")  # Shapefile로 저장
df_grid_loc0.to_file("C:/earthquake/result/Tsunami-EMERGENCY_ASSEMBLY_AREA/2.지진해일긴급대피장소_위치후보지(기타).shp", encoding="cp949")
df_grid_loc1.to_file("C:/earthquake/result/Tsunami-EMERGENCY_ASSEMBLY_AREA/1.지진해일긴급대피장소_위치후보지(학교_공원_건축물).shp", encoding="cp949")

sys.path.remove(PACK_DIR)

layer0 = iface.addVectorLayer("C:/earthquake/result/Tsunami-EMERGENCY_ASSEMBLY_AREA/2.지진해일긴급대피장소_위치후보지(기타).shp", "", "ogr")  # 레이어로 불러와서 띄우기
layer1 = iface.addVectorLayer("C:/earthquake/result/Tsunami-EMERGENCY_ASSEMBLY_AREA/1.지진해일긴급대피장소_위치후보지(학교_공원_건축물).shp", "", "ogr")
