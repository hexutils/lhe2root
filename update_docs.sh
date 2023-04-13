#!/bin/bash
rm docs/source/modules.rst #need to update the module.rst
sphinx-apidoc ./ -o docs/source #the code should be in the same directory if you want to document it

shopt -s extglob

cd docs
rm -rf -- !("build"|"source") #extglob allows for this
cd ../

make clean
make html

shopt -s dotglob
mv docs/build/html/* docs/ #places the documents here because of the way github pages works