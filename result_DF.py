from pdf_reader import find_closest_right, find_closest_down, find_closest_element_center
import pandas as pd



def get_category(e, cat, filename):
    result = ''
    d = e.iloc[[0]]
    try:
        d['mean_X'] = 0.5*(d['x0'] + d['x1'])
        d['mean_Y'] = 0.5*(d['y0'] + d['y1'])

        cat['mean_X'] = 0.5*(cat['x0'] + cat['x1'])
        cat['mean_Y'] = 0.5*(cat['y0'] + cat['y1'])

        # Get the same pages items
        df_temp = cat[cat['page_num'] == d.iloc[0]['page_num']]
        df_temp = df_temp[df_temp['mean_Y'] > d.iloc[0]['mean_Y']]

        result_df = find_closest_element_center(d, df_temp)
        result = result_df.iloc[0]['name']
    except:
        result = filename[:-4]
    return result.strip()

def get_price(e, Prices):
    result = ''
    try:
        result = find_closest_right(e, Prices, is_same_level=True)
        result =  result.iloc[0]['name'].strip()
    except:
        result = None
    return result


def get_description(e, _Dishes, _Descriptions):
	result = ''
	try:
		e_down = find_closest_down(e, _Dishes)
		df_temp = _Descriptions[_Descriptions['page_num'] == e.iloc[0]['page_num']]
		df_temp = df_temp[df_temp['y1'] <= 0.5 * (list(e['y0'])[0] + list(e['y1'])[0])]
		df_temp = df_temp[df_temp['y0'] >= 0.5 * (list(e_down['y0'])[0] + list(e_down['y1'])[0])]
		df_temp = df_temp[df_temp['x0'] < list(e['x1'])[0]]
		df_temp = df_temp[df_temp['x1'] > list(e['x0'])[0]]

		# tmp_descr = tmp_descr[tmp_descr['y1'] <= 0.5 * (list(e['y0'])[0] + list(e['y1'])[0])]

		result = df_temp.iloc[0]['name'].strip()
	except:
		result = None
	return result


def get_Result(_Dish, _Categories, _Prices, _Description, _filename, _Vegans):
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
		item_name = e.iloc[0]['name'].strip()
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
		desciption = get_description(e, _Dish, _Description)
		category = get_category(e, _Categories, _filename)
		currency = 'GBP'
		price = get_price(e, _Prices)

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