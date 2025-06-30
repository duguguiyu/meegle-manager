# Meegle Manager

基于 Meegle API 实现的项目管理工具，提供两层架构：SDK 层和业务层。

## 项目结构

```
meegle-manager/
├── meegle_sdk/              # SDK层 - 与业务无关的Meegle API封装
│   ├── __init__.py
│   ├── auth/                # 认证相关
│   │   ├── __init__.py
│   │   └── token_manager.py
│   ├── client/              # API客户端
│   │   ├── __init__.py
│   │   ├── base_client.py
│   │   └── meegle_client.py
│   ├── apis/                # 各种API封装
│   │   ├── __init__.py
│   │   ├── chart_api.py
│   │   ├── work_item_api.py
│   │   ├── team_api.py
│   │   └── user_api.py
│   └── models/              # 数据模型
│       ├── __init__.py
│       └── base_models.py
├── meegle_business/         # 业务层 - 具体业务逻辑
│   ├── __init__.py
│   ├── timeline/            # Timeline相关业务
│   │   ├── __init__.py
│   │   ├── extractor.py
│   │   └── models.py
│   └── export/              # 导出相关业务
│       ├── __init__.py
│       └── csv_exporter.py
├── examples/                # 使用示例
│   ├── sdk_examples.py
│   └── business_examples.py
├── tests/                   # 测试文件
│   ├── test_sdk/
│   └── test_business/
├── config/                  # 配置文件
│   └── settings.py
├── requirements.txt
└── setup.py
```

## 安装和使用

### 安装依赖
```bash
pip install -r requirements.txt
```

### SDK 层使用示例

```python
from meegle_sdk import MeegleSDK

# 初始化SDK
sdk = MeegleSDK(
    plugin_id="your_plugin_id",
    plugin_secret="your_plugin_secret",
    user_key="your_user_key"
)

# 获取Chart数据
chart_data = sdk.charts.get_chart_details("chart_id")

# 获取Work Items
work_items = sdk.work_items.get_projects()

# 获取用户信息
users = sdk.users.get_all_users()
```

### 业务层使用示例

```python
from meegle_business import TimelineExtractor, CSVExporter

# 提取Timeline数据
extractor = TimelineExtractor(sdk)
timeline_data = extractor.extract_date_range_timeline(chart_data, days_back=7)

# 导出CSV
exporter = CSVExporter()
exporter.export_timeline_to_csv(timeline_data, "timeline_export")
```

## 配置

在 `config/settings.py` 中配置你的 Meegle API 信息：

```python
MEEGLE_CONFIG = {
    "plugin_id": "your_plugin_id",
    "plugin_secret": "your_plugin_secret", 
    "user_key": "your_user_key",
    "base_url": "https://project.larksuite.com/open_api",
    "project_key": "your_project_key"
}
```

## 开发和测试

### 运行测试
```bash
python -m pytest tests/
```

### 运行示例
```bash
python examples/sdk_examples.py
python examples/business_examples.py
```
