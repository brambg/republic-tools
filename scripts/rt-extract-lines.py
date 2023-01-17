import json
from icecream import ic

with open("1728-textstore.json") as f:
	text_store=json.load(f)

for l in text_store['_resources'][0]['_ordered_segments']:
	print(l)
