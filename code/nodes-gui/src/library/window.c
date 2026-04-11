#include "library/window.h"

#include <raylib.h>
#include <raymath.h>
#include <rlgl.h>
#include <stddef.h>

const Color DOTS_COLOR = (Color) { .r = 0xB0, .g = 0xB0, .b = 0xB0, .a = 0xFF };
const Color INPUT_PORT_COLOR = (Color) { .r = 0x15, .g = 0x20, .b = 0xA0, .a = 0xFF };

static Rectangle convert_clip(struct ClipArea clip_area) {
	return (Rectangle) {.x = clip_area.x, .y = clip_area.y, .width = clip_area.width, .height = clip_area.height };
}

static Vector2 convert_position(struct Position position) {
	return (Vector2) {.x = position.x, .y = position.y };
}

static void update_group(struct GroupBlock* state) {
}

static void update_atomic(struct AtomicBlock* state) {
	if (IsMouseButtonDown(MOUSE_BUTTON_LEFT)) {
		const Vector2 position = GetMousePosition();
		const bool click_inside = CheckCollisionPointRec(position, convert_clip(state->rect));
		if (click_inside) {
			const Vector2 mouse_delta = GetMouseDelta();

			state->rect = (struct ClipArea) {
				.x = state->rect.x + mouse_delta.x, .y = state->rect.y + mouse_delta.y,
				.width = state->rect.width, .height = state->rect.height
			};
		}
	}
}

static void update_board(struct GlobalState* state) {
	for (int i = 0; i < state->amount_groups; i++) {
		rlPushMatrix();
		rlTranslatef(state->groups[i].rect.x, state->groups[i].rect.y, 0.0f);
		{
			update_group(&state->groups[i]);
		}
		rlPopMatrix();
	}

	for (int i = 0; i < state->amount_atomics; i++) {
		rlPushMatrix();
		rlTranslatef(state->atomics[i].rect.x, state->atomics[i].rect.y, 0.0f);
		{
			update_atomic(&state->atomics[i]);
		}
		rlPopMatrix();
	}
}

static void draw_input_port(Font font, struct Port* port, float port_text_size) {
	const Vector2 draw_port_text_size = MeasureTextEx(font, port->name, port_text_size, 0);

	Vector2 position = { .x = 0, .y = draw_port_text_size.y / 2 };
	DrawCircleLinesV(position, 5, BLACK);
	DrawCircleV(position, 5, INPUT_PORT_COLOR);

	const Vector2 text_position = (Vector2) {.x = 10, .y = 0 };
	DrawTextEx(font, port->name, text_position, port_text_size, 0, BLACK);
}

static void draw_output_port(Font font, struct Port* port, float port_text_size) {
	const Vector2 draw_port_text_size = MeasureTextEx(font, port->name, port_text_size, 0);

	Vector2 position = { .x = 0, .y = draw_port_text_size.y / 2 };
	DrawCircleLinesV(position, 5, BLACK);
	DrawCircleV(position, 5, INPUT_PORT_COLOR);

	const Vector2 text_position = (Vector2) {.x = -draw_port_text_size.x - 10, .y = 0 };
	DrawTextEx(font, port->name, text_position, port_text_size, 0, BLACK);
}

static void draw_atomic(Font font, struct AtomicBlock* block) {
	Rectangle rect = convert_clip(block->rect);
	rect.height += 20.0f * block->amount_input_ports;

	const float line_y = 50.0f;

	const float text_size = 20.0f;
	const float port_text_size = 16.0f;
	const Vector2 drawn_text_size = MeasureTextEx(font, block->name, text_size, 0);
	const float text_x = 10.0f;
	const float text_y = line_y / 2 - drawn_text_size.y / 2;

	DrawRectangleRoundedLinesEx(rect, 0.05f, 10, 2, GRAY);
	DrawRectangleRounded(rect, 0.05f, 10, LIGHTGRAY);
	DrawLineEx((Vector2) { .x = rect.x, .y = rect.y + line_y}, (Vector2) { .x = rect.x + rect.width, .y = rect.y + line_y }, 1, GRAY);
	DrawTextEx(font, block->name, (Vector2) { .x = rect.x + text_x, .y = rect.y + text_y }, text_size, 2, BLACK);

	for (int i = 0; i < block->amount_input_ports; i++) {
		struct Port* port = &block->input_ports[i];
		rlPushMatrix();
		rlTranslatef(rect.x, rect.y + line_y + (float) (i+1) * 20, 0);
		{
			draw_input_port(font, port, port_text_size);
		}
		rlPopMatrix();
	}

	for (int i = 0; i < block->amount_output_ports; i++) {
		struct Port* port = &block->output_ports[i];
		rlPushMatrix();
		rlTranslatef(rect.x + rect.width, rect.y + line_y + (float) (i+1) * 20, 0);
		{
			draw_output_port(font, port, port_text_size);
		}
		rlPopMatrix();
	}
}

static void draw_group(Font font, struct GroupBlock* block) {
	for (int i = 0; i < block->amount_atomics; i++) {
		rlPushMatrix();
		rlTranslatef(block->atomics[i].rect.x, block->atomics[i].rect.y, 0.0f);
		{
			draw_atomic(font, &block->atomics[i]);
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
		rlPushMatrix();
		rlTranslatef(state->groups[i].rect.x, state->groups[i].rect.y, 0.0f);
		{
			draw_group(font, &state->groups[i]);
		}
		rlPopMatrix();
	}

	for (int i = 0; i < state->amount_atomics; i++) {
		rlPushMatrix();
		rlTranslatef(state->atomics[i].rect.x, state->atomics[i].rect.y, 0.0f);
		{
			draw_atomic(font, &state->atomics[i]);
		}
		rlPopMatrix();
	}
}

void run_window(int width, int height, struct GlobalState* state) {
	SetTraceLogLevel(LOG_DEBUG);
	SetConfigFlags(FLAG_MSAA_4X_HINT);
	SetTargetFPS(30);

	InitWindow(width, height, "raylib example - basic window");

	Font ubuntu_font = LoadFontEx("./resources/library/Ubuntu-M.ttf", 48, NULL, 0);
	GenTextureMipmaps(&ubuntu_font.texture);
	SetTextureFilter(ubuntu_font.texture, TEXTURE_FILTER_TRILINEAR);

	Camera2D camera = { 0 };
	camera.offset = (Vector2) { .x = width / 2, .y = height / 2 };
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

		update_board(state);

		BeginDrawing();
		{
			ClearBackground(RAYWHITE);
			BeginMode2D(camera);
			{
				draw_board_grid(1000, 2000);

				rlPushMatrix();
				rlTranslatef(state->position.x, state->position.y, 0);
				{
					draw_board(state, ubuntu_font);
				}
				rlPopMatrix();
			}

			EndMode2D();
		}
		EndDrawing();
	}

	UnloadFont(ubuntu_font);
	CloseWindow();
}