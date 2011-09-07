# /bin/bash
# builds documentation and pushes it to GitHub Pages

# The clean command might throw errors (trying to delete non-existent files), so
# we want to prevent it to stop the script from working.
function make_clean {
    set +e
    make clean
    set -e
}

# exit immediately in case of errors
set -e

# only committed changes must be documented!
git stash

# make a clean build of the html files and moves it out of the way.
make_clean
make html
mkdir /tmp/atc-docs
cp -R _build/html/* /tmp/atc-docs/
make_clean

# save aptana project files
cd ..
mkdir /tmp/atc-project-files
mv .project .pydevproject /tmp/atc-project-files

# switch to GitHub pages repository and imports the build
git checkout gh-pages
rm -rdf *
cp -r /tmp/atc-docs/* .
rm -rf /tmp/atc-docs
touch .nojekyll

# track changes and pushes them to the server
git add . .nojekyll
git commit -a -m "Automatic Documentation Build"
git push

# revert to normal editing mode
git checkout master
cp /tmp/atc-project-files .
rm -rf /tmp/atc-project-files
git stash pop
