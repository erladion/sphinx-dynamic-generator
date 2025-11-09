#--- Project Configuration ---
NAME := sphinx-dynamic-handling
VERSION := 1.0.0
RELEASE := 1
ARCHIVE := $(NAME)-$(VERSION)
TARBALL := $(ARCHIVE).tar.gz
SPEC_FILE := $(NAME).spec
RPM_DIR := $(HOME)/rpmbuild
SOURCES_DIR := $(RPM_DIR)/SOURCES
BUILD_OPTS := -ba

.PHONY: all clean tar rpm source

all: rpm

#=====================================================================
#Source Tarball Management
#=====================================================================
tar: $(TARBALL)

#Target to create the source tarball.
$(TARBALL): clean_archive
	@echo "📦 Creating source directory $(ARCHIVE)/..."
	mkdir $(ARCHIVE)

	@echo "📂 Copying files into $(ARCHIVE)/..."
# Files must be copied to match the relative paths used in the spec file's %install section
	cp build-docs.sh $(ARCHIVE)/
	cp -r source $(ARCHIVE)/
	cp LICENSE $(ARCHIVE)/

	@echo "🎁 Compressing into $(TARBALL)..."
	tar -czvf $(TARBALL) $(ARCHIVE)/

	@echo "🗑️ Cleaning up temporary directory..."
	rm -rf $(ARCHIVE)


source: tar

#Target to clean up the temporary directory and tarball
clean_archive:
	@echo "🧹 Cleaning up previous build artifacts..."
	rm -f $(TARBALL)
	rm -rf $(ARCHIVE)

#=====================================================================
#RPM Build Management
#=====================================================================
rpm: $(TARBALL)
	@echo "📤 Copying $(TARBALL) to RPM SOURCES directory..."
	mkdir -p $(SOURCES_DIR)
	cp $(TARBALL) $(SOURCES_DIR)/

	@echo "⚙️ Starting RPM build for $(SPEC_FILE)..."
	# The --define '_topdir $(RPM_DIR)' is often necessary for some environments
	rpmbuild $(BUILD_OPTS) --define "_topdir $(RPM_DIR)" $(SPEC_FILE)

	rm -f $(TARBALL)


#=====================================================================
#General Cleanup
#=====================================================================
clean: clean_archive
	@echo "Removing temporary RPM files..."
	rm -rf $(RPM_DIR)/BUILD/$(ARCHIVE)
	rm -f $(RPM_DIR)/RPMS//.rpm
	rm -f $(RPM_DIR)/SRPMS/*.rpm
	@echo "Removing source tarball from RPM SOURCES directory..."
	rm -f $(SOURCES_DIR)/$(TARBALL)