from pdf_reader import delete_empty_names, find_closest_down, find_closest_element_center
from menu_entity import is_separate_price
import re
import pandas as pd

def get_cat_dish_and_price(_dish, _items, _filename):
    str_result = ""
    try:
        tmp_df = _items[_items['page_num'] == _dish.iloc[0]['page_num']]
        tmp_df = tmp_df[tmp_df['y0'] > _dish.iloc[0]['y1']]
        tmp_df = tmp_df[tmp_df['height'] > 1.2*_dish.iloc[0]['height']]


        result =find_closest_element_center(e=_dish, df2 = tmp_df)
        str_result = result.iloc[0]['name'].strip()
    except:
        str_result = _filename
    return str_result


def string_is_price(s):
    flag = False
    p = re.compile(r'\d+(\.\d+)?$')
    s = s.replace(" ", "")
    s = s.replace(",", ".")
    if p.match(s):
        flag = True
    return flag


def get_price_dish_cat1(e):
    s = e.iloc[0]['name']
    p = s.strip().split(" ")[-1]
    try:
        if p[0].isdigit() == False:
            p = p[1:]
    except:
        p=p
    return p


def get_price_dish_cat(e):
	s = e.iloc[0]['name']
	p_array = s.strip().split(" ")
	try:
		for j in range(1, len(p_array) + 1):
			tmp_p = p_array[-j]
			if len(tmp_p) == 0:
				continue
			try:
				if tmp_p[0].isdigit() == False and tmp_p[0] != '.':
					tmp_p = tmp_p[1:]
			except:
				tmp_p = tmp_p

			tmp_p = tmp_p.replace(",", ".")
			if tmp_p.replace(".", "").isdigit() and string_is_price(p_array[-j - 1]):
				p_array[-j] = p_array[-j - 1] + tmp_p
			if tmp_p.isdigit() and string_is_price(p_array[-j - 1]) == False:
				break
		result = p_array[-1]
		try:
			if result[0].isdigit() == False:
				result = result[1:]
		except:
			result = result

	except:
		result = None
	return result


def get_name_dish_with_price(e):
	s = e.iloc[0]['name']
	p_array = s.strip().split(" ")
	b = [item for item in p_array if len(item) > 1 and not is_separate_price(item)]
	result = " ".join(b)

	return result.strip()


def get_descr_dish_with_price(e, _Items, _Dishes):
	result = ''
	try:
		df_temp = _Items[_Items['page_num'] == e.iloc[0]['page_num']]
		df_temp = df_temp[df_temp['y1'] < 0.5 * (e.iloc[0]['y0'] + e.iloc[0]['y1'])]
		df_temp = df_temp[df_temp['x0'] < e.iloc[0]['x1']]
		df_temp = df_temp[df_temp['x1'] > e.iloc[0]['x0']]

		e_down = find_closest_down(e, _Dishes)
		df_temp = df_temp[df_temp['y0'] > 0.5 * (e_down.iloc[0]['y0'] + e_down.iloc[0]['y1'])]

		tmp_descr = delete_empty_names(df_temp)
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

		result = descr.iloc[0]['name']
	except:
		result = None
	return result


def get_Result_dish_with_price(_Dish, _Items, _filename, _Vegans):
	_Dish = _Dish.reset_index(drop=True)
	Result = pd.DataFrame(columns=[
		'item_name',
		'description',
		'veg_comment',
		'price',
		'currency',
		'category',
		'comment',
		'size_comment',
		'price_comment',
		'category_order'
	])

	for i in range(0, len(_Dish)):
		e = _Dish.iloc[[i]]
		# item_name = e.iloc[0]['name'].strip()
		item_name = get_name_dish_with_price(e)
		s = item_name
		# Get Veg Comment
		veg_comment = None
		try:
			s_temp = s.replace(") (", ",")
			s_temp = s_temp.replace(")(", ", ")
			s_temp = s_temp.replace("(", "")
			s_temp = s_temp.replace(")", "")
			s_vg = s_temp.split(" ")[-1]

			if len(_Vegans[_Vegans['veg_comment'] == s_vg]) > 0:
				item_name = " ".join(s_temp.split(" ")[:-1])
				veg_comment = s_vg
		except:
			veg_comment = None
		desciption = get_descr_dish_with_price(e, _Items=_Items, _Dishes=_Dish)
		category = get_cat_dish_and_price(_dish=e, _items=_Items, _filename=_filename)
		currency = 'GBP'
		price = get_price_dish_cat(e)

		tmp_result = pd.DataFrame({
			'item_name': [item_name],
			'description': [desciption],
			'veg_comment': [veg_comment],
			'price': [price],
			'currency': [currency],
			'category': [category],
			'comment': [None],
			'size_comment': [None],
			'price_comment': [None],
			'category_order': [None]})

		Result = Result.append(tmp_result, ignore_index=True)

	return Result