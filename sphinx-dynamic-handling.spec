# ----------------------------------------------------------------------
# Header Section
# ----------------------------------------------------------------------
Name:           sphinx-dynamic-handling
Version:        1.0.0
Release:        1%{?dist}
Summary:        Documentation and asset files for sphinx-dynamic-generator.
License:        MIT
URL:            https://github.com/erladion/sphinx-dynamic-generator
Source0:        %{name}-%{version}.tar.gz

## Makes the package relocatable.
Prefix:         %{_prefix} 

%description
This package contains the configuration, utility scripts, and source assets 
(RST templates, extensions, static files) necessary for building 
sphinx-dynamic-generator documentation.


# ----------------------------------------------------------------------
# Preparation Section
# ----------------------------------------------------------------------
%prep
%setup -q


# ----------------------------------------------------------------------
# Installation Section
# ----------------------------------------------------------------------
%install
## Define the relocatable target application data directory.
DATADIR=%{buildroot}%{_prefix}/share/%{name}

# Create the base application and the 'documentation' directories
install -d -m 755 $DATADIR/documentation

# Create the empty chapters folder inside the documentation directory
install -d -m 755 $DATADIR/documentation/chapters

# 1. Install build-docs.sh (Relocatable: Ends up alongside 'documentation' folder)
install -p -m 755 build-docs.sh $DATADIR/

# 2. Install Files into $DATADIR/documentation/
# The primary documentation config files
install -p -m 644 source/conf.py $DATADIR/documentation/
install -p -m 644 source/index_template.rst $DATADIR/documentation/

# The generator script (give executable permission)
install -p -m 755 source/generator.py $DATADIR/documentation/

# 3. Install Subdirectories (recursively copy all contents)
install -d -m 755 $DATADIR/documentation/_static
cp -a source/_static/* $DATADIR/documentation/_static/

install -d -m 755 $DATADIR/documentation/extensions
cp -a source/extensions/* $DATADIR/documentation/extensions/

# 4. Install Documentation/License Files
install -d -m 755 %{buildroot}%{_docdir}/%{name}
install -p -m 644 LICENSE %{buildroot}%{_docdir}/%{name}/

# ----------------------------------------------------------------------
# Files Section
# ----------------------------------------------------------------------
%files
%license LICENSE
%{_docdir}/%{name}/LICENSE 

# The main build script
%attr(755,root,root) %{_prefix}/share/%{name}/build-docs.sh

# Documentation files and generator script
%attr(644,root,root) %{_prefix}/share/%{name}/documentation/conf.py
%attr(644,root,root) %{_prefix}/share/%{name}/documentation/index_template.rst
%attr(755,root,root) %{_prefix}/share/%{name}/documentation/generator.py

# Directories
%{_prefix}/share/%{name}/documentation/_static/
%{_prefix}/share/%{name}/documentation/extensions/

# The empty chapters folder
%dir %{_prefix}/share/%{name}/documentation/chapters