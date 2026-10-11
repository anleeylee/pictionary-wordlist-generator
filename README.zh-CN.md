# Pictionary 词库生成器（Pictionary Wordlist Generator）

> **批量生成主题化 Pictionary 单词词库（JSON）——自动难度分级、类别平衡与合规过滤，专为派对游戏词表设计。**

[![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![CLI](https://img.shields.io/badge/CLI-ready-4B8BBE)](wordlist_generator.py)
[![No dependencies](https://img.shields.io/badge/deps-stdlib%20only-blueviolet)](requirements.txt)

---

## 相关链接

- 🎲 **在线工具体验：** [Pictionary Word Generator — 免费 7000+ 画画提示词](https://pictionarywordgenerators.com/)
- 英文版说明：[README.md](README.md)

---

## 这个工具做什么

主题化 Pictionary 词库是一个 JSON 文件，直接供派对游戏单词生成器读取。
每个词库把可画提示词按类别（动物、食物、地点、抽象概念……）和难度
（简单 / 中等 / 困难）组织好。

**本工具用一条命令，把小规模人工精选种子词扩展为完整、均衡、通过合规检查的词库**——
新增一个主题（太空、厨房、运动、节日……）只需几分钟，而不是手工维护上千行。

它的产出专为在线画画单词生成器设计，例如
[Pictionary Word Generator](https://pictionarywordgenerators.com/)——
那里的每个提示词都必须可画、适合家庭、并且类别分布均衡。

## 解决的痛点

手工维护词表又慢又不一致：

- 有人写 **200 条**，有人写 **2000 条**——难度分布漂移，玩家卡在生僻词上。
- 类别比例失衡：某个主题悄悄变成 80% "动物"，"全类别"模式玩起来很单调。
- 品牌名和不合适词汇混进家庭词库，事后要专门清扫（"跨 9 个库的品牌词清扫"
  正是这种返工——带合规过滤的生成器能在源头阻止它发生）。

## 特性

- **种子词 → 词库，一条命令**：用小型 JSON 种子文件（类别 → 提示词）定义主题，即可得到完整词库。
- **难度分级**（easy / medium / hard）：文档化启发式——短具体词与内置常用词集 → *简单*；普通短语 → *中等*；习语与长提示词 → *困难*。
- **类别平衡**：可配置的每类上限（默认 100），防止单一类别主导整场游戏。
- **合规过滤**：内置品牌词与敏感词黑名单（可扩展），保证词库家庭安全、不含第三方商标。
- **去重**：词库内大小写不敏感、空白归一化去重。
- **零第三方依赖**：纯 Python 标准库。
- **可复现输出**：每个词库自带 `generated_at` 时间戳、计数与警告，网站上的数字永远可审计。

## 安装

```bash
git clone https://github.com/anleeylee/pictionary-wordlist-generator.git
cd pictionary-wordlist-generator

# 无需 pip install —— 仅标准库
python wordlist_generator.py --help
```

## 用法

```bash
# 用内置种子文件生成太空词库
python wordlist_generator.py \
  --seed seeds/space.json \
  --out words/space.json
```

按主题调整平衡：

```bash
# 每类上限 40 条
python wordlist_generator.py --seed seeds/space.json --out words/space.json \
  --max-per-category 40
```

可选模板扩充（默认关闭——精选种子词保持高质量）：

```bash
python wordlist_generator.py --seed seeds/space.json --out words/space.json \
  --expand 20
```

### 种子文件格式

```json
{
  "theme": "space",
  "title": "Space",
  "categories": {
    "Nature": ["Moon", "Sun", "Star", "Comet"],
    "Objects": ["Rocket", "Satellite", "Telescope"]
  }
}
```

### 输出文件格式

```json
{
  "theme": "space",
  "title": "Space",
  "entries": [
    {"prompt": "Moon", "category": "Nature", "difficulty": "easy"},
    {"prompt": "Solar Eclipse", "category": "Nature", "difficulty": "medium"}
  ],
  "generated_at": "2026-10-12T05:10:00+00:00",
  "counts": {"easy": 40, "medium": 30, "hard": 30, "total": 100},
  "warnings": {"low_categories": {}, "filtered": 0}
}
```

## 分级规则

| 特征 | 等级 |
|---|---|
| 命中内置常用词集（cat、moon、pizza……） | easy |
| 单词 ≤ 6 字符 | easy |
| 普通短语（无习语标记） | medium |
| 习语标记（cognitive、existential、butterfly effect……） | hard |
| 超过 22 字符 / 5 个以上单词 | hard |

分级是启发式而非保证——种子词作者始终是最终编辑。
工具**不会**为了填满类别而凭空造词：类别低于下限时会在 `warnings` 中报告，
而不是静默补齐。

## 为什么不直接用一份超大静态列表？

因为词库是网站单词计数的*唯一事实来源*，而发布计数是要被审计的。
当每个词库都带有可复现的生成路径、变更日志与 JSON 结构时，
"7,958 条词条"、"6,964 条去重提示词"、"24 个词库"这类数字就变成可核验的事实，
而不是营销话术。这个工具存在的意义就是让这条流水线可重复。

## 测试

```bash
python -m unittest discover -s tests -v
```

覆盖：难度分级、品牌/敏感词过滤、去重、类别平衡、端到端 CLI JSON 输出。

## 许可

MIT——可自由使用与扩展，请保留署名。生成的词库属于你的内容，工具只是让它可复现。
