#include "library/window.h"

int main(void)
{
	const int WIDTH = 800;
	const int HEIGHT = 450;
	struct Port input_ports[] = {
		(struct Port) { .name = "Messages" },
		(struct Port) { .name = "Objects" },
	};

	struct Port output_ports[] = {
		(struct Port) { .name = "Messages" },
		(struct Port) { .name = "Objects" },
	};

	struct AtomicBlock group_atomics[] = {
		(struct AtomicBlock) {
			.id = 0, .name = "Atomic",
			.amount_input_ports = 2, .input_ports = input_ports,
			.amount_output_ports = 2, .output_ports = output_ports,
			.rect = (struct ClipArea) {.x = 0, .y = 0, .width = 200, .height = 300 },
		},
	};

	struct GroupBlock group_blocks[] = {
		(struct GroupBlock) {
			.id = 0, .name = "Group", .amount_atomics = 1, .atomics = group_atomics,
			.rect = (struct ClipArea) {.x = -250, .y = 0, .width = 200, .height = 300 },
		}
	};

	struct AtomicBlock free_atomics[] = {
		(struct AtomicBlock) {
			.id = 0, .name = "Atomic",
			.amount_input_ports = 2, .input_ports = input_ports,
			.amount_output_ports = 2, .output_ports = output_ports,
			.rect = (struct ClipArea) {.x = -50, .y = 0, .width = 200, .height = 300 },
		},
	};

	struct GlobalState state = {
		.position = (struct Position) {0.0f, 0.0f},
		.amount_groups = 1,
		.groups = group_blocks,
		.amount_atomics = 1,
		.atomics = free_atomics
	};

	run_window("./lib/resources", WIDTH, HEIGHT, &state);


	return 0;
}
