# Makefile for GoogleTest unit testing executable

# HIT
HIT_DIR = ../hit

# Google Test (gtest)
GTEST_DIR = ../gtest

# MOOSETools contrib unit testing source files
UNIT_SRCFILES := $(shell find ./src -name "*.C")

# Flags passed to the C++ compiler.
CXXFLAGS += -g

all : moosetools-unit

check : all
	./moosetools-unit

clean :
	rm -rf moosetools-unit *.o

parse.o lex.o braceexpr.o: $(HIT_DIR)/parse.cc $(HIT_DIR)/lex.cc $(HIT_DIR)/braceexpr.cc $(HIT_DIR)/braceexpr.h $(HIT_DIR)/lex.h $(HIT_DIR)/parse.h
	$(CXX) $(CXXFLAGS) -I$(HIT_DIR) -c $(HIT_DIR)/parse.cc $(HIT_DIR)/lex.cc $(HIT_DIR)/braceexpr.cc

gtest-all.o : $(GTEST_DIR)/gtest/gtest.h $(GTEST_DIR)/gtest-all.cc
	$(CXX) $(CXXFLAGS) -I$(GTEST_DIR) -c $(GTEST_DIR)/gtest-all.cc

gtest-main.o : gtest-all.o
	$(CXX) $(CXXFLAGS) -I$(GTEST_DIR) -c $(GTEST_DIR)/gtest-main.cc

moosetools-unit.o : $(UNIT_SRCFILES)
	$(CXX) $(CXXFLAGS) -I$(GTEST_DIR) -I$(HIT_DIR) -c $(UNIT_SRCFILES) -o $@

moosetools-unit : moosetools-unit.o gtest-all.o gtest-main.o parse.o lex.o braceexpr.o
	$(CXX) $(CXXFLAGS) -I$(GTEST_DIR) -I$(HIT_DIR) $^ -o $@
