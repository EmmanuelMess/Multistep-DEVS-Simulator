

### Build

docker build -t multistep-devs:24.04 .

### Run

docker run -it \
       --workdir /root/code \
       -v $PWD/code/:/root/code/:rw \
       multistep-devs:24.04 opencode

