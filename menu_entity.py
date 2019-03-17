from pdf_reader import find_closest_right, find_closest_down, delete_empty_names
import pandas as pd


def is_separate_price(s):
    flag = False
    numbers = sum(c.isdigit() for c in s)
    if numbers >= 0.5*len(s.replace(" ", "")):
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


def get_description_dish_price(_Dishes, _items):
    Descriptions = pd.DataFrame(columns=['name', 'x0', 'x1', 'y0', 'y1', 'height', 'width', 'page_num'])
    try:
        _Dishes = _Dishes.reset_index(drop=True)
        for i in range(0, len(_Dishes)):
            e = _Dishes.iloc[[i]]
            tmp_descr = _items[_items['height'] <= list(e['height'])[0]]
            e_down = find_closest_down(e, _Dishes)

            tmp_descr = tmp_descr[tmp_descr['page_num'] == list(e['page_num'])[0]]
            tmp_descr = tmp_descr[tmp_descr['y1'] <= list(e['y0'])[0]]

            if (len(e_down) > 0):
                tmp_descr = tmp_descr[tmp_descr['y0'] >= list(e_down['y1'])[0]]

            e_center_X = 0.5 * (list(e['x0'])[0] + list(e['x1'])[0])

            tmp_descr = tmp_descr[tmp_descr['x0'] <= e_center_X]
            tmp_descr = tmp_descr[tmp_descr['x1'] >= e_center_X]

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

                Descriptions = Descriptions.append(descr, ignore_index=True)
    except:
        print("Without descriptions")

    return Descriptions