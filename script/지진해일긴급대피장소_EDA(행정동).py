"""
Author: NY.Kim
Date : 2019-12-23
생활인구, 지진해일긴급대피장소 EDA 결과 저장 program
"""
import sys
import platform

if platform.architecture()[0]=='32bit':
    PACK_DIR ='C:/earthquake/package/32bit/site-packages'
else:
    PACK_DIR ='C:/earthquake/package/64bit/site-packages'
sys.path.append(PACK_DIR)

import numpy as np
import pandas as pd
import os
import glob
import matplotlib.pyplot as plt
import geopandas as gpd
import seaborn as sns
sns.set_style("whitegrid")
from datetime import datetime
from matplotlib import rc
import csv
#EDA 결과 저장 폴더 생성

try:
    os.makedirs("C:/earthquake/result/EDA/해일대피장소")
except OSError:
    pass
    
"""
분석 대상 구/군 입력
"""
gu = "구/군을 입력하세요"

try:
    os.makedirs("C:/earthquake/result/EDA/해일대피장소/{0}".format(gu))
except OSError:
    pass


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

"""
데이터 불러오기 & 데이터프레임화
"""
for filename in all_files:
    try:
        with open(filename,'r',encoding='cp949') as f:
            read_file(f.read())
    except UnicodeDecodeError:
        with open(filename,'r',encoding='UTF-8') as f:
            read_file(f.read())

df_living = pd.concat(li, axis=0, ignore_index=True)  # 생활인구 DATA 불러오기

col = ["STD_YM", "INDEX_ID", "TIME", "H_MAX_POP", "W_MAX_POP", "V_MAX_POP", "F_MAX_POP", "A_MAX_POP"]
df_living = df_living[col]

names = ['STD_YM', 'INDEX_ID', 'TIME', 'H_MAX', 'W_MAX', 'V_MAX', 'F_MAX', 'A_MAX']

df_living.columns = names  # 컬럼 이름 변경

path = "C:/earthquake/result/Tsunami-EMERGENCY_ASSEMBLY_AREA/AHP.shp"  # 격자 경로 설정
shape_file = gpd.read_file(path, encoding="cp949")  # 격자 Data 불러오기
df_grid = shape_file.copy()
del df_grid["geometry"]
df_grid = df_grid.fillna(0)

name_map = df_grid[["sigungu_cd", "sigungu_nm", "adm_dr_cd", "adm_dr_nm"]].drop_duplicates()
name_map.index = range(len(name_map))  # 코드 매핑용 Data생성


"""
데이터 전처리
"""
df_living["STD_YM"] = pd.to_datetime(df_living["STD_YM"], format='%Y%m')  # 날짜형식으로 변환
df_living['year'] = df_living['STD_YM'].map(lambda x: x.year).astype("object")
df_living["month"] = df_living['STD_YM'].map(lambda x: x.month).astype("object")

df_grid["lbl"] = df_grid["lbl"].replace("N/A", 0)
df_grid["lbl"] = df_grid["lbl"].astype("float").astype("int")

df_grid_code = df_grid[["gid", "sigungu_cd", "adm_dr_cd", "coast", "refuge_sum", "po_sum", "lbl", "val"]].drop_duplicates("gid", keep="first")
df_grid_code = df_grid_code.rename(columns={"gid": "INDEX_ID"})

a = df_living["INDEX_ID"].unique()  # 미확인 격자 확인
b = df_grid["gid"].unique()
del_idx = list(set(a) - set(b))

df_living_n = df_living[~df_living["INDEX_ID"].isin(del_idx)]  # 분석 대상이 아닌 격자 제거

df_living_f = pd.merge(df_living_n, df_grid_code, how="left")  # 시군구/행정동 코드가 포함된 Data생성
df_living_f = pd.merge(df_living_f, name_map, how="left")
df_living_f = df_living_f[df_living_f["coast"] == 1]  # 해안가 격자 선택
df_living_f = df_living_f.loc[df_living_f["sigungu_nm"] == gu]  # 시군구 선택
df_living_f.index = range(len(df_living_f))

living_index_month_max = df_living_f.groupby(["INDEX_ID", "year", "month"], as_index=False)["A_MAX"].max()
living_index_max_a = living_index_month_max.loc[living_index_month_max.groupby("INDEX_ID")["A_MAX"].idxmax()]
living_index_max_a.index = range(len(living_index_max_a))
living_index_max_a = pd.merge(living_index_max_a, df_grid_code, how="left")
living_index_max = pd.merge(living_index_max_a, name_map, how="left")  # 격자별 생활인구 최대값


"""
생활인구 EDA
"""
try:
    today = datetime.today().strftime("%y%m%d")

    rc('font', family='Malgun Gothic')  # 맑은 고딕 폰트 적용으로 한글 깨짐 방지
    plt.rcParams["figure.figsize"] = [12, 8]  # 기본 그래프 사이즈 설정

    dong_p = living_index_max.groupby(["adm_dr_nm"], as_index=False)[["val", "lbl"]].sum()
    dong_p.to_csv("C:/earthquake/result/EDA/해일대피장소/{0}/행정동별_주민_생활인구_비교{1}.csv".format(gu, today), encoding="cp949")
    dong = dong_p.sort_values(by="val", ascending=False).adm_dr_nm.tolist()
    dong_p = pd.melt(dong_p, id_vars="adm_dr_nm", var_name="class", value_name="people")
    g = sns.catplot(x="adm_dr_nm", y="people", hue="class", data=dong_p, kind="bar",
                    height=7.5, aspect=1.5, palette="Blues", order=dong, legend_out=False)
    plt.title("행정동별 생활인구/주민등록인구 비교", fontsize=15, y=1.03)
    plt.xlabel("", fontsize=11)
    plt.xticks(fontsize=11, rotation=25)
    plt.ylabel("")
    leg = g.axes.flat[0].get_legend()
    leg.set_title("")
    new_labels = ['생활인구', '주민등록인구']
    for t, l in zip(leg.texts, new_labels): t.set_text(l)
    plt.savefig("C:/earthquake/result/EDA/해일대피장소/{0}/행정동별_주민_생활인구_비교{1}.png".format(gu, today), bbox_inches='tight')
    plt.close()

    dong_p = living_index_max.groupby(["adm_dr_nm"], as_index=False)[["lbl", "refuge_sum"]].sum()
    dong_p.to_csv("C:/earthquake/result/EDA/해일대피장소/{0}/행정동별_주민등록인구_해일대피_비교{1}.csv".format(gu, today), encoding="cp949")
    order = dong_p.sort_values(by=["lbl"], ascending=False).adm_dr_nm.tolist()
    dong_p = pd.melt(dong_p, id_vars="adm_dr_nm", var_name="class", value_name="people")
    mask = dong_p["class"].isin(['refuge_sum'])
    mask_p_mean = dong_p[mask].people.mean()

    if mask_p_mean != 0:
        scale = int(dong_p[~mask].people.mean() / mask_p_mean)
    else:
        scale = 0

    dong_p.loc[mask, 'people'] = dong_p.loc[mask, 'people'] * scale
    fig, ax1 = plt.subplots()
    g = sns.barplot(x="adm_dr_nm", y="people", hue="class", data=dong_p, palette="Blues",
                    order=order, ax=ax1)
    ax2 = ax1.twinx()
    ax2.set_ylim(ax1.get_ylim())

    if mask_p_mean != 0:
        y_labels = np.round(ax1.get_yticks() / scale).astype(int)
    else:
        y_labels = range(0,len(ax1.get_yticks()))
    ax2.set_yticklabels(y_labels)
    ax2.set_ylabel("대피장소")
    ax2.grid(False)
    ax1.set(xlabel="", ylabel="")
    ax1.set_xticklabels(ax1.get_xticklabels(), rotation=25)
    leg = g.axes.get_legend()
    leg.set_title("")
    new_labels = ['주민등록인구', '대피장소']
    for t, l in zip(leg.texts, new_labels): t.set_text(l)
    plt.title("행정동별 주민등록인구/해일대피장소 비교", fontsize=15, y=1.03)
    plt.savefig("C:/earthquake/result/EDA/해일대피장소/{0}/행정동별_주민등록인구_해일대피_비교{1}.png".format(gu, today))
    plt.close()

    dong_p = living_index_max.groupby(["adm_dr_nm"], as_index=False)[["val", "refuge_sum"]].sum()
    dong_p.to_csv("C:/earthquake/result/EDA/해일대피장소/{0}/행정동별_생활인구_해일대피_비교{1}.csv".format(gu, today), encoding="cp949")
    order = dong_p.sort_values(by=["val"], ascending=False).adm_dr_nm.tolist()
    dong_p = pd.melt(dong_p, id_vars="adm_dr_nm", var_name="class", value_name="people")
    mask = dong_p["class"].isin(['refuge_sum'])
    mask_p_mean = dong_p[mask].people.mean()

    if mask_p_mean != 0:
        scale = int(dong_p[~mask].people.mean() / mask_p_mean)
    else:
        scale = 0
    dong_p.loc[mask, 'people'] = dong_p.loc[mask, 'people'] * scale
    fig, ax1 = plt.subplots()
    g = sns.barplot(x="adm_dr_nm", y="people", hue="class", data=dong_p, palette="Blues",
                    order=order, ax=ax1)
    ax1.set_ylabel('인구수')
    ax2 = ax1.twinx()
    ax2.set_ylim(ax1.get_ylim())
    if mask_p_mean != 0:
        y_labels = np.round(ax1.get_yticks() / scale).astype(int)
    else:
        y_labels = range(0,len(ax1.get_yticks()))
    ax2.set_yticklabels(y_labels)
    ax2.set_ylabel("대피장소")
    ax2.grid(False)
    ax1.set(xlabel="", ylabel="")
    ax1.set_xticklabels(ax1.get_xticklabels(), rotation=25)
    leg = g.axes.get_legend()
    leg.set_title("")
    new_labels = ['생활인구', '대피장소']
    for t, l in zip(leg.texts, new_labels): t.set_text(l)
    plt.title("행정동별 생활인구/해일대피장소 비교", fontsize=15, y=1.03)
    plt.savefig("C:/earthquake/result/EDA/해일대피장소/{0}/행정동별_생활인구_해일대피_비교{1}.png".format(gu, today))
    plt.close()

    dong_p = living_index_max.groupby(["adm_dr_nm"], as_index=False)[["lbl", "po_sum"]].sum()
    dong_p.to_csv("C:/earthquake/result/EDA/해일대피장소/{0}/행정동별_주민등록인구_수용가능인구_비교{1}.csv".format(gu, today), encoding="cp949")
    order = dong_p.sort_values(by=["lbl"], ascending=False).adm_dr_nm.tolist()
    dong_p = pd.melt(dong_p, id_vars="adm_dr_nm", var_name="class", value_name="people")
    plt.rcParams["figure.figsize"] = (12,8)
    g = sns.catplot(x="adm_dr_nm", y="people", hue="class", data=dong_p, kind="bar",
                height=7.5, aspect=1.5, palette="Blues", order=order, legend_out=False)
    plt.xlabel("", fontsize=11)
    plt.xticks(fontsize=11, rotation=25)
    plt.ylabel("")
    leg = g.axes.flat[0].get_legend()
    leg.set_title("")
    new_labels = ['주민등록인구', '수용가능인구']
    for t, l in zip(leg.texts, new_labels): t.set_text(l)
    plt.title("행정동별 주민등록/수용가능인구 비교", fontsize=15, y=1.03)
    plt.savefig("C:/earthquake/result/EDA/해일대피장소/{0}/행정동별_주민등록인구_수용가능인구_비교{1}.png".format(gu, today), bbox_inches='tight')
    plt.close()

    dong_p = living_index_max.groupby(["adm_dr_nm"], as_index=False)[["val", "po_sum"]].sum()
    dong_p.to_csv("C:/earthquake/result/EDA/해일대피장소/{0}/행정동별_생활인구_수용가능인구_비교{1}.csv".format(gu, today), encoding="cp949")
    order = dong_p.sort_values(by=["val"],ascending=False).adm_dr_nm.tolist()
    dong_p = pd.melt(dong_p, id_vars="adm_dr_nm", var_name="class", value_name="people")
    plt.rcParams["figure.figsize"] = (12,8)
    g = sns.catplot(x="adm_dr_nm", y="people", hue="class", data=dong_p, kind="bar",
                height=7.5, aspect=1.5, palette="Blues", order=order, legend_out=False)
    plt.xlabel("", fontsize=11)
    plt.xticks(fontsize=11, rotation=25)
    plt.ylabel("")
    leg = g.axes.flat[0].get_legend()
    leg.set_title("")
    new_labels = ['생활인구', '수용가능인구']
    for t, l in zip(leg.texts, new_labels): t.set_text(l)
    plt.title("행정동별 생활인구/수용가능인구 비교", fontsize=15, y=1.03)
    plt.savefig("C:/earthquake/result/EDA/해일대피장소/{0}/행정동별_생활인구_수용가능인구_비교{1}.png".format(gu, today), bbox_inches='tight')
    plt.close()

    living_month_time = df_living_f.groupby(["month", "TIME"], as_index=False)["A_MAX"].sum()
    living_month_time["month"] = living_month_time["month"].map(lambda x: str(x) + "월").astype("object")
    sns.lineplot(x="TIME", y="A_MAX", data=living_month_time)
    plt.title("전반적인 총 생활인구 양상", fontsize=15, y=1.03)
    plt.xlim(0, 23)
    plt.xlabel("시간")
    plt.ylabel("")
    plt.savefig("C:/earthquake/result/EDA/해일대피장소/{0}/총_생활인구_양상{1}.png".format(gu, today))
    plt.close()

    plt.rcParams["figure.figsize"] = [12, 10]
    living_month_time = df_living_f.groupby(["STD_YM", "TIME"], as_index=False)["A_MAX"].sum()
    living_month_time["STD_YM"] = living_month_time["STD_YM"].astype("str").map(lambda x: x[:-3])
    living_month_time.to_csv("C:/earthquake/result/EDA/해일대피장소/{0}/월_시간대_생활인구_현황{1}.csv".format(gu, today), encoding="cp949")
    sns.lineplot(x="TIME", y="A_MAX", hue="STD_YM", data=living_month_time, palette="Paired")
    plt.title("월/시간대 별 생활인구 현황", fontsize=15, y=1.03)
    plt.ylabel("")
    plt.xlim(0, 23)
    plt.legend().texts[0].set_text('')
    plt.savefig("C:/earthquake/result/EDA/해일대피장소/{0}/월_시간대_생활인구_현황{1}.png".format(gu, today))
    plt.close()

    living_month_time = df_living_f.groupby(["month", "TIME"], as_index=False)["H_MAX"].sum()
    living_month_time["month"] = living_month_time["month"].map(lambda x: str(x) + "월").astype("object")
    living_month_time.to_csv("C:/earthquake/result/EDA/해일대피장소/{0}/월_시간대_거주인구_현황{1}.csv".format(gu, today), encoding="cp949")
    sns.lineplot(x="TIME", y="H_MAX", hue="month", data=living_month_time, palette="Paired")
    plt.title("월/시간대 별 거주인구 현황", fontsize=15, y=1.03)
    plt.ylabel("")
    plt.xlim(0, 23)
    plt.legend().texts[0].set_text('')
    plt.savefig("C:/earthquake/result/EDA/해일대피장소/{0}/월_시간대_거주인구_현황{1}.png".format(gu, today))
    plt.close()

    living_month_time = df_living_f.groupby(["month", "TIME"], as_index=False)["W_MAX"].sum()
    living_month_time["month"] = living_month_time["month"].map(lambda x: str(x) + "월").astype("object")
    living_month_time.to_csv("C:/earthquake/result/EDA/해일대피장소/{0}/월_시간대_근무인구_현황{1}.csv".format(gu, today), encoding="cp949")
    sns.lineplot(x="TIME", y="W_MAX", hue="month", data=living_month_time, palette="Paired")
    plt.title("월/시간대 별 근무인구 현황", fontsize=15, y=1.03)
    plt.ylabel("")
    plt.xlim(0, 23)
    plt.legend().texts[0].set_text('')
    plt.savefig("C:/earthquake/result/EDA/해일대피장소/{0}/월_시간대_근무인구_현황{1}.png".format(gu, today))
    plt.close()

    living_month_time = df_living_f.groupby(["month", "TIME"], as_index=False)["V_MAX"].sum()
    living_month_time["month"] = living_month_time["month"].map(lambda x: str(x) + "월").astype("object")
    living_month_time.to_csv("C:/earthquake/result/EDA/해일대피장소/{0}/월_시간대_방문인구_현황{1}.csv".format(gu, today), encoding="cp949")
    sns.lineplot(x="TIME", y="V_MAX", hue="month", data=living_month_time, palette="Paired")
    plt.title("월/시간대 별 방문인구 현황", fontsize=15, y=1.03)
    plt.ylabel("")
    plt.xlim(0, 23)
    plt.legend().texts[0].set_text('')
    plt.savefig("C:/earthquake/result/EDA/해일대피장소/{0}/월_시간대_방문인구_현황{1}.png".format(gu, today))
    plt.close()

    living_month_time = df_living_f.groupby(["month", "TIME"], as_index=False)["F_MAX"].sum()
    living_month_time["month"] = living_month_time["month"].map(lambda x: str(x) + "월").astype("object")
    living_month_time.to_csv("C:/earthquake/result/EDA/해일대피장소/{0}/월_시간대_외국인인구_현황{1}.csv".format(gu, today), encoding="cp949")
    sns.lineplot(x="TIME", y="F_MAX", hue="month", data=living_month_time, palette="Paired")
    plt.title("월/시간대 별 외국인 현황", fontsize=15, y=1.03)
    plt.ylabel("")
    plt.xlim(0, 23)
    plt.legend().texts[0].set_text('')
    plt.savefig("C:/earthquake/result/EDA/해일대피장소/{0}/월_시간대_외국인인구_현황{1}.png".format(gu, today))
    plt.close()

    plt.rcParams["figure.figsize"] = [12, 8]
    living_time_index = df_living_f.loc[df_living_f.groupby(["INDEX_ID", "TIME"])["A_MAX"].idxmax()]
    living_time_index.index = range(len(living_time_index))

    living_time_si = living_time_index.groupby(["adm_dr_nm", "TIME"], as_index=False)["A_MAX"].sum()
    living_time_si.index = range(len(living_time_si))
    living_time_si.to_csv("C:/earthquake/result/EDA/해일대피장소/{0}/행정동_시간대별_생활인구_현황{1}.csv".format(gu, today), encoding="cp949")


    g = sns.lineplot(x="TIME", y="A_MAX", hue="adm_dr_nm", data=living_time_si, palette="Paired")
    plt.title("행정동/시간대 별 생활인구 현황", fontsize=15, y=1.03)
    plt.xlim(0, 23)
    plt.ylabel("")
    plt.legend(bbox_to_anchor=(1.04, 1), loc="upper left").texts[0].set_text('행정동')
    plt.savefig("C:/earthquake/result/EDA/해일대피장소/{0}/행정동_시간대별_생활인구_현황{1}.png".format(gu, today), bbox_inches="tight")
    plt.close()

    living_month_index = df_living_f.loc[df_living_f.groupby(["INDEX_ID", "STD_YM"])["A_MAX"].idxmax()]
    living_month_index.index = range(len(living_month_index))
    living_month_si = living_month_index.groupby(["adm_dr_nm", "STD_YM"], as_index=False)["A_MAX"].sum()
    living_month_si["STD_YM"] = living_month_si["STD_YM"].astype("str").map(lambda x: x[:-3])
    living_month_si.to_csv("C:/earthquake/result/EDA/해일대피장소/{0}/행정동_월별_생활인구_현황{1}.csv".format(gu, today), encoding="cp949")

    sns.lineplot(x="STD_YM", y="A_MAX", hue="adm_dr_nm", data=living_month_si, palette="Paired")
    plt.title("행정동/월 별 생활인구 현황", fontsize=15, y=1.03)
    plt.xlabel("")
    plt.xticks(rotation=25)
    plt.ylabel("")
    plt.legend(bbox_to_anchor=(1.04, 1), loc="upper left").texts[0].set_text('행정동')
    plt.savefig("C:/earthquake/result/EDA/해일대피장소/{0}/행정동_월별_생활인구_현황{1}.png".format(gu, today), bbox_inches="tight")
    plt.close()

    dong_p = living_index_max.groupby(["adm_dr_nm"], as_index=False)[["A_MAX", "val"]].sum()
    dong_p = dong_p.sort_values(by="A_MAX", ascending=False)
    dong_p.index = range(len(dong_p))
    order = dong_p.sort_values(by=["A_MAX"], ascending=False).adm_dr_nm.tolist()
    adm_dr_nm = order
    refuge_sum = list(dong_p["val"])
    sns.lineplot(x="adm_dr_nm", y="val", data=dong_p, color="orange", marker='o', markersize=10, linewidth=5,
                 sort=False)
    sns.barplot(x="adm_dr_nm", y="A_MAX", data=dong_p, color="navy", order=order)
    plt.title("행정동별 생활인구 비교", fontsize=15, y=1.03)
    plt.xlabel("")
    plt.xticks(fontsize=11, rotation=25)
    plt.ylabel("")
    plt.legend(labels=["생활인구(백분위적용)", "생활인구"])
    plt.savefig("C:/earthquake/result/EDA/해일대피장소/{0}/행정동_분위수_생활인구_현황{1}.png".format(gu, today), bbox_inches="tight")
    plt.close()
    
    sys.path.remove(PACK_DIR)
except:
    err_line = 'err_line == {}'.format(sys.exc_info()[-1].tb_lineno)
    err_msg = '  err_msg == ' + ' '.join(map(str, sys.exc_info()[:2])).replace('\'', '')
    print(err_line, '  err_msg=', err_msg)
    sys.path.remove(PACK_DIR)