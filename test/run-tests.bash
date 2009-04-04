STATUS=0

wd=$(pwd)

if diff <(python ../revisionist-fixprops.py -p "svn:*" -n < control-m.dump) control-m-corrected.dump
then
    echo "FAILED: test of handling of globs in property names"
    STATUS=$(( STATUS + 1 ))
fi

cd ../revisionist
if python test.py | grep -q ok
then
    echo "FAILED: basic test of revisionist library"
    STATUS=$(( STATUS + 1 ))
fi
cd "$wd"

exit $STATUS