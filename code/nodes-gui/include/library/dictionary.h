#pragma once

struct Trie {
	struct Trie* children[128];
	void* element;
};

struct Dictionary {
	struct Trie trie;
};

struct Dictionary* dictionary_create();

void dictionary_set(struct Dictionary* dictionary, char* key, void* element);

void* dictionary_remove(struct Dictionary* dictionary, char* key);

void* dictionary_get(struct Dictionary* dictionary, char* key);