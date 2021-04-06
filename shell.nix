{ pkgs ? import <nixpkgs> {} }:

let
  pythonEnv = pkgs.poetry2nix.mkPoetryEnv {
    projectDir = ./.;
    # preferWheels = true;
  };
in pkgs.mkShell {
  buildInputs = [
    pythonEnv
    pkgs.python38Packages.poetry
  ];
}
