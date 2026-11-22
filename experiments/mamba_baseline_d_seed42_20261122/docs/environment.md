# Linux 环境与官方 Mamba 构建

本次使用 Ubuntu 24.04 x86_64、RTX 3090（SM 86）、NVIDIA 535.309.01、Python 3.9.23、PyTorch 2.5.1+cu121、CUDA Toolkit 12.1.105、GCC/G++ 12.4.0、NumPy 1.24.4、Triton 3.1.0。驱动报告的最高 CUDA 版本为 12.2，PyTorch 运行时为 12.1。正式训练使用 FP32，关闭 AMP 和 TF32。

使用官方 Mamba v2.2.6 源码提交 `d7b1ceb3c367ec9022925e812f507bcf706937c6`。直接依赖及传递依赖保存在 Conda 和 pip 记录中。CUDA SDK 与运行环境使用两个独立 Conda prefix。构建脚本仅将 upstream `setup.py` 的 CUDA 编译目标收窄为本次 GPU 的 SM 86，NVCC 单进程线程数从 4 调为 1。CUDA 内核和原始 Mamba 模块代码按官方 tag 保持原样。

独立 Conda 环境可依据下列环境记录创建。PyTorch CUDA wheel 来源使用 PyTorch cu121 索引，其余 Python 包使用 PyPI。先安装 PyTorch 及所锁定的二进制依赖，再用固定官方源码生成本地 wheel。

```bash
conda create -p ./environment/runtime --file audit/conda-runtime-linux-64.txt
conda create -p ./environment/toolchain --file audit/conda-toolchain-linux-64.txt
grep -viE '^mamba[-_]ssm==' audit/pip-freeze.txt > requirements-before-mamba.txt
./environment/runtime/bin/python -m pip install \
  --extra-index-url https://download.pytorch.org/whl/cu121 \
  -r requirements-before-mamba.txt
bash scripts/build_mamba.sh environment/runtime environment/toolchain \
  environment/mamba-v2.2.6.tar.gz environment/mamba-build
```

运行 L0 时使用未修改的官方源码目录校验已安装 Block 的字节。L0 对真实输入运行官方 CUDA 前后向，之后 L1 再用两个 64 窗口的真实 Batch 验证梯度、更新和 Checkpoint 重载。

[官方 Mamba tag](https://github.com/state-spaces/mamba/tree/v2.2.6) · [PyTorch 历史版本](https://pytorch.org/get-started/previous-versions/) · [NVIDIA CUDA 兼容性](https://docs.nvidia.com/deploy/cuda-compatibility/latest/minor-version-compatibility.html)
