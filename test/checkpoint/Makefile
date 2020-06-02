CFLAGS := -Wall -Wextra -Wno-long-long -Wpedantic
CC := cc
BIN_DIR := bin

default: all
all: $(BIN_DIR)/PiEst
$(BIN_DIR)/PiEst: pi_est.cc
	if [ ! -d $(BIN_DIR) ]; then mkdir -p $(BIN_DIR); fi
	$(CC) --std=c++11 -lstdc++ -lm $(CFLAGS) $^ -o $@
