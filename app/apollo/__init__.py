# -*- coding: utf-8 -*-
"""
	app.apollo
	~~~~~~~~~~~~~~

	Provides methods to manipulate Portfolio objects for input into
	visualization libraries
"""

from app.cronus.analytics import Metrics
from app.cronus.coredata import DataObject


class Worth(Metrics):
	"""
	Description.

	Attributes
	----------
	"""

	def __init__(self, *args, **kwargs):
		"""
		Class constructor.

		Parameters
		----------
		args : sequence of arguments, optional
		kwargs : dict of keyword arguments, optional
		"""

		super(Worth, self).__init__(*args, **kwargs)

	@property
	def share_value(self):
		# adds transaction price to prices df if needed
		df = self.native_prices.join_frame(self.shares_w_reinv)
		df['value'] = df.native_price * df.shares

		# TODO: sum by dates, not datetimes
		df = df.groupby(level=df.index.names).sum()
		return DataObject({'shares': df.shares, 'value': df.value})

	def calc_worth(self, how='stock', mode='uniform', convert=False):
		"""
		Calculate portfolio worth for a specific date

		Parameters
		----------
		how : {'own', 'act', 'stock', 'own_stock', 'act_stock', 'own_act'}
			How to group the values:
			* own: by owner
			* act: by account
			* stock: by stock
			* own_stock: by owner and stock
			* act_stock: by account and stock
			* own_act: by owner and account

			default 'stock'

		mode : {'latest', 'uniform'}
			How to select the date on which to calculate the value
			* latest: view most recent data irrespective of incomplete entries
			* uniform: view most recent data that contains values for all
				entries

		convert : boolean, default False
			convert commodity ids to symbols

		"""
		# group transactions by date
#		max_date = max(i[3] for i in df.index)

		# make sep data frames for each date
		# TODO: account for multiple owners and/or accounts
		df = self.share_value
		old_index = df.non_date_index
		dfs = [f for f in df.sorted.split_frame('date')]
		date_list = [(f.index[0], len(f)) for f in dfs]
		by_date = dict(date_list)
		max_entries = max(by_date.values())
		items = by_date.items()
		df.reset_index(inplace=True)

		# select grouping
		switch = {
			'own': ['owner_id'],
			'act': ['account_id'],
			'stock': ['commodity_id'],
			'own_stock': ['owner_id', 'commodity_id'],
			'act_stock': ['account_id', 'commodity_id'],
			'own_act': ['owner_id', 'account_id']}

		new_index = ['date'] + switch.get(how.lower())
		to_delete = set(old_index).difference(new_index)
		df.set_index(new_index, inplace=True)
		df = df.sorted

		for f in to_delete:
			del df[f]

		# select mode
		switch = {
			'latest': max(by_date.keys()),
			'uniform': max(d[0] for d in items if d[1] == max_entries)}

		the_date = switch.get(mode.lower())
		selected = df.groupby(level='date').get_group(the_date)
		return selected.reset_index('date').to_dict()['value']

	def convert_worth(self, worth):
		"""
		Converts Portfolio values into a more parseable format

		Parameters
		----------
		worth : dict {id: value}

		Returns
		-------
		data : sequence of ('symbol', value)
		"""
		symbols = [self.mapping.symbol.get(x, 'N/A') for x in worth.keys()]
		worths = ['%.2f' % x for x in worth.values()]
		keys = ('symbol', 'worth')
		zipped = zip(symbols, worths)
		return [dict(zip(keys, values)) for values in zipped]
