#pragma once

struct ClipArea {
	float x;                // Rectangle top-left corner position x
	float y;                // Rectangle top-left corner position y
	float width;            // Rectangle width
	float height;           // Rectangle height
};

// Vector2, 2 components
struct Position {
	float x;                // Vector x component
	float y;                // Vector y component
};

struct Port {
	char* name;
};

struct AtomicBlock {
	int id;
	char* name;
	int amount_input_ports;
	struct Port* input_ports;
	int amount_output_ports;
	struct Port* output_ports;
	struct ClipArea rect;
};

struct GroupBlock {
	int id;
	char* name;
	int amount_atomics;
	struct AtomicBlock* atomics;
	struct ClipArea rect;
};

struct GlobalState {
	struct Position position;
	int amount_groups;
	struct GroupBlock* groups;
	int amount_atomics;
	struct AtomicBlock* atomics;
};

void run_window(const char* resources_directory, int width, int height, struct GlobalState* state);