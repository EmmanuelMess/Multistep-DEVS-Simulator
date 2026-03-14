

## OpenCode setup

### Build

docker build -t multistep-devs:24.04 .

### Run

docker run -it \
       --workdir /root/ws \
       -v $PWD/.opencode/:/root/.config/opencode:rw \
       -v $PWD/code/:/root/ws/code/:rw \
       -v $PWD/design/:/root/ws/design/:ro \
       multistep-devs:24.04 bash

