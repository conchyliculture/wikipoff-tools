wget -nc https://pypi.python.org/packages/fe/33/9fa773d6f2f11d95f24e590190220e23badfea3725ed71d78908fbfd4a14/pylzma-0.4.8.tar.gz#md5=7040c489c7bbd0e1a4331484e1579261

tar xvf pylzma-0.4.8.tar.gz
cd pylzma-0.4.8
/usr/bin/python setup.py install --root=../lib/ --prefix=../
/usr/bin/python3 setup.py install --root=../lib/ --prefix=../
