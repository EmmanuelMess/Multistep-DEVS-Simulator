#include "library/blocks.h"

#include <stdlib.h>

struct Port * blocks_create_port(char *id, char *name) {
	struct Port* port = calloc(1, sizeof(struct Port));
	*port = (struct Port) { .id = id, .name = name };
	return port;
}

struct AtomicBlock * blocks_create_atomic(char *id, char *name, int amount_input_ports, struct Port **input_ports,
	int amount_output_ports, struct Port **output_ports, struct Position position, float width, float height) {
	struct AtomicBlock* atomic_block = calloc(1, sizeof(struct AtomicBlock));
	*atomic_block = (struct AtomicBlock) {
		.id = id, .name = name,
		.amount_input_ports = amount_input_ports, .input_ports = input_ports,
		.amount_output_ports = amount_output_ports, .output_ports = output_ports,
		.position = position,
		.width = width, .height = height,
	};
	return atomic_block;
}

struct GroupBlock * blocks_create_group(char *id, char *name, int amount_atomics, struct AtomicBlock **atomic_blocks,
	struct Position position, float width, float height) {
	struct GroupBlock* group_block = calloc(1, sizeof(struct GroupBlock));
	*group_block = (struct GroupBlock) {
		.id = id, .name = name,
		.amount_atomics = amount_atomics, .atomics = atomic_blocks,
		.position = position,
		.width = width, .height = height,
	};
	return group_block;
}

struct Connection * blocks_create_connection(char *input_id, char *output_id) {
	struct Connection* port = calloc(1, sizeof(struct Connection));
	*port = (struct Connection) { .input_id = input_id, .output_id = output_id, .activated = false };
	return port;
}

struct GlobalState * create_global_state(struct Position position, int amount_groups, struct GroupBlock **group_blocks,
	int amount_atomics, struct AtomicBlock **free_atomic_blocks, int amount_ports, struct Connection **connections) {
	struct Dictionary* ports = dictionary_create(); // [char* -> struct Port*]
	for (int i = 0; i < amount_groups; ++i) {
		struct GroupBlock* group_block = group_blocks[i];
		for (int j = 0; j < group_block->amount_atomics; ++j) {
			struct AtomicBlock* atomic = group_block->atomics[j];
			for (int k = 0; k < atomic->amount_input_ports; ++k) {
				struct Port* port = atomic->input_ports[k];
				dictionary_set(ports, port->id, port);
			}

			for (int k = 0; k < atomic->amount_output_ports; ++k) {
				struct Port* port = atomic->output_ports[k];
				dictionary_set(ports, port->id, port);
			}
		}
	}

	for (int i = 0; i < amount_atomics; ++i) {
		struct AtomicBlock* atomic = free_atomic_blocks[i];
		for (int j = 0; j < atomic->amount_input_ports; ++j) {
			struct Port* port = atomic->input_ports[j];
			dictionary_set(ports, port->id, port);
		}

		for (int j = 0; j < atomic->amount_output_ports; ++j) {
			struct Port* port = atomic->output_ports[j];
			dictionary_set(ports, port->id, port);
		}
	}

	struct GlobalState* global_state = calloc(1, sizeof(struct GlobalState));
	*global_state = (struct GlobalState) {
		.position = position,
		.amount_groups = amount_groups,
		.groups = group_blocks,
		.amount_atomics = amount_atomics,
		.atomics = free_atomic_blocks,
		.amount_connections = amount_ports,
		.connections = connections,
		.ports = ports
	};
	return global_state;
}
