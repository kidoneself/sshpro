# Docker 数据目录

该目录用于存放运行时需要持久化的文件，例如：

- `compose/`：远程执行 `docker compose` 时生成的 `docker-compose.yml` 和 `.env`
- `downloads/`：批量下载脚本保存的压缩包或资源文件
- `tmp/`：执行临时脚本时使用的缓存文件

在目标主机上，应用会将“Docker 配置路径”再拼接 `/naspt` 作为根目录。例如输入 `/volume1/docker`，最终文件会落在 `/volume1/docker/naspt/...`。未手动填写时默认使用 `/docker/naspt`。也可以通过设置环境变量 `NASPT_REMOTE_BASE_DIR` 覆盖 Docker 配置路径（无需带 `/naspt`，程序会自动追加）。

为了避免把生产数据提交到 Git，这些子目录都放了 `.gitkeep` 占位符。

