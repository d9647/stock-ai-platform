# Nix configuration for Stock AI Platform
# Defines system-level dependencies needed for the backend API

{ pkgs }: {
  deps = [
    # Python 3.11
    pkgs.python311
    pkgs.python311Packages.pip
    pkgs.python311Packages.setuptools
    pkgs.python311Packages.wheel

    # PostgreSQL
    pkgs.postgresql_16
    pkgs.postgresql_16.lib

    # Essential build tools
    pkgs.gcc
    pkgs.pkg-config

    # Required for psycopg2 (PostgreSQL adapter)
    pkgs.libpq

    # Required for some Python packages
    pkgs.openssl
    pkgs.zlib

    # For TA-Lib (technical analysis library)
    pkgs.ta-lib
  ];

  # Environment setup
  env = {
    PYTHON_LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath [
      pkgs.stdenv.cc.cc.lib
      pkgs.zlib
      pkgs.postgresql_16.lib
      pkgs.libpq
    ];
  };
}
