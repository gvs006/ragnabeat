FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Instalando o MySQL Client original que o CMake precisa
RUN apt-get update && apt-get install -y \
    cmake make gcc g++ libmysqlclient-dev zlib1g-dev libpcre3-dev netcat-openbsd pkg-config \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /server

# Como foi feito antes de usar o athena-start
# CMD ["/bin/bash", "-c", "rm -rf build && mkdir build && cd build && cmake -G 'Unix Makefiles' -DENABLE_PRERE=ON -DENABLE_PACKETVER=20211103 -DALLOW_SAME_DIRECTORY=ON .. && make clean && make && cd .. && ./athena-start start"]

CMD ["./athena-start", "start"]