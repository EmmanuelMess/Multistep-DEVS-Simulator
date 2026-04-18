#pragma once

#include "library/window.h"

struct Port* blocks_create_port(char* id, char* name);

struct AtomicBlock* blocks_create_atomic(char* id, char* name, int amount_input_ports, struct Port** input_ports,
                                         int amount_output_ports, struct Port** output_ports, struct Position position, float width, float height);

struct GroupBlock* blocks_create_group(char* id, char* name, int amount_atomics, struct AtomicBlock** atomic_blocks,
                                       struct Position position, float width, float height);

struct Connection* blocks_create_connection(char* input_id, char* output_id);

struct GlobalState* create_global_state(struct Position position,
                                        int amount_groups, struct GroupBlock** group_blocks,
                                        int amount_atomics, struct AtomicBlock** free_atomic_blocks,
                                        int amount_ports, struct Connection** connections);
