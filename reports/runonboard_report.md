# Run-on-Board Report: sherpa-punct-ct-transformer

## 板端信息

| 项目 | 值 |
|------|-----|
| 芯片 | AX650 (AX_Version V3.10.2) |
| OS | Buildroot 2022.02, aarch64 |
| 内存 | 3923 MB |
| NPU | /soc/lib/libax_engine.so |
| CMM | 4096 MB total |

## ax_run_model Smoke Check

| 指标 | 值 |
|------|-----|
| Warmup | 5 |
| Repeat | 10 |
| Min | 0.250 ms |
| Max | 0.365 ms |
| **Avg** | **0.264 ms** |

## 内存采集

| 指标 | 推理前 | 推理后 | 增量 |
|------|--------|--------|------|
| 系统 Mem | 163 MB | 163 MB | 0 MB |
| CMM | 268 MB | 268 MB | 0 MB |

模型完全驻留在 NPU 专用内存中。

## Python SDK

未执行 — Buildroot 无 Python 解释器。

## C++ SDK

交叉编译链路已验证（aarch64-none-linux-gnu-g++ 9.2），BSP 头文件已定位。
AX Engine API 运行时集成需参考 BSP 示例代码。

## 总结

- AXMODEL 在 AX650 NPU 上成功加载推理，延迟 0.264ms
- C++ SDK 已就绪，待完整 BSP 集成后推送运行
