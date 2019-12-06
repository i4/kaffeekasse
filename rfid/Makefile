PACKAGE    := getuid
TARGET     := armv7a-unknown-linux-gnueabihf
PKG_CONFIG := $(TARGET:%=%-)pkg-config
CC         := $(TARGET:%=%-)gcc
VERBOSE    := @
VARIANT    ?= release

PACKAGES   := libfreefare libnfc libcrypto
BINARY     := bin/$(TARGET)/$(VARIANT)
PREFIX     := /usr/local
obj-dir    := obj/$(TARGET)/$(VARIANT)
dep-dir    := dep/$(TARGET)/$(VARIANT)
src-dir    := src
src-y      := $(wildcard $(src-dir)/*.c)
mod-y      := $(patsubst %.c,%,$(notdir $(src-y)))
obj-y      := $(mod-y:%=$(obj-dir)/%.o)
dep-y      := $(src-y:%=$(dep-dir)/%.d)

CFLAGS     := $(CFLAGS) -D_DEFAULT_SOURCE -D_POSIX_C_SOURCE=200809L -std=c99 -g -Wall -Werror $(shell $(PKG_CONFIG) --cflags libfreefare libnfc libcrypto)
LDFLAGS    := $(LDFLAGS) $(shell $(PKG_CONFIG) --libs libnfc libfreefare libcrypto)

ifeq ($(VERBOSE),)
$(info PACKAGE:    $(PACKAGE))
$(info TARGET:     $(TARGET))
$(info PKG_CONFIG: $(PKG_CONFIG))
$(info PACKAGES:   $(PACKAGES))
$(info VARIANT:    $(VARIANT))
$(info CC:         $(CC))
$(info CFLAGS:     $(CFLAGS))
$(info LDFLAGS:    $(LDFLAGS))
$(info obj-dir:    $(obj-dir))
$(info dep-dir:    $(dep-dir))
$(info src-dir:    $(src-dir))
$(info obj-y:      $(obj-y))
$(info dep-y:      $(dep-y))
$(info src-y:      $(src-y))
endif

all: $(VARIANT)

ifeq ($(VARIANT), release)
CFLAGS += -O2 -DNDEBUG
install:
	$(VERBOSE) install -t $(PREFIX)/bin/ $(BINARY)
else ifeq ($(VARIANT), debug)
CFLAGS += -Og -UNDEBUG
else
$(error invalid variant ($(VARIANT)): [debug, release])
endif

$(VARIANT): $(BINARY)
	@printf '%s:\t%s\n' '$@' '$^'

$(filter-out $(VARIANT),debug release):
	$(VERBOSE) $(MAKE) VARIANT=$@

.PHONY: all install release debug

$(BINARY): $(obj-y)
	@mkdir -p $(@D)
	$(VERBOSE) $(CC) -o $@ $< $(LDFLAGS)

$(obj-y): $(obj-dir)/%.o: $(src-dir)/%.c
	@mkdir -p $(@D) $(dir $(dep-dir)/$*.d)
	$(VERBOSE) $(CC) -o $@ -c $^ -MD -MF $(dep-dir)/$*.d $(CPPFLAGS) $(CFLAGS)

clean:
	$(VERBOSE) rm -rf obj dep

-include $(deb-y)
