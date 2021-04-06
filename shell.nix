{ pkgs ? import <nixpkgs> {} }:

let
  pythonEnv = pkgs.poetry2nix.mkPoetryEnv {
    projectDir = ./.;
    # preferWheels = true;
  };
in pkgs.mkShell {
  buildInputs = [
    pkgs.python38
    pkgs.python38Packages.poetry
  ];
}
