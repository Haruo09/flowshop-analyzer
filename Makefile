CXX := g++
CXXFLAGS := -O3 -std=c++20 -Wall -Wextra -Iinclude

UNAME_S := $(shell uname -s)
ifeq ($(OS),Windows_NT)
	SHARED_EXT := .dll
	EXE_EXT := .exe
	PIC_FLAG :=
	MKDIR_CMD := python -c "import os; os.makedirs('build/lib', exist_ok=True); os.makedirs('build/bin', exist_ok=True)"
	RM_CMD := python -c "import shutil; shutil.rmtree('build', ignore_errors=True)"
else ifeq ($(UNAME_S),Darwin)
	SHARED_EXT := .dylib
	EXE_EXT :=
	PIC_FLAG := -fPIC
	MKDIR_CMD := mkdir -p build/lib build/bin
	RM_CMD := rm -rf build
else
	SHARED_EXT := .so
	EXE_EXT :=
	PIC_FLAG := -fPIC
	MKDIR_CMD := mkdir -p build/lib build/bin
	RM_CMD := rm -rf build
endif

LIB_DIR := build/lib
BIN_DIR := build/bin
LIB_TARGET := $(LIB_DIR)/libflowshop$(SHARED_EXT)
BIN_TARGET := $(BIN_DIR)/flowshop_runner$(EXE_EXT)

LIB_SRCS := $(wildcard src/*.cpp)
HEADERS := $(wildcard include/flowshop_analyzer/*.h include/flowshop_analyzer/*.hpp)

.PHONY: all clean dirs

all: dirs $(LIB_TARGET) $(BIN_TARGET)

dirs:
	@$(MKDIR_CMD)

$(LIB_TARGET): $(LIB_SRCS) $(HEADERS)
	$(CXX) $(CXXFLAGS) $(PIC_FLAG) -shared $(LIB_SRCS) -o $(LIB_TARGET)

$(BIN_TARGET): apps/main.cpp $(LIB_SRCS) $(HEADERS)
	$(CXX) $(CXXFLAGS) apps/main.cpp $(LIB_SRCS) -o $(BIN_TARGET)

clean:
	@$(RM_CMD)
