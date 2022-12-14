FROM apache/druid:24.0.1

RUN mkdir -p /opt/druid/extensions/druid-protobuf-extensions
RUN wget -O /opt/druid/extensions/druid-protobuf-extensions/kafka-protobuf-provider-6.0.1.jar https://packages.confluent.io/maven/io/confluent/kafka-protobuf-provider/6.0.1/kafka-protobuf-provider-6.0.1.jar
RUN wget -O /opt/druid/extensions/druid-protobuf-extensions/kotlin-stdlib-1.4.0.jar https://repo1.maven.org/maven2/org/jetbrains/kotlin/kotlin-stdlib/1.4.0/kotlin-stdlib-1.4.0.jar
RUN wget -O /opt/druid/extensions/druid-protobuf-extensions/wire-schema-3.2.2.jar https://repo1.maven.org/maven2/com/squareup/wire/wire-schema/3.2.2/wire-schema-3.2.2.jar
