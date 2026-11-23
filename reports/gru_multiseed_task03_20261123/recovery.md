# 准入检查恢复记录

第一次配置比对退出 1，未执行 GPU Batch 或正式训练。预备配置以 JSON 格式写入 .yaml 文件时，PyYAML 将科学计数法 1e-08 解析为字符串。用原数值生成 YAML 浮点标量并重新核对所有字段，Adam eps 数值保持 1e-8。首次检查日志保留。

第二次检查在收集系统版本时退出 1，原因是运行环境 Python 3.9 缺少 platform.freedesktop_os_release。改读 /etc/os-release 后重新执行全量检查。该次也未启动训练。
