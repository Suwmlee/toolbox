# 漫画整理工具

一个用于整理漫画并与Komga集成的Python工具。

## 功能特性

- **Tachiyomi转移**: 将Tachiyomi下载的漫画转移到Komga目录
- **漫画整理**: 优化文件夹结构和命名规范
- **Komga集成**: 自动更新Komga元数据（作者、星级）并按星级移动文件

## 项目结构

```
manga/
├── core/               # 核心模块
│   ├── config.py      # 配置管理
│   ├── logger.py      # 日志系统
│   └── constants.py   # 常量定义
├── models/            # 数据模型
│   └── manga_info.py  # 漫画信息类
├── api/               # API封装
│   └── komga_api.py   # Komga API客户端
├── utils/             # 工具函数
│   ├── file_utils.py  # 文件操作
│   └── name_utils.py  # 名称处理
├── services/          # 业务服务层
│   ├── manga_service.py      # 漫画处理服务
│   ├── transfer_service.py   # 转移服务
│   ├── organize_service.py   # 整理服务
│   └── komga_service.py      # Komga服务
├── main.py            # 主程序入口
├── manga.yaml         # 配置文件
└── requirements.txt   # 依赖包
```

## 安装

```bash
# 安装依赖
pip install -r requirements.txt

# 复制配置模板
cp manga.template.yaml manga.yaml

# 编辑配置文件
vim manga.yaml
```

## 使用方法

### 基本命令

```bash
# 查看帮助
python main.py -h

# Tachiyomi转移
python main.py transfer --debug       # 调试模式（不实际执行）
python main.py transfer               # 正式执行

# 漫画整理
python main.py organize --debug       # 调试模式
python main.py organize               # 正式执行

# Komga整理
python main.py komga --debug          # 调试模式
python main.py komga                  # 正式执行

# 组合操作（按顺序执行）
python main.py transfer organize --debug      # 先转移后整理（调试）
python main.py transfer organize              # 先转移后整理（正式）
python main.py transfer organize komga        # 全流程整理

# 强制执行（覆盖配置文件设置）
python main.py transfer --force

# 使用自定义配置文件
python main.py transfer -c custom.yaml --debug
```

### 命令参数说明

#### 操作命令（至少选择一个）

- `transfer` - 从Tachiyomi转移漫画到Komga目录
- `organize` - 整理漫画文件夹（优化命名和结构）
- `komga` - 整理Komga库（更新元数据、按星级移动）

#### 可选参数

- `-h, --help` - 显示帮助信息
- `-d, --debug` - 调试模式，不实际执行操作（仅显示将要执行的操作）
- `-f, --force` - 强制执行模式，覆盖配置文件中的调试模式设置
- `-c, --config PATH` - 指定配置文件路径（默认: manga.yaml）
- `-v, --verbose` - 详细输出模式

## 功能说明

### 1. Tachiyomi转移 (`transfer`)

将Tachiyomi下载目录的漫画转移到Komga目录：

- 自动识别漫画类型（单本/系列）
- 根据配置规则决定是否移动
- 优化漫画和章节命名
- 自动压缩为ZIP格式

### 2. 漫画整理 (`organize`)

优化现有漫画文件夹：

- 统一文件夹结构
- 规范化命名（移除汉化组、调整标签顺序）
- 支持一级和二级目录结构
- 自动处理压缩文件

### 3. Komga整理 (`komga`)

与Komga API集成进行高级整理：

- 自动添加/更新星级标签
- 按星级移动文件到对应目录
- 从文件名提取并更新作者信息
- 调整目录结构（添加作者层级）
- 清理空目录

## 配置文件

配置文件 `manga.yaml` 包含以下主要部分：

### 基本配置

```yaml
debug: true                      # 是否为调试模式（true=不实际执行，false=正式执行）
manga-type:                      # 支持的漫画文件类型
  - .zip
  - .cbz
  - .pdf
```

### Tachiyomi配置

```yaml
tachiyomi:
  enable: true
  sources:                       # 源目录列表
    - /path/to/tachiyomi/downloads
  filters:                       # 漫画类型过滤器
    - name: tankobon
      type: tankobon
  mapping:                       # 移动规则映射
    - name: tankobon
      default: move
      dst: /path/to/destination
```

### 整理配置

```yaml
organize-manga:
  folders:                       # 需要整理的文件夹
    - /path/to/manga/folder

groups:                          # 需要移除的汉化组名
  - "[某汉化组]"

tags:                           # 需要后置的标签
  - key: 汉化
    alias: ["中文", "中字"]
```

### Komga配置

```yaml
komgalib:
  enable: true
  domain: http://localhost:25600
  cookies: "your_cookie_string"
  prefix-path: /actual/path
  lib-path: /komga/path/
  lib-names:                    # 要处理的库名
    - "Manga Library"
  Tier3: "★★★"                  # 三星标签
  Tier4: "★★★★"                 # 四星标签
  Tier5: "★★★★★"                # 五星标签
```

## 重构说明

此版本是完全重构后的2.0版本，主要改进：

### 架构改进
- 模块化设计：核心/模型/API/工具/服务分层
- 统一配置管理：Config类集中管理所有配置
- 标准日志系统：使用logging替代print
- 消除全局变量：通过Config对象传递状态

### 代码质量
- 消除代码重复：提取公共逻辑到服务层
- 职责清晰：每个模块职责单一明确
- 类型提示：添加类型注解提高可维护性
- 文档完善：详细的docstring和注释

### 易用性
- 更好的错误处理
- 清晰的日志输出
- 灵活的命令行参数
- 完善的帮助信息

## 旧版本文件

旧版本的文件已移动到 `backup/` 目录，包括：

- `run.py` -> `backup/old_run.py`
- `transfer_manga.py` -> `backup/old_transfer_manga.py`
- `organize_manga.py` -> `backup/old_organize_manga.py`
- `organize_komga.py` -> `backup/old_organize_komga.py`
- `komgaapi.py` -> `backup/old_komgaapi.py`
- `mangainfo.py` -> `backup/old_mangainfo.py`
- `utils.py` -> `backup/old_utils.py`

## 注意事项

1. 首次使用建议先用 `--debug` 调试模式运行
2. 确保配置文件中的路径正确
3. Komga功能需要有效的Cookie认证
4. 操作前建议备份重要数据

## 许可证

MIT License
