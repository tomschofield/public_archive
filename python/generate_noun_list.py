#makes a list of all nouns in the wordnet copera to a text file
from nltk.corpus import wordnet as wn

noun_list = ""
for synset in list(wn.all_synsets('n')):
 	print synset.lemma_names
 	for name in synset.lemma_names:
 		noun_list+=name.replace("_", "+")+"\n"



fo = open("noun_list.txt", "wb")
fo.write(noun_list);

# Close opend file
fo.close()


