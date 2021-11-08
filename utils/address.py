import geopandas as gpd
import shapely.geometry


def split_sido_sggnm(df):
    """
    시군구 명칭과 시도 명칭에서 각각 '시', '군' 명칭을 분리하여 반환한다

    :param df:
    :return:
    """
    if df['sggnm'] == '시흥시':
        return df['sggnm']

    if df['sidonm'].endswith('시'):
        return df['sidonm']
    elif '시' in df['sggnm']:
        return f"{df['sggnm'].split('시')[0]}시"
    else:
        return df['sggnm']


def split_sggnm_gu(df):
    """
    시군구 명칭에서 '구' 명칭을 분리하여 반환한다

    :param df:
    :return:
    """
    if df['sggnm'] == '시흥시':
        return None

    if '시' in df['sggnm']:
        return f"{df['sggnm'].split('시')[1]}"
    elif df['sggnm'].endswith('구'):
        return df['sggnm']
    else:
        return ''


def make_full_address(df):
    """
    시군, 구, 동 명칭을 합하여 원본 주소를 생성하여 반환한다

    :param df:
    :return:
    """
    if df['Gu']:
        if df['Sido'] != df['Sigun']:
            address = f'{df["Sido"]} {df["Sigun"]} {df["Gu"]} {df["Dong"]}'
        else:
            address = f'{df["Sigun"]} {df["Gu"]} {df["Dong"]}'
    else:
        if df['Sido'] != df['Sigun']:
            address = f'{df["Sido"]} {df["Sigun"]} {df["Dong"]}'
        else:
            address = f'{df["Sigun"]} {df["Dong"]}'
    return address


def make_dataset(filename: str):
    """
    geojson 파일을 업로드 하기 위해 전처리 후 데이터를 반환한다

    :param filename:
    :return:
    """

    gdf = gpd.read_file(filename)
    gdf['geometry'] = gdf['geometry'].apply(lambda x: shapely.geometry.mapping(x))

    gdf['adm_nm'] = gdf['adm_nm'].str.replace('·', ',')
    gdf['Sido'] = gdf['sidonm']
    gdf['Sigun'] = gdf.apply(split_sido_sggnm, axis=1)
    gdf['Gu'] = gdf.apply(split_sggnm_gu, axis=1)
    gdf['Dong'] = gdf['adm_nm'].apply(lambda x: x.split()[-1])
    gdf['Address'] = gdf.apply(make_full_address, axis=1)
    gdf.drop(['adm_nm', 'sidonm', 'sggnm', 'sgg', 'sido'], axis=1, inplace=True)

    data = gdf.to_dict('records')

    return data
