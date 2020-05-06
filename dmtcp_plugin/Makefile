# tool macros
CC := cc # FILL: the compiler
CCFLAG := -shared -lstdc++ # FILL: compile flags
DBGFLAG := -g -DDEBUG
INCLUDE = -I../dmtcp/include
CCOBJFLAG := $(CCFLAG) --std=c++11 -c -fPIC -Wall -Wextra -Wno-long-long $(INCLUDE)
MKDIR := mkdir -p

# path macros
OBJ_PATH := .
SRC_PATH := .
DBG_PATH := debug

# compile macros
TARGET_NAME := libcragon_exeinfo.so # : target name
TARGET := $(TARGET_NAME)
TARGET_DEBUG := $(DBG_PATH)/$(TARGET_NAME)

# src files & obj files
SRC := $(foreach x, $(SRC_PATH), $(wildcard $(addprefix $(x)/*,.cpp*)))
OBJ := $(addprefix $(OBJ_PATH)/, $(addsuffix .o, $(notdir $(basename $(SRC)))))
OBJ_DEBUG := $(addprefix $(DBG_PATH)/, $(addsuffix .o, $(notdir $(basename $(SRC)))))

# clean files list
DISTCLEAN_LIST := $(OBJ) \
                  $(OBJ_DEBUG)
CLEAN_LIST := $(TARGET) \
			  $(TARGET_DEBUG) \
			  $(DISTCLEAN_LIST)

# default rule
default: all

# non-phony targets
$(TARGET): $(OBJ)
	$(CC) $(CCFLAG) -o $@ $?

$(OBJ_PATH)/%.o: $(SRC_PATH)/%.cpp*
	$(CC) $(CCOBJFLAG) -o $@ $<

debug_dir: 
	$(MKDIR) $(DBG_PATH)

$(DBG_PATH)/%.o: $(SRC_PATH)/%.cpp* debug_dir 
	$(CC) $(CCOBJFLAG) $(DBGFLAG) -o $@ $<

$(TARGET_DEBUG): $(OBJ_DEBUG)
	$(CC) $(CCFLAG) $(DBGFLAG) $? -o $@

# phony rules
.PHONY: all
all: $(TARGET)

.PHONY: debug
debug: $(TARGET_DEBUG)

.PHONY: clean
clean:
	@echo CLEAN $(CLEAN_LIST)
	@rm -f $(CLEAN_LIST)
	@rmdir $(DBG_PATH)

.PHONY: distclean
distclean:
	@echo CLEAN $(DISTCLEAN_LIST)
	@rm -f $(DISTCLEAN_LIST)
