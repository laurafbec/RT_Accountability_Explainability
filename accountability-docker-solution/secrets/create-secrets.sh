#!/bin/bash

set -o nounset \
    -o errexit \
    -o verbose \
    -o xtrace

#Cleanup files
rm -f *.crt *.csr *creds *.key *.jks *.p12 *.pem *.srl
rm -rf CA zookeeper broker broker1 connect producer mongo

# Generate CA key
mkdir CA
cd CA
openssl req -new -x509 -keyout ca-1.key -out ca-1.crt -days 9999 -subj "/CN=ca1/OU=TEST/O=TEST/L=Leon/S=CL/C=ES" -passin pass:123456 -passout pass:123456
cd ..

for i in zookeeper broker broker1 connect producer mongo
do
	echo $i
        mkdir $i
        cd $i
	# Create host keystore
	keytool -genkey -noprompt \
				 -alias $i \
				 -dname "CN=$i, OU=TEST, O=TEST, L=Leon, S=CL, C=ES" \
				 -keystore kafka.$i.keystore.jks \
				 -keyalg RSA \
				 -storepass 123456 \
				 -keypass 123456

	# Create the certificate signing request (CSR)
	keytool -keystore kafka.$i.keystore.jks -alias $i -certreq -file $i.csr -storepass 123456 -keypass 123456 -noprompt

	#Sign the host certificate with the certificate authority (CA)
	openssl x509 -req -CA ../CA/ca-1.crt -CAkey ../CA/ca-1.key -in $i.csr -out $i-ca1-signed.crt -days 9999 -CAcreateserial -passin pass:123456

	#Import the CA cert into the keystores
	keytool -keystore kafka.$i.keystore.jks -alias CARoot -import -file ../CA/ca-1.crt -storepass 123456 -keypass 123456 -noprompt

	#Import the signed host certificate into the keystore
	keytool -keystore kafka.$i.keystore.jks -alias $i -import -file $i-ca1-signed.crt -storepass 123456 -keypass 123456 -noprompt

	# Create truststore and import the CA cert.
	keytool -keystore kafka.$i.truststore.jks -alias CARoot -import -file ../CA/ca-1.crt -storepass 123456 -keypass 123456 -noprompt

  # Save creds
  echo "123456" > ${i}_sslkey_creds
  echo "123456" > ${i}_keystore_creds
  echo "123456" > ${i}_truststore_creds
cd ..
done

cp broker/* broker1
cp CA/ca-1.crt producer
cp CA/ca-1.crt mongo

#Export private key from producer keystore
#Create .pem store for caroot used in python producer
cd producer
keytool -importkeystore -srckeystore kafka.producer.keystore.jks  -destkeystore kafka.producer.keystore.p12  -deststoretype PKCS12 -srcalias producer -deststorepass 123456  -srcstorepass 123456 -noprompt
openssl pkcs12 -in kafka.producer.keystore.p12  -nokeys -out producer.pem -passin pass:123456
openssl pkcs12 -in kafka.producer.keystore.p12  -nodes -nocerts -out producer_key.pem -passin pass:123456
keytool -exportcert -alias CARoot -keystore kafka.producer.keystore.jks -rfc -file CARoot.pem -storepass 123456 -keypass 123456
cd ..

cd mongo
keytool -importkeystore -srckeystore kafka.mongo.keystore.jks  -destkeystore kafka.mongo.keystore.p12  -deststoretype PKCS12 -srcalias mongo -deststorepass 123456  -srcstorepass 123456 -noprompt
openssl pkcs12 -in kafka.mongo.keystore.p12  -nokeys -out mongo.pem -passin pass:123456
openssl pkcs12 -in kafka.mongo.keystore.p12  -nodes -nocerts -out mongo_key.pem -passin pass:123456
cat mongo.pem mongo_key.pem > mongo_all.pem
cd ..
