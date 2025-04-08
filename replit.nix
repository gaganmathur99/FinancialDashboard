{pkgs}: {
  deps = [
    pkgs.postgresql
    pkgs.sqlite
    pkgs.flutter
    pkgs.rustc
    pkgs.pkg-config
    pkgs.openssl
    pkgs.libxcrypt
    pkgs.libiconv
    pkgs.cargo
    pkgs.glibcLocales
  ];
}
