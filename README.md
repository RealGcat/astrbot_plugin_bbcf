# BBCF招式查询插件

这是一个用于AstrBot的插件，可以查询BBCF(苍翼默示录：神观之梦)游戏角色招式数据并渲染为图片输出。

## 功能特性

- 从dustloop.com获取BBCF角色招式数据
- 将招式数据渲染为清晰的图片格式
- 支持多种招式属性查询（伤害、发生帧、帧优势等）
- **新增碰撞箱数据查询**（攻击箱、推箱、受击箱）
- 智能解析用户输入格式
- 多源数据获取（主页面、框架数据页面、碰撞箱专页）

## 使用方法

### 基本格式
```
查 角色名 招式指令
```

### 示例
```
查 es 5b
查 ragna 2a
查 jin 623c
```

### 支持的招式数据
- 招式名称
- 伤害值
- 防御类型
- 发生帧
- 持续帧
- 恢复帧
- 帧优势
- 取消属性
- 特殊属性
- **碰撞箱数据** (新增)
  - 攻击箱 (Hitbox)
  - 推箱 (Pushbox) 
  - 受击箱 (Hurtbox)

## 安装依赖

```bash
pip install -r requirements.txt
```

## 依赖项

- aiohttp >= 3.8.0 (HTTP客户端)
- beautifulsoup4 >= 4.11.0 (HTML解析)
- Pillow >= 9.0.0 (图片渲染)
- lxml >= 4.9.0 (XML/HTML解析器)

## 数据来源

本插件的数据来源于 [Dustloop Wiki](https://www.dustloop.com/w/BBCF)，这是一个权威的格斗游戏资料网站。

## 注意事项

- 确保网络连接正常，能够访问dustloop.com
- 角色名请使用英文缩写（如：es, ragna, jin等）
- 招式指令支持数字和字母组合（如：5b, 2a, 623c等）
- 如果找不到数据，请检查角色名和招式指令是否正确
- 碰撞箱数据可能不是所有招式都有，取决于dustloop.com的数据完整性
- 碰撞箱数值通常以游戏内单位表示，用于精确的招式分析

## 支持

[AstrBot开发文档](https://docs-v4.astrbot.app/dev/star/plugin.html)