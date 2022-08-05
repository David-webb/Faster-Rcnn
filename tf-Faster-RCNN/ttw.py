import string
from collections import OrderedDict
source = list(string.ascii_letters)
for index in range(0, 10):
    source.append(str(index))
# 停用词:通过手动打码统计的
stop_words = ['G', 'I', 'L', 'O', 'Q', 'U', 'W', 'Z', 'a', 'b', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'l', 'm',
	      'n', 'o', 'q', 'r', 't', 'u', 'w', 'y', 'z', '0', '9']
source = list(set(source)-set(stop_words))
#source.sort()
# print len(set([w.lower() for w in source]))
print(source)
