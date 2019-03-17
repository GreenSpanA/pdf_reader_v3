import pandas as pd
import pdfquery
import re
import numpy as np


def single_file_coordinates(pdf_menu_file):
    # create tree of elements
    menu_tree = pdfquery.PDFQuery(pdf_menu_file)
    menu_tree.load()

    # number of pages in the pdf_menu_file
    num_pages = len(menu_tree.tree.xpath('//*/LTPage'))

    print('number of pages', num_pages)

    menu_pd = pd.DataFrame(
        columns=['items', 'height', 'x0', 'x1', 'y0', 'y1', 'page_num'])

    for page_num in range(1, num_pages + 1):

        selector = '//LTPage[@pageid = "' + str(page_num) + '"]//*'

        treeExtract = menu_tree.tree.xpath(selector)

        menu_pd_page = single_page_coordinates(treeExtract, menu_tree)

        if menu_pd_page.shape[0] != 0:

            menu_pd_page['page_num'] = page_num

            menu_pd = pd.concat([menu_pd, menu_pd_page])

        else:
            menu_pd = pd.DataFrame()

    return menu_pd


def single_page_coordinates(treeExtract, menu_tree):
    start = '//'
    box = '/@bbox'
    t = '/text()'
    h = '/@height'

    H = []
    T = []
    B = []

    X0 = []
    X1 = []
    Y0 = []
    Y1 = []

    p = re.compile(r'\[|]')
    p1 = re.compile('Element ([a-z]+) at', re.I)

    elements = [
        p1.search(str(t)).group(1) for t in treeExtract if p1.search(str(t))
    ]
    elements = set(elements)
    elements = [
        l for l in elements if l not in [
            'LTFigure', 'LTImage', 'LTPage', 'pdfxml', 'LTRect', 'LTLine',
            'LTCurve'
        ]
    ]

    if elements != []:

        for e in elements:

            bbox = menu_tree.tree.xpath(start + e + box)
            text = menu_tree.tree.xpath(start + e + t)
            height = menu_tree.tree.xpath(start + e + h)

            text = [str(t).strip() for t in text]
            height = [float(str(h)) for h in height]

            x0 = []
            x1 = []
            y0 = []
            y1 = []

            for bb in bbox:
                b = str(bb)
                coords = p.sub('', b).split(',')
                coords = [float(c.strip()) for c in coords]
                x0.append(coords[0])
                x1.append(coords[1])
                y0.append(coords[2])
                y1.append(coords[3])

            H.extend(height)
            T.extend(text)
            X0.extend(x0)
            X1.extend(x1)
            Y0.extend(y0)
            Y1.extend(y1)

        menu_pd = pd.DataFrame()

        menu_pd['items'] = T
        menu_pd['height'] = H
        menu_pd['x0'] = X0
        menu_pd['x1'] = X1
        menu_pd['y0'] = Y0
        menu_pd['y1'] = Y1

        menu_pd.drop_duplicates(inplace=True)
        menu_pd.sort_values(by=['x1', 'x0'], ascending=False, inplace=True)
        menu_pd.reset_index(inplace=True, drop=True)

        empty = []
        for row in menu_pd.itertuples():
            if row[1] == '':
                empty.append(row[0])
        menu_pd.drop(menu_pd.index[empty], inplace=True)
        menu_pd.reset_index(inplace=True, drop=True)

    else:

        menu_pd = pd.DataFrame()

    return menu_pd


def standalone_letters(menu):
    S = []
    height = []
    index = []
    items = []
    prices = []
    page = []
    x0 = []
    x1 = []
    y0 = []
    y1 = []

    SFL_main = pd.DataFrame(
        columns=['items', 'height', 'x0', 'x1', 'y0', 'y1'])

    # regex to extract price
    price_reg = re.compile(r"(.*?)(([£$]*[0-9]+[.,]*[0-9]{,2})$)", re.I)

    for row in menu.itertuples():

        try:

            if len(row[1]) == 1:
                two = menu[menu['x1'] == row[4]]
                two = two.sort_values(by='x0')

                #indices of each row of 'two', which need to be removed from 'menu'
                S.extend(list(two.index))

                two.reset_index(inplace=True, drop=True)
                count = 0
                while count < two.shape[0] - 1:
                    x_first = two.iloc[count, 0]
                    x_last = two.iloc[count + 1, 0]
                    item = x_first + x_last

                    items.append(item)

                    # height of the second in two
                    height.append(two.loc[count + 1, 'height'])

                    # index is the index row[0]
                    #index.append(row[2])

                    # page number is row[4]
                    #page.append(row[4])

                    # x0 is from the standalone letter
                    x0.append(two.loc[count, 'x0'])

                    # x1 is from the second part
                    x1.append(two.loc[count + 1, 'x1'])

                    # y0 is from the second part
                    y0.append(two.loc[count + 1, 'y0'])

                    # y1 is from the second part
                    y1.append(two.loc[count + 1, 'y1'])

                    count += 2
        except:
            pass

    SFL = pd.DataFrame()
    SFL['height'] = height
    SFL['items'] = items
    SFL['x0'] = x0
    SFL['x1'] = x1
    SFL['y0'] = y0
    SFL['y1'] = y1

    # delete rows from self.menu_pd, which have the same  indices as two
    # menuPd now contains one
    menu1 = menu
    menu1.drop(menu1.index[S], inplace=True)
    menu1 = pd.concat([menu1, SFL], ignore_index=True)
    menu1 = menu1.sort_values(by='x1', ascending=False)
    menu1.reset_index(inplace=True, drop=True)

    return menu1


def get_name(tmp_str):
    if len(re.findall(r'"([^"]*)"', tmp_str)) == 0:
        tmp_str = re.findall(r'\#(.+)\#',
                             tmp_str.translate(str.maketrans({
                                 "'": '#'
                             })))[0]
    else:
        tmp_str = re.findall(r'"([^"]*)"', tmp_str)[0]
    tmp_str = tmp_str.replace("\\n", "")
    return tmp_str


def get_coordinates(tmp_str):
    tmp_str = re.findall(r'\s([\d\.\,\-]+)\s', tmp_str)[0]
    tmp_coord = tmp_str.split(",")
    return [(lambda x: round(float(x),3))(x) for x in tmp_coord]


def get_diff3(d1, d2):
    return round(float(d1-d2), 3)


def collapse_rows(df_tmp, sense=0.03):
    df = df_tmp.copy()
    df = df.sort_values(['page_num', 'y1', 'x0'], ascending=[True, False, True])
    df = df.reset_index(drop=True)
    # Collapse rows
    df['flag'] = 1
    for i in range(1, len(df)):
        height = df.iloc[i]['height']

        y0, y0_next = df.iloc[i - 1]['y0'], df.iloc[i]['y0']
        y1, y1_next = df.iloc[i - 1]['y1'], df.iloc[i]['y1']

        x0, x0_next = df.iloc[i - 1]['x0'], df.iloc[i]['x0']
        x1, x1_next = df.iloc[i - 1]['x1'], df.iloc[i]['x1']

        # Check on width
        # Width of page = 612

        # if (((x0 < 300) and (x0_next < 300)) or ((x0 > 300) and (x0_next > 300))):
        if (x0_next < x1) and (x1_next > x0):

            if (((abs(y1_next - y0) < sense * height) and (abs(y0_next - y1) < sense * height)) and
                    (df.iloc[i - 1]['page_num'] == df.iloc[i]['page_num'])):
                df.loc[i - 1, 'flag'] = 0

                df.loc[i, 'name'] = str(df.iloc[i - 1]['name']) + str(df.iloc[i]['name'])

                df.loc[i, 'x0'] = min(df.iloc[i - 1]['x0'], df.iloc[i]['x0'])
                df.loc[i, 'x1'] = max(df.iloc[i - 1]['x1'], df.iloc[i]['x1'])

                df.loc[i, 'y0'] = min(df.iloc[i - 1]['y0'], df.iloc[i]['y0'])
                df.loc[i, 'y1'] = max(df.iloc[i - 1]['y1'], df.iloc[i]['y1'])

                # Set new coordinates of box

    df = df[df['flag'] == 1]
    df = df.drop(columns=['flag'])
    df = df.reset_index(drop=True)
    return df


def mean_char(a,b):
    x = a/len(b)
    return round(float(x), 3)


def round3(x):
    return round(float(x), 3)


def find_closest_element(e, df2, tmp_x='x1', tmp_y='y0', tmp_x1='x0', tmp_y1='y0'):
    # dataframes to numpy arrays of complex numbers
    p1 = (e[tmp_x] + 1j * e[tmp_y]).values
    p2 = (df2[tmp_x1] + 1j * df2[tmp_y1]).values
    # calculate all the distances, between each point in
    # e and each point in df2 (using an array-broadcasting trick)
    all_dists = abs(p1[..., np.newaxis] - p2)
    nearest_idxs1 = np.argmin(all_dists)
    return df2.iloc[[nearest_idxs1]]


def find_closest_element_center(e, df2):
    # dataframes to numpy arrays of complex numbers
    p1 = (0.5 * (e['x1'] + e['x0']) + 1j * 0.5 * (e['y0'] + e['y1'])).values
    p2 = (0.5 * (df2['x1'] + df2['x0']) + 1j * 0.5 * (df2['y0'] + df2['y1'])).values
    # calculate all the distances, between each point in
    # e and each point in df2 (using an array-broadcasting trick)
    all_dists = abs(p1[..., np.newaxis] - p2)
    nearest_idxs1 = np.argmin(all_dists)
    return df2.iloc[[nearest_idxs1]]


def find_closest_down(e, df):
    # Select items on the same page
    page_n = list(e['page_num'])[0]
    df = df[df['page_num'] == page_n]
    # Cut element y1< e['y1']
    df = df[df['y1'] < list(e['y1'])[0]]
    # Sort items top -> buttom -> right
    try:
        e_closest_bottom = find_closest_element_center(e, df)
        #tmp_dist = find_len()
    except:
        e_closest_bottom = pd.DataFrame(columns=['name', 'x0', 'x1', 'y0', 'y1', 'height', 'width', 'page_num'])
    return e_closest_bottom


def find_closest_right(e, df, is_same_level=True):
    # Select items on the same page
    page_n = list(e['page_num'])[0]
    df = df[df['page_num'] == page_n]
    df = df[df.name.str.strip().ne("") & df.name.notnull()]
    # Cut element x0 >  e['x1']
    df_right = df[df['x0'] > list(e['x1'])[0]]

    # df_right = df_right[df_right['x0'] <= list(e['x1'])[0]]
    if is_same_level:
        tmp_mean = 0.5 * (list(e['y0'])[0] + list(e['y1'])[0])
        df_right = df_right[df_right['y1'] >= tmp_mean]
        df_right = df_right[df_right['y0'] <= tmp_mean]
        # find closest buttom element
    try:
        e_closest_right = find_closest_element(e, df_right, tmp_x='x0', tmp_y='y0', tmp_x1='x1', tmp_y1='y0')

    except:
        e_closest_right = pd.DataFrame(columns=['name', 'x0', 'x1', 'y0', 'y1', 'height', 'width', 'page_num'])
    return e_closest_right


def delete_empty_rows(df, column_name="name"):
    filter = df[column_name] != ' '
    df = df[filter]
    df = df.reset_index(drop=True)
    return df


def mean_char(a, b):
    x = a/len(b)
    return round(float(x), 3)

################################


def find_cat_h(heights, items, min_cat_count, min_dish_count):
    for h in reversed(heights[heights['count'] >= min_cat_count].index.values):
        cat_h = h
        tmp_items = items[items['height'].between(0.99 * cat_h, 1.01 * cat_h)]
        tmp_items = tmp_items[tmp_items['name'].apply(lambda x: len(x)) > 3]
        if len(tmp_items) < min_cat_count:
            continue
        # Split cat at pages
        word_count = 0
        for p in tmp_items['page_num'].unique():
            word_count = len(items[items['page_num'] == p]) + word_count

        if word_count / len(tmp_items['page_num'].unique()) < 10:
            continue
        h_next = max(heights.index.values[heights.index.values < h])
        if (len(items[items['height'].between(0.99 * h_next, 1.01 * h_next)]) > min_dish_count) and (heights.loc[h]['count'] > heights.loc[h_next]['count']):
            continue
        else:
            break
    return cat_h


def delete_empty_names(df):
    df = df[df.name.str.strip().ne("") & df.name.notnull()]
    return df


def union_items(df, items):
    df['flag'] = 1
    for i in range(1, len(df)):
        tmp_cat_name = find_closest_down(df.iloc[[i - 1]], df)
        if len(tmp_cat_name) == 0:
            continue

        if list(find_closest_down(df.iloc[[i - 1]],
                                  items)['name'])[0] == list(tmp_cat_name['name'])[0]:
            df.loc[i - 1, 'flag'] = 0
            df.loc[i, 'name'] = str(df.iloc[i - 1]['name']) + str(
                df.iloc[i]['name'])

            df.loc[i, 'x0'] = min(df.iloc[i - 1]['x0'],
                                  df.iloc[i]['x0'])
            df.loc[i, 'x1'] = max(df.iloc[i - 1]['x1'],
                                  df.iloc[i]['x1'])

            df.loc[i, 'y0'] = min(df.iloc[i - 1]['y0'],
                                  df.iloc[i]['y0'])
            df.loc[i, 'y1'] = max(df.iloc[i - 1]['y1'],
                                  df.iloc[i]['y1'])

    df = df[df['flag'] == 1]
    df = df.drop(columns=['flag'])
    df = df.reset_index(drop=True)
    return df


