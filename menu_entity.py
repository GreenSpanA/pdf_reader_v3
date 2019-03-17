from pdf_reader import find_closest_right


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