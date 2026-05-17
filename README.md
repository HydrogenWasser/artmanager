# 美术资源管理工具 (Pixel Asset Manager)

一个面向像素游戏开发的轻量级美术资源管理工具，绑定真实文件系统，用于管理 Aseprite 文件、PNG、AI 原图、预览图、动画序列帧等美术素材。

## 特性

- 绑定真实文件系统，不复制素材
- 三栏布局：左侧逻辑资源树、中间资源网格、右侧属性面板
- 支持 PNG / JPG / WEBP / GIF / Aseprite 缩略图
- 深色主题 UI
- 标签、备注、搜索
- 集成 Aseprite 打开和 CLI 导出

## 安装

```bash
pip install -r requirements.txt
```

依赖：
- PySide6 >= 6.7.0
- Pillow >= 10.0.0
- watchdog >= 4.0.0
- send2trash >= 1.8.3

## 运行

```bash
python run.py
```

## 配置 Aseprite

1. 打开工具后，进入"设置"
2. 设置 Aseprite 可执行文件路径（例如 `C:/Program Files/Aseprite/Aseprite.exe`）
3. 设置缩略图尺寸（128 / 192 / 256）

## 第一版功能

- [x] 项目打开与 `.artmgr` 初始化
- [x] 左侧逻辑资源树（新建、重命名、删除节点）
- [x] 中间资源网格
- [x] 右侧属性面板
- [ ] 文件添加与管理
- [ ] 缩略图生成与缓存
- [ ] Aseprite 集成
- [ ] 搜索
- [ ] 设置对话框

## 已知限制

- 第一版暂不支持拖拽调整节点层级
- 第一版暂不支持 Godot 集成
- 第一版暂不支持云同步和多人协作
