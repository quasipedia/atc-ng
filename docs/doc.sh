# /bin/bash
# builds documentation and pushes it to GitHub Pages

# only committed changes must be documented!
git stash

# make a clean build of the html files and moves it out of the way
make clean
make html
mkdir /tmp/atc-docs
cp -R _build/html/* /tmp/atc-docs/
make clean

# switch to GitHub pages repository and imports the build
cd ..
git checkout gh-pages
rm -Rdf *
cp -R /tmp/atc-docs/* .
rm -Rf /tmp/atc-docs
touch .nojekyll

# track changes and pushes them to the server
git add . .nojekyll
git commit -a -m "Automatic Documentation Build"
git push

# revert to normal editing mode
git checkout master
git stash pop
