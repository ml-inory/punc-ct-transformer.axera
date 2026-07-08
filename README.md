# Sherpa Punctuation CT-Transformer for AX650

中文标点预测，CT-Transformer 架构，AX650 NPU3。输入 int32 [1,64] token IDs，输出 6 类标点：`，` `。` `？` `、`。

原始模型：[sherpa-onnx](https://k2-fsa.github.io/sherpa/onnx/punctuation/pretrained_models.html#id4) · ONNX ~281MB · AXMODEL ~270MB · 词表 272,727

## 板端要求

AX650，`/soc/lib/libax_engine.so` 存在。若 `ctypes.util.find_library('ax_engine')` 返回 None：
```bash
echo "/soc/lib" >> /etc/ld.so.conf && ldconfig
```

## 获取模型

```bash
# 下载 ONNX → Pulsar2 编译
wget https://huggingface.co/csukuangfj/sherpa-onnx-punct-ct-transformer-zh-en-vocab272727-2024-04-12/resolve/main/model.onnx -O model_convert/model.onnx
cd model_convert && ./compile_pulsar2.sh
cp compile/model.axmodel ../models/
```

## Python SDK

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple numpy onnxruntime

# pyaxengine（板端若无法访问 GitHub，PC 下载 wheel 后 scp）
pip install /tmp/axengine-0.1.3-py3-none-any.whl

# 运行
PYTHONPATH=python python python/sherpa_punct_sdk/example.py
PYTHONPATH=python python python/sherpa_punct_sdk/example.py "今天天气真好我们出去散步吧"
```

## C++ SDK

```bash
# 拉取板端头文件和库
scp -r root@<board>:/soc/lib/ ax_libs/
scp -r root@<board>:/soc/include/ ax_headers/

# 交叉编译
cd cpp
<CROSS_COMPILE_PREFIX>g++ -std=c++17 \
    -Iinclude -I../ax_headers/include -L../ax_libs/lib \
    -Wl,-rpath-link,../ax_libs/lib \
    -o demo src/punctuation_runner.cpp examples/demo.cpp \
    -lax_engine -lax_sys -lpthread -ldl

# 上板运行
scp demo root@<board>:/tmp/
ssh root@<board> "cd /tmp && LD_LIBRARY_PATH=/soc/lib ./demo /path/to/model.axmodel /path/to/tokens.json"
```

## 模型转换（从零复现）

详见 [`model_convert/README.md`](model_convert/README.md)。

## 性能

| SDK | 引擎 | 延迟 |
|-----|------|------|
| C++ | AX_ENGINE_RunSync | 0.254ms |
| Python | pyaxengine | ~同 |
