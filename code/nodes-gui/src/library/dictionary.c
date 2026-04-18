#include "library/dictionary.h"

#include <stdlib.h>

static int trie_get_index(char value) {
	if (value <= 127) {
		return value;
	} else {
		return -1;
	}
}

static void trie_set(struct Trie* trie, char* key, void* element) {
	if (*key == '\0') {
		trie->element = element;
		return;
	}

	int index = trie_get_index(*key);
	if (index < 0) {
		return;
	}

	if (trie->children[index] == NULL) {
		trie->children[index] = calloc(1, sizeof(struct Trie));
	}

	trie_set(trie->children[index], key+1, element);
}

static void* trie_remove(struct Trie* trie, char* key) {
	if (*key == '\0') {
		void* original_element = trie->element;
		trie->element = NULL;
		return original_element;
	}

	int index = trie_get_index(*key);
	if (index < 0) {
		return NULL;
	}

	if (trie->children[index] == NULL) {
		return NULL;
	}

	return trie_remove(trie->children[index], key+1);
}

static void* trie_get(struct Trie* trie, char* key) {
	if (*key == '\0') {
		return trie->element;
	}

	int index = trie_get_index(*key);
	if (index < 0) {
		return NULL;
	}

	if (trie->children[index] == NULL) {
		return NULL;
	}

	return trie_get(trie->children[index], key+1);
}

struct Dictionary* dictionary_create() {
	struct Dictionary* dictionary = calloc(1, sizeof(struct Dictionary));

	return dictionary;
}

void dictionary_set(struct Dictionary* dictionary, char* key, void* element) {
	trie_set(&dictionary->trie, key, element);
}

void* dictionary_remove(struct Dictionary* dictionary, char* key) {
	return trie_remove(&dictionary->trie, key);
}

void* dictionary_get(struct Dictionary* dictionary, char* key) {
	return trie_get(&dictionary->trie, key);
}