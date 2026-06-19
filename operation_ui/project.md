项目需求
1、

1 前端项目技术选型：

"axios": "^0.27.2",
"vue": "^3.5.4",
"vue-router": "^4.3.3",
element-ui plus
 "pinia": "^2.0.16",

工程目录设计：
src/
├──apis # api接口
├──assets # 资源
├──componets # 组件
├──config # 配置
├──views # 页面组件
├── store # 状态管理
├── utils # 工具函数
├── router # 路由配置

vite.config.ts

# 接口统一封装到apis

# 统一返回数据集处理