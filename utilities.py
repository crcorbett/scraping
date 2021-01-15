import re
from string import capwords

def string_clean(string):
	cleaned = re.sub('( \(\))', '',string)
	cleaned = cleaned.rstrip()
	return cleaned

def string_capitalise(string):
	cleaned = capwords(string)
	return cleaned