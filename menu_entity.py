from pdf_reader import find_closest_right, find_closest_down, delete_empty_names
import pandas as pd
import math


def is_separate_price(s):
    flag = False
    numbers = sum(c.isdigit() for c in s)
    s = s.replace(" ", "")
    s = s.strip()
    if numbers >= 0.5*len(s) and s[-1].isdigit():
        flag = True
    return flag


def is_dish_with_price(e):
    flag = False
    try:
        if len(list(e['name'])[0].strip()) > 5 and is_separate_price(list(e['name'])[0].split()[-1]):
            flag = True
    except:
        flag = False
    return flag


def is_dish_then_price(e, df):
    flag = False
    try:
        e_right = find_closest_right(e, df, is_same_level=True)
        if len(list(e['name'])[0]) > 5 and is_separate_price(list(e_right['name'])[0].split()[-1]):
            flag = True
    except:
        flag = False
    return flag


def cut_prices_form_df(df):
    df['flag'] = 1
    df = df.reset_index(drop=True)
    for i in range(0, len(df)):
        if is_separate_price(list(df.iloc[[i]]['name'])[0]):
            df.loc[i, 'flag'] = 0
    df = df[df['flag'] == 1]
    df = df.drop(columns=['flag'])
    df = df.reset_index(drop=True)
    return df


def get_items_dish_price(df):
    df['flag'] = 0
    df = df.reset_index(drop=True)

    for i in range(0, len(df)):
        if is_dish_then_price(df.iloc[[i]], df):
            df.loc[i, 'flag'] = 1

    df = df[df['flag'] == 1]
    df = df.drop(columns=['flag'])
    df = df.reset_index(drop=True)
    return df


def get_description_dish_price(_Dishes, _items, _Prices):
    Descriptions = pd.DataFrame(columns=['name', 'x0', 'x1', 'y0', 'y1', 'height', 'width', 'page_num'])
    try:
        _Dishes = _Dishes.reset_index(drop=True)
        for i in range(0, len(_Dishes)):
            e = _Dishes.iloc[[i]]
            tmp_descr = _items[_items['height'] < list(e['height'])[0]]
            e_down = find_closest_down(e, _Dishes)
            tmp_descr = tmp_descr[tmp_descr['page_num'] == list(e['page_num'])[0]]
            tmp_descr = tmp_descr[tmp_descr['y1'] <= 0.5 * (list(e['y0'])[0] + list(e['y1'])[0])]

            if (len(e_down) > 0):
                tmp_descr = tmp_descr[tmp_descr['y0'] >= 0.5 * (list(e_down['y0'])[0] + list(e_down['y1'])[0])]

            tmp_descr = tmp_descr[tmp_descr['x0'] < list(e['x1'])[0]]
            tmp_descr = tmp_descr[tmp_descr['x1'] > list(e['x0'])[0]]
            a = tmp_descr.index.values
            a = a - min(a)
            if len(a) - sum(a) != 1:
                tmp_descr = tmp_descr.iloc[[min(a)]]

            tmp_descr = delete_empty_names(tmp_descr)
            tmp_descr = tmp_descr.reset_index(drop=True)

            if len(tmp_descr) > 0:
                tmp_name = ''
                for j in range(0, len(tmp_descr)):
                    tmp_name = tmp_name + tmp_descr.iloc[j]['name']

                descr = pd.DataFrame({
                    'name': [tmp_name],
                    'x0': [min(tmp_descr['x0'])],
                    'x1': [max(tmp_descr['x1'])],
                    'y0': [min(tmp_descr['y0'])],
                    'y1': [max(tmp_descr['y1'])],
                    'height': [max(tmp_descr['height'])],
                    'width': [max(tmp_descr['width'])],
                    'page_num': [min(tmp_descr['page_num'])]
                })

                e_down_right = find_closest_right(descr, _Prices, is_same_level=True)
                if len(e_down_right) > 0 and is_separate_price(e_down_right.iloc[0]['name']):
                    continue
            Descriptions = Descriptions.append(descr, ignore_index=True)
    except:
        print("Without descriptions")
    return Descriptions


def get_prices_dish_price(_Dishes, _items):
    Prices = pd.DataFrame(columns=['name', 'x0', 'x1', 'y0', 'y1', 'height', 'width', 'page_num'])
    try:
        _Dishes = _Dishes.reset_index(drop=True)
        for i in range(0, len(_Dishes)):
            e = _Dishes.iloc[[i]]
            e_right = find_closest_right(e, _items, is_same_level=True)
            if is_separate_price(list(e_right['name'])[0]):
                p = pd.DataFrame({
                    'name': [list(e_right['name'])[0]],
                    'x0': [list(e_right['x0'])[0]],
                    'x1': [list(e_right['x1'])[0]],
                    'y0': [list(e_right['y0'])[0]],
                    'y1': [list(e_right['y1'])[0]],
                    'height': [list(e_right['height'])[0]],
                    'width': [list(e_right['width'])[0]],
                    'page_num': [list(e_right['page_num'])[0]]
                })
                Prices = Prices.append(p, ignore_index=True)

    except:
        print("Without prices")
    return Prices

def get_post_prices_dish_price(_Prices, median_H):
    _Prices = _Prices.reset_index(drop=True)
    # median_H = _Prices['height'].median()
    prices_n = pd.DataFrame(columns=['name', 'x0', 'x1', 'y0', 'y1', 'height', 'width', 'page_num'])
    try:
        for i in range(0, len(_Prices)):
            big_prices = _Prices.iloc[[i]]
            big_prices = big_prices.reset_index(drop=True)
            height_a = _Prices.iloc[i]['height'] / len(list(_Prices.iloc[[i]]['name'])[0])
            #tmp_len = math.ceil(list(big_prices['height'])[0] / median_H)
            tmp_len = int(round(list(big_prices['height'])[0] / median_H))

            if tmp_len > 1:
                for j in range(0, tmp_len):
                    tmp_x0, tmp_x1 = _Prices.iloc[i]['x0'], _Prices.iloc[i]['x1']
                    tmp_y0, tmp_y1 = _Prices.iloc[i]['y1'] - (j + 1) * height_a, _Prices.iloc[i]['y1'] - j * height_a
                    tmp_price = pd.DataFrame({
                        'name': [_Prices.iloc[i]['name'][j]],
                        'x0': [tmp_x0],
                        'x1': [tmp_x1],
                        'y0': [tmp_y0],
                        'y1': [tmp_y1],
                        'height': [height_a],
                        'width': [list(_Prices.iloc[[i]]['width'])[0]],
                        'page_num': [list(_Prices.iloc[[i]]['page_num'])[0]]})
                    prices_n = prices_n.append(tmp_price, ignore_index=True)
            else:
                tmp_price = pd.DataFrame({
                    'name': [list(_Prices.iloc[[i]]['name'])[0]],
                    'x0': [list(_Prices.iloc[[i]]['x0'])[0]],
                    'x1': [list(_Prices.iloc[[i]]['x1'])[0]],
                    'y0': [list(_Prices.iloc[[i]]['y0'])[0]],
                    'y1': [list(_Prices.iloc[[i]]['y1'])[0]],
                    'height': [list(_Prices.iloc[[i]]['height'])[0]],
                    'width': [list(_Prices.iloc[[i]]['width'])[0]],
                    'page_num': [list(_Prices.iloc[[i]]['page_num'])[0]]})
                prices_n = prices_n.append(tmp_price, ignore_index=True)
    except:
        print("Error with post price's processing ")
    return prices_n

def collapse_prices(df):
    df = df.reset_index(drop=True)
    # Collapse rows
    df['flag'] = 1
    for i in range(0, len(df)):
        e = df.iloc[[i]]
        tmp_y_mean = 0.5*(e.iloc[0]['y0'] + e.iloc[0]['y1'])
        df_temp = df[df['page_num'] == e.iloc[0]['page_num']]
        df_temp = df_temp[(df_temp['y0'] <= tmp_y_mean) & (df_temp['y1'] >= tmp_y_mean)]
        #print("For iteration %s count is %s" % (i, len(df_temp)))
        df_temp = df_temp[(df_temp['x0'] <= e.iloc[0]['x1']) & (df_temp['x0'] > e.iloc[0]['x0'])]
        #print(len(df_temp))
        if len(df_temp) == 0:
            continue
        else:
            flag_index = df_temp.index.values[0]
            df.loc[i, 'name'] = str(df.loc[i, 'name']) + str(df_temp.iloc[0]['name'])
            df.loc[i, 'x1'] = df_temp.iloc[0]['x1']
            df.loc[i, 'y0'] = min(df_temp.iloc[0]['y0'],  df.loc[i, 'y0'])
            df.loc[i, 'y1'] = max(df_temp.iloc[0]['y1'],  df.loc[i, 'y1'])
            df.loc[flag_index, 'flag'] = 0

    df = df[df['flag'] == 1]
    df = df.drop(columns=['flag'])
    df = df.reset_index(drop=True)
    return df
