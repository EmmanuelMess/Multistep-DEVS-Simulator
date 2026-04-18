#include "library/blocks.h"
#include "library/window.h"

int main(void)
{
	const int WIDTH = 800;
	const int HEIGHT = 450;
	struct Port* input_ports_1[] = {
		blocks_create_port("<port:0>", "Messages1"),
		blocks_create_port("<port:1>", "Objects1"),
	};

	struct Port* output_ports_1[] = {
		blocks_create_port("<port:2>", "Messages2"),
		blocks_create_port("<port:3>", "Objects2"),
	};

	struct AtomicBlock* group_atomics[] = {
		blocks_create_atomic("<atomic:0>", "Atomic1", 2, input_ports_1, 2, output_ports_1,
			(struct Position) { .x = 0, .y = 0 }, 200.0f, 300.0f),
	};

	struct GroupBlock* group_blocks[] = {
		blocks_create_group("<group:0>", "Group1", 1, group_atomics,
			(struct Position) { .x = -250, .y = -100 }, 200.0f, 300.0f),
	};

	struct Port* input_ports_2[] = {
		blocks_create_port("<port:4>", "Messages1"),
		blocks_create_port("<port:5>", "Objects1"),
	};

	struct Port* output_ports_2[] = {
		blocks_create_port("<port:6>", "Messages2"),
		blocks_create_port("<port:7>", "Objects2"),
	};


	struct AtomicBlock* free_atomics[] = {
		blocks_create_atomic("<atomic:1>", "Atomic2", 2, input_ports_2, 2, output_ports_2,
			(struct Position) { .x = 100.0f, .y = 100.0f }, 200.0f, 300.0f),
	};

	struct Connection* port_connections[] = {
		blocks_create_connection("<port:2>", "<port:4>"),
		blocks_create_connection("<port:3>", "<port:5>")
	};

	struct GlobalState* state = create_global_state((struct Position) {0.0f, 0.0f}, 1, group_blocks, 1, free_atomics, 2, port_connections);

	port_connections[0]->activated = true;

	run_window("./lib/resources", WIDTH, HEIGHT, state);


	return 0;
}
