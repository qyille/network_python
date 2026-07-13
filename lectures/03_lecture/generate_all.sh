#!/usr/bin/env bash
# Генерация pb2-файлов для всех примеров
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"

# 01_hello_grpc
python -m grpc_tools.protoc \
    -I "$HERE/examples/01_hello_grpc" \
    --python_out="$HERE/examples/01_hello_grpc" \
    --grpc_python_out="$HERE/examples/01_hello_grpc" \
    "$HERE/examples/01_hello_grpc/hello.proto"

# 02_streaming
python -m grpc_tools.protoc \
    -I "$HERE/examples/02_streaming" \
    --python_out="$HERE/examples/02_streaming" \
    --grpc_python_out="$HERE/examples/02_streaming" \
    "$HERE/examples/02_streaming/streaming.proto"

# 03_grpc_vs_rest
python -m grpc_tools.protoc \
    -I "$HERE/examples/03_grpc_vs_rest" \
    --python_out="$HERE/examples/03_grpc_vs_rest" \
    --grpc_python_out="$HERE/examples/03_grpc_vs_rest" \
    "$HERE/examples/03_grpc_vs_rest/bookstore.proto"

# 04_errors_interceptors
python -m grpc_tools.protoc \
    -I "$HERE/examples/04_errors_interceptors" \
    --python_out="$HERE/examples/04_errors_interceptors" \
    --grpc_python_out="$HERE/examples/04_errors_interceptors" \
    "$HERE/examples/04_errors_interceptors/errors.proto"

echo "✅ Все pb2-файлы сгенерированы"
