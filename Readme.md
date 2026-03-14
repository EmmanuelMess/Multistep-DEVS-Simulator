

## OpenCode setup

### Build

docker build -t multistep-devs:24.04 .

### Run

docker run -it \
       --workdir /root/ws \
       -v ~/.local/share/opencode:/root/.local/share/opencode:rw \
       -v $PWD/.mulch/:/root/ws/.mulch:rw \
       -v $PWD/.claude/:/root/ws/.claude:rw \
       -v $PWD/.opencode/:/root/.config/opencode:rw \
       -v $PWD/code/:/root/ws/code/:rw \
       -v $PWD/design/:/root/ws/design/:ro \
       -v "$PWD/spec files/:/root/ws/spec files/:ro" \
       -v $PWD/LAYOUT.md:/root/ws/LAYOUT.md:ro \
       multistep-devs:24.04 bash

