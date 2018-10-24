with import <nixpkgs> {};

stdenv.mkDerivation {
  name = "saleorEnv";
  buildInputs = [
    git
    nodejs
    postgresql
    # zlib # a system dependency of pillow if building from pypi.
    # openssl # system dependency of cryptography if building
    # from pypi.
    ncurses # system dependency required by uwsgi
    python3Packages.virtualenv
    python3Packages.pip
    python3Packages.cryptography
    python3Packages.cairocffi
    python3Packages.pillow
    # The following packages are required to build cairocffi from pypi
    # but nixos specific patches are needed so we'll use cairocffi
    # from the nixpkgs repo instead.
    # cairo
    # pango
    # gdk_pixbuf
    # libffi
    # pkgconfig
  ];

  shellHook = ''
  SOURCE_DATE_EPOCH=$(date +%s)
  virtualenv --no-setuptools venv
  export PATH=$PWD/venv/bin:$PATH
  export PYTHONPATH=$PWD/venv/bin:$PYTHONPATH
  pip install -r requirements.txt
  export NODE_PATH=$PWD/node_modules
  export PATH=$PWD/node_modules/.bin:$PATH
  '';
}
