# Quickstart

## OpenSSL + OQS Provider  
### Ubuntu 
        https://developer.ibm.com/tutorials/awb-quantum-safe-openssl/

### macOS-en kicsit más:
        xcode-select --install
        brew install cmake ninja git openssl

        export WORKSPACE=/Users/kolosmacbook/Desktop/oqs
        export BUILD_DIR=$WORKSPACE/build
        
        mkdir -p $BUILD_DIR/lib64
        ln -s $BUILD_DIR/lib64 $BUILD_DIR/lib

        cd $WORKSPACE
        git clone https://github.com/openssl/openssl.git
        cd openssl

        ./Configure \
                --prefix=$BUILD_DIR \
                no-ssl no-tls1 no-tls1_1 no-afalgeng \
                no-shared threads -lm darwin64-x86_64-cc \ 

        make -j $(sysctl -n hw.ncpu)
        make -j $(sysctl -n hw.ncpu) install_sw install_ssldirs

        cd $WORKSPACE
        git clone https://github.com/open-quantum-safe/liboqs.git
        cd liboqs

        mkdir build && cd build
        cmake \
                -DCMAKE_INSTALL_PREFIX=$BUILD_DIR \
                -DBUILD_SHARED_LIBS=ON \
                -DOQS_USE_OPENSSL=OFF \
                -DCMAKE_BUILD_TYPE=Release \
                -DOQS_BUILD_ONLY_LIB=ON \
                -DOQS_DIST_BUILD=ON \
                ..
        
        make -j $(sysctl -n hw.ncpu)
        make -j $(sysctl -n hw.ncpu) install

        cd $WORKSPACE
        git clone https://github.com/open-quantum-safe/oqs-provider.git
        cd oqs-provider

        liboqs_DIR=$BUILD_DIR cmake \
                -DCMAKE_INSTALL_PREFIX=$WORKSPACE/oqs-provider \
                -DOPENSSL_ROOT_DIR=$BUILD_DIR \
                -DCMAKE_BUILD_TYPE=Release \
                -S . \
                -B _build

        cmake --build _build

        cp _build/lib/* $BUILD_DIR/lib/

        sed -i "" "s/default = default_sect/default = default_sect\noqsprovider = oqsprovider_sect/g" $BUILD_DIR/ssl/openssl.cnf
        echo -e "\n[ oqsprovider_sect ]\nactivate = 1" >> $BUILD_DIR/ssl/openssl.cnf

        export OPENSSL_CONF=$BUILD_DIR/ssl/openssl.cnf
        export OPENSSL_MODULES=$BUILD_DIR/lib
        export PATH=$BUILD_DIR/bin:$PATH


        TESZT:
        $BUILD_DIR/bin/openssl list -providers -verbose -provider oqsprovider

### egyszerűbben:
        https://www.linode.com/docs/guides/post-quantum-encryption-nginx-ubuntu2404/
        
        brew install openssl cmake ninja git

        Válasszunk egy mappát, amiben:
        git clone https://github.com/open-quantum-safe/oqs-provider.git
        cd oqs-provider
        scripts/fullbuild.sh
        sudo cmake --install _build
        scripts/runtests.sh

        edit openssl.cnf
                oqsprovider = oqsprovider_sect
                [oqsprovider_sect] 
                        activate = 1
        
        openssl list -providers
        openssl list -kem-algorithms -provider oqsprovider | egrep -i "(kyber|kem)768"


## CA Certificate, hogy localhost-on tesztelhessük https-t (macOs Keychain Access)
### https://deliciousbrains.com/ssl-certificate-authority-for-local-https-development/
        backend/cert:
        openssl genrsa -des3 -out myCA.key 2048
                passphrase: 1234
        openssl req -x509 -new -nodes -key myCA.key -sha256 -days 1825 -out myCA.pem
        

        sudo security add-trusted-cert -d -r trustRoot -k "/Library/Keychains/System.keychain" myCA.pem


        openssl genrsa -out localhost.key 2048
        openssl req -new -key localhost.key -out localhost.csr
        
        localhost.ext-be:
                authorityKeyIdentifier=keyid,issuer
                basicConstraints=CA:FALSE
                keyUsage = digitalSignature, nonRepudiation, keyEncipherment, dataEncipherment
                subjectAltName = @alt_names

                [alt_names]
                DNS.1 = localhost
        

        openssl x509 -req -in localhost.csr -CA myCA.pem -CAkey myCA.key \
                -CAcreateserial -out localhost.crt -days 825 -sha256 -extfile localhost.ext

        sudo security add-trusted-cert -d -r trustRoot -k "/Library/Keychains/System.keychain" localhost.crt

        killall "Google Chrome"


## NgingX buildelése buildelése OQS-es OpenSSL-el
### build
        export WORKSPACE=/Users/kolosmacbook/Desktop/oqs
        cd $WORKSPACE
        
        wget http://nginx.org/download/nginx-1.26.0.tar.gz
        tar xvf nginx-1.26.0.tar.gz
        cd nginx-1.26.0

        ./configure --prefix=$WORKSPACE/custom-nginx  \
                --with-http_ssl_module \
                --with-openssl=$WORKSPACE/openssl \
                --with-openssl-opt="enable-ec_nistp_64_gcc_128"
        
        make -j$(sysctl -n hw.ncpu)
        make install

        #proxy kódja: custom-nginx/conf/nginx.conf

        export CUSTOM_NGINX=$WORKSPACE/custom-nginx
        
        $CUSTOM_NGINX/sbin/nginx -c $CUSTOM_NGINX/conf/nginx.conf
        $CUSTOM_NGINX/sbin/nginx -s stop

### futtatás (külön terminálban)
#### indítás
        export WORKSPACE=/Users/kolosmacbook/Desktop/oqs
        export CUSTOM_NGINX=$WORKSPACE/custom-nginx
        $CUSTOM_NGINX/sbin/nginx -c $CUSTOM_NGINX/conf/nginx.conf
#### leállítás
        export WORKSPACE=/Users/kolosmacbook/Desktop/oqs
        export CUSTOM_NGINX=$WORKSPACE/custom-nginx
        $CUSTOM_NGINX/sbin/nginx -s stop


## /backend:
        cd backend
        python3 -m venv env
        source env/bin/activate
        pip install --no-cache-dir -r requirements.txt

        uvicorn server:app --host 0.0.0.0 --port 8000 --reload

        tesztek futtatása:
                source env/bin/activate
                PYTHONPATH=. pytest


## /frontend:
        cd frontend
        npm i
        npm run dev
        
        or

        npm run build
        npm start


## test users:
t@g.c
t
cae9b6905136901b9f17fc6389fbdf9e00d10fb05ffcdf40e98f45014ee5fdcc

tibor@test.com
testtibor
75259b4bc1fdc3d125396ec588bb929ad9cb3b50d0e599b02044040c0f19537b



3394a700934ec193bf03944a2bce8658364418aca6b1dc4e74d254e22bf62b76


valami2@g.com
12345678
7e31484437aceff126aeafca26b76f4c8aae820b9e5a3c19d08d58072efb8b80

tibor3@test.com
12345678
090c9fe67c7067045c5c74b3f975a573b6a3076fc776664966e9132f7fade48a