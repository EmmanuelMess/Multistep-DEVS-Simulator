#include "library/window.h"

#include <raylib.h>
#include <raymath.h>
#include <rlgl.h>
#include <stdio.h>

#include "library/dictionary.h"

#define DEBUG false

const Color DOTS_COLOR = (Color) { .r = 0xB0, .g = 0xB0, .b = 0xB0, .a = 0xFF };
const Color INPUT_PORT_COLOR = (Color) { .r = 0x15, .g = 0x20, .b = 0xA0, .a = 0xFF };
const Color DEACTIVATED_CONNECTION_COLOR = BLACK;
const Color ACTIVATED_CONNECTION_COLOR = RED;

const float PORT_CIRCLE_SIZE = 5.0f;  // [px]
const float ATOMIC_LINE_POSITION = 50.0f;  // [px]
const float PORT_TEXT_SIZE = 16.0f;  // [px]

static Vector2 convert_position(struct Position position) {
	return (Vector2) { .x = position.x, .y = position.y };
}

static struct Position convert_vector2(Vector2 position) {
	return (struct Position) { .x = position.x, .y = position.y };
}

#if DEBUG
static void log_matrix(Matrix matrix) {
	TraceLog(LOG_DEBUG, "[%f %f %f %f", matrix.m0, matrix.m4, matrix.m8,  matrix.m12);
	TraceLog(LOG_DEBUG, "%f %f %f %f", matrix.m1, matrix.m5, matrix.m9,  matrix.m13);
	TraceLog(LOG_DEBUG, "%f %f %f %f", matrix.m2, matrix.m6, matrix.m10, matrix.m14);
	TraceLog(LOG_DEBUG, "%f %f %f %f]", matrix.m3, matrix.m7, matrix.m11, matrix.m15);
}
#endif

// ----------------------------- UPDATE TEMP DATA ---------------------------

static void update_data_port(Font font, Matrix world_to_port, struct Port* port) {
	const Vector2 draw_port_text_size = MeasureTextEx(font, port->name, PORT_TEXT_SIZE, 0);
	const float port_position_y = draw_port_text_size.y / 2.0f;

	port->position_global = convert_vector2(Vector2Transform((Vector2) {.x = 0, .y = 0}, world_to_port));
	port->position_global.y += port_position_y;
}

static void update_data_atomic(Font font, Matrix world_to_atomic, struct AtomicBlock* atomic) {
	atomic->position_global = (struct Position) { .x = world_to_atomic.m12, .y = world_to_atomic.m13 };

	for (int i = 0; i < atomic->amount_input_ports; i++) {
		struct Port* port = atomic->input_ports[i];
		const float port_position_y = ATOMIC_LINE_POSITION + (float) (i+1) * 20;
		const Matrix world_to_port = MatrixMultiply(MatrixTranslate(0, port_position_y, 0.0f), world_to_atomic);

		update_data_port(font, world_to_port, port);
	}

	for (int i = 0; i < atomic->amount_output_ports; i++) {
		struct Port* port = atomic->output_ports[i];
		const float port_position_y = ATOMIC_LINE_POSITION + (float) (i+1) * 20;
		const Matrix world_to_port = MatrixMultiply(MatrixTranslate(atomic->width, port_position_y, 0.0f), world_to_atomic);

		update_data_port(font, world_to_port, port);
	}
}

static void update_data_group(Font font, Matrix world_to_group, struct GroupBlock* block) {
	block->position_global = (struct Position) { .x = world_to_group.m12, .y = world_to_group.m13 };

	for (int i = 0; i < block->amount_atomics; i++) {
		struct AtomicBlock* atomic = block->atomics[i];
		const Matrix world_to_atomic = MatrixMultiply(MatrixTranslate(atomic->position.x, atomic->position.y, 0.0f), world_to_group);

		update_data_atomic(font, world_to_atomic, atomic);
	}
}

static void update_data_ui(Font font, Matrix world_to_board, struct GlobalState* state) {
	for (int i = 0; i < state->amount_groups; i++) {
		struct GroupBlock* group = state->groups[i];
		const Matrix world_to_group = MatrixMultiply(MatrixTranslate(group->position.x, group->position.y, 0.0f), world_to_board);

		update_data_group(font, world_to_group, group);
	}

	for (int i = 0; i < state->amount_atomics; i++) {
		struct AtomicBlock* atomic = state->atomics[i];
		const Matrix world_to_atomic = MatrixMultiply(MatrixTranslate(atomic->position.x, atomic->position.y, 0.0f), world_to_board);

		update_data_atomic(font, world_to_atomic, atomic);
	}
}

// ----------------------------- UPDATE ---------------------------

static void update_atomic(struct GlobalState* state, Matrix screen_to_atomic, struct AtomicBlock* atomic) {
	if (IsMouseButtonDown(MOUSE_BUTTON_LEFT)) {
		const Vector2 post_mouse_position = GetMousePosition();

		{  // Move atomic
			const Vector2 prev_mouse_position = Vector2Subtract(post_mouse_position, GetMouseDelta());
			const Vector2 atomic_prev_mouse_position =
				Vector2Transform((Vector2){ prev_mouse_position.x, prev_mouse_position.y }, screen_to_atomic);

			const bool click_inside = CheckCollisionPointRec(atomic_prev_mouse_position,
				(Rectangle) { .x = 0, .y = 0, .width = atomic->width, .height = atomic->height });
			if (click_inside) {
				const Vector2 parent_post_mouse_position =
					Vector2Transform((Vector2){ post_mouse_position.x, post_mouse_position.y }, screen_to_atomic);
				const Vector2 parent_mouse_delta = Vector2Subtract(parent_post_mouse_position, atomic_prev_mouse_position);

				atomic->position = (struct Position) {
					.x = atomic->position.x + parent_mouse_delta.x, .y = atomic->position.y + parent_mouse_delta.y
				};
			}
		}
	}
}

static void update_group(struct GlobalState* state, Matrix screen_to_group, struct GroupBlock* block) {
	for (int i = 0; i < block->amount_atomics; i++) {
		struct AtomicBlock* atomic = block->atomics[i];
		const Matrix screen_to_atomic = MatrixMultiply(MatrixTranslate(-atomic->position.x, -atomic->position.y, 0.0f), screen_to_group);

		update_atomic(state, screen_to_atomic, atomic);
	}
}

static void update_ui(struct GlobalState* state, Matrix screen_to_board) {
	for (int i = 0; i < state->amount_groups; i++) {
		struct GroupBlock* group = state->groups[i];
		const Matrix screen_to_group = MatrixMultiply(MatrixTranslate(-group->position.x, -group->position.y, 0.0f), screen_to_board);

		update_group(state, screen_to_group, group);
	}

	for (int i = 0; i < state->amount_atomics; i++) {
		struct AtomicBlock* atomic = state->atomics[i];
		const Matrix screen_to_atomic = MatrixMultiply(MatrixTranslate(-atomic->position.x,- atomic->position.y, 0.0f), screen_to_board);

		update_atomic(state, screen_to_atomic, atomic);
	}
}

// -------------------------------------- DRAW ------------------------------

static void draw_input_port(Font font, struct Port* port, float port_text_size) {
	const Vector2 draw_port_text_size = MeasureTextEx(font, port->name, port_text_size, 0);

	Vector2 position = { .x = 0, .y = draw_port_text_size.y / 2 };
	DrawCircleLinesV(position, PORT_CIRCLE_SIZE, BLACK);
	DrawCircleV(position, PORT_CIRCLE_SIZE, INPUT_PORT_COLOR);

	const Vector2 text_position = (Vector2) {.x = 10, .y = 0 };
	DrawTextEx(font, port->name, text_position, port_text_size, 0, BLACK);
}

static void draw_output_port(Font font, struct Port* port, float port_text_size) {
	const Vector2 draw_port_text_size = MeasureTextEx(font, port->name, port_text_size, 0);

	Vector2 position = { .x = 0, .y = draw_port_text_size.y / 2 };
	DrawCircleLinesV(position, PORT_CIRCLE_SIZE, BLACK);
	DrawCircleV(position, PORT_CIRCLE_SIZE, INPUT_PORT_COLOR);

	const Vector2 text_position = (Vector2) {.x = -draw_port_text_size.x - 10, .y = 0 };
	DrawTextEx(font, port->name, text_position, port_text_size, 0, BLACK);
}

static void draw_atomic(Font font, struct AtomicBlock* block) {
#if DEBUG
	DrawCircleV(Vector2Zero(), 10, YELLOW);
#endif

	Rectangle rect = {.x = 0, .y = 0, .width = block->width, .height = block->height};
	rect.height += 20.0f * (float) block->amount_input_ports;

	const float text_size = 20.0f;
	const Vector2 drawn_text_size = MeasureTextEx(font, block->name, text_size, 0);
	const float text_x = 10.0f;
	const float text_y = ATOMIC_LINE_POSITION / 2 - drawn_text_size.y / 2;

	DrawRectangleRoundedLinesEx(rect, 0.05f, 10, 2, GRAY);
	DrawRectangleRounded(rect, 0.05f, 10, LIGHTGRAY);
	DrawLineEx((Vector2) { .x = 0, .y = ATOMIC_LINE_POSITION}, (Vector2) { .x = rect.width, .y = ATOMIC_LINE_POSITION }, 1, GRAY);
	DrawTextEx(font, block->name, (Vector2) { .x = text_x, .y = text_y }, text_size, 2, BLACK);

	for (int i = 0; i < block->amount_input_ports; i++) {
		struct Port* port = block->input_ports[i];
		rlPushMatrix();
		rlTranslatef(0, ATOMIC_LINE_POSITION + (float) (i+1) * 20, 0);
		{
			draw_input_port(font, port, PORT_TEXT_SIZE);
		}
		rlPopMatrix();
	}

	for (int i = 0; i < block->amount_output_ports; i++) {
		struct Port* port = block->output_ports[i];
		rlPushMatrix();
		rlTranslatef(rect.width, ATOMIC_LINE_POSITION + (float) (i+1) * 20, 0);
		{
			draw_output_port(font, port, PORT_TEXT_SIZE);
		}
		rlPopMatrix();
	}
}

static void draw_group(Font font, struct GroupBlock* block) {
	for (int i = 0; i < block->amount_atomics; i++) {
		struct AtomicBlock* atomic = block->atomics[i];

		rlPushMatrix();
		rlTranslatef(atomic->position.x, atomic->position.y, 0.0f);
		{
			draw_atomic(font, atomic);
		}
		rlPopMatrix();
	}
}

static void draw_board_grid(int x_size, int y_size) {
	for (int i = -y_size/2; i < y_size/2; i += 20) {
		for (int j = -x_size/2; j < x_size/2; j += 20) {
			DrawCircle(i, j, 2, DOTS_COLOR);
		}
	}
}

static void draw_board(const struct GlobalState* state, Font font) {
	for (int i = 0; i < state->amount_groups; i++) {
		struct GroupBlock* group = state->groups[i];
		rlPushMatrix();
		rlTranslatef(group->position.x, group->position.y, 0.0f);
		{
#if DEBUG
			DrawCircleV(Vector2Zero(), 10, BLUE);
#endif

			draw_group(font, group);
		}
		rlPopMatrix();
	}

	for (int i = 0; i < state->amount_atomics; i++) {
		struct AtomicBlock* atomic = state->atomics[i];
		rlPushMatrix();
		rlTranslatef(atomic->position.x, atomic->position.y, 0.0f);
		{
			draw_atomic(font, atomic);
		}
		rlPopMatrix();
	}
}

// ------------------------------------- DRAW CONNECTIONS -----------------------------
static void draw_connections(const struct GlobalState* state) {
	for (int i = 0; i < state->amount_connections; ++i) {
		struct Connection* connection = state->connections[i];
		struct Port* port_input = dictionary_get(state->ports, connection->input_id);
		struct Port* port_output = dictionary_get(state->ports, connection->output_id);

		const Color color = connection->activated? ACTIVATED_CONNECTION_COLOR:DEACTIVATED_CONNECTION_COLOR;

		DrawLineBezier(convert_position(port_input->position_global), convert_position(port_output->position_global), 2, color);
	}
}

void run_window(const char* resources_directory, int width, int height, struct GlobalState* state) {
	SetTraceLogLevel(LOG_DEBUG);
	SetConfigFlags(FLAG_MSAA_4X_HINT);
	SetTargetFPS(30);

	InitWindow(width, height, "raylib example - basic window");

#define DIRECTORY_CHAR_LEN (500)
	char font_directory[DIRECTORY_CHAR_LEN];
	snprintf(font_directory, DIRECTORY_CHAR_LEN-1, "%s%s", resources_directory, "/library/Ubuntu-M.ttf");
#undef DIRECTORY_CHAR_LEN

	Font ubuntu_font = LoadFontEx(font_directory, 48, NULL, 0);
	GenTextureMipmaps(&ubuntu_font.texture);
	SetTextureFilter(ubuntu_font.texture, TEXTURE_FILTER_TRILINEAR);

	Camera2D camera = { 0 };
	camera.offset = (Vector2) { .x = width / 2.0f, .y = height / 2.0f };
	camera.target = (Vector2) { .x = 0, .y = 0 };
	camera.zoom = 1.0f;

	while (!WindowShouldClose())
	{
		// Translate based on mouse right click
		if (IsMouseButtonDown(MOUSE_BUTTON_MIDDLE))
		{
			Vector2 delta = GetMouseDelta();
			delta = Vector2Scale(delta, -1.0f/camera.zoom);
			camera.target = Vector2Add(camera.target, delta);
		}

		// Zoom based on mouse wheel
		float wheel = GetMouseWheelMove();
		if (wheel != 0) {
			// Get the world point that is under the mouse
			Vector2 mouseWorldPos = GetScreenToWorld2D(GetMousePosition(), camera);

			// Set the offset to where the mouse is
			camera.offset = GetMousePosition();

			// Set the target to match, so that the camera maps the world space point
			// under the cursor to the screen space point under the cursor at any zoom
			camera.target = mouseWorldPos;

			// Zoom increment
			// Uses log scaling to provide consistent zoom speed
			float scale = 0.2f*wheel;
			camera.zoom = Clamp(expf(logf(camera.zoom)+scale), 0.125f, 64.0f);
		}

		{
			const Matrix world_to_board = MatrixTranslate(-state->position.x, -state->position.y, 0.0f);
			const Matrix screen_to_world = MatrixInvert(GetCameraMatrix2D(camera));
			const Matrix screen_to_board = MatrixMultiply(world_to_board, screen_to_world);
			update_ui(state, screen_to_board);

			update_data_ui(ubuntu_font, MatrixTranslate(state->position.x, state->position.y, 0.0f), state);
		}

		BeginDrawing();
		{
			ClearBackground(RAYWHITE);
			BeginMode2D(camera);
			{
				draw_board_grid(1000, 2000);

				rlPushMatrix();
				rlTranslatef(state->position.x, state->position.y, 0);
				{
#if DEBUG
					DrawCircleV(Vector2Zero(), 10, RED);
#endif

					draw_board(state, ubuntu_font);
				}
				rlPopMatrix();

				draw_connections(state);
			}
			EndMode2D();
		}
		EndDrawing();
	}

	UnloadFont(ubuntu_font);
	CloseWindow();
}