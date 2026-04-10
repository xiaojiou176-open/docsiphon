# Docsiphon Design System

## Purpose

这份 `MASTER` 不是要把 GitHub README 幻想成可随意写 CSS 的 landing page。
它是这个仓的**前门排版合同**，负责锁定：

- 首屏顺序
- 证据梯子
- 边界文案
- 资产分工

## Tone

- `CLI-first`
- `proof-first`
- `developer editorial`
- `quiet confidence`

说得更直白一点：

> 它应该像一个会做事的开发者工具前厅，
> 不是营销页，也不是客服 FAQ。

## Color Direction

- 正文基底：浅底
- 正文字色：深 slate
- 强调色：绿色只给 success / CTA
- 深色面板：只给 code / proof / evidence 区块

### Preferred tokens

| Token | Value | Use |
| --- | --- | --- |
| `ink-strong` | `#1E293B` | 正文主标题与正文文本 |
| `ink-muted` | `#334155` | 次级说明 |
| `success-accent` | `#22C55E` | success chip / CTA |
| `surface-soft` | `#F8FAFC` | 浅色信息区块 |
| `proof-band` | `#0F172A` | code / proof / evidence 深色带 |

## Type Rules

- 正文短段落，优先 2 到 4 行一段
- 命令块前必须先有一句人话解释
- monospace 只留给命令、artifact 名称、状态词
- 不要连续堆 3 段免责声明

## Proof Ladder

| Level | Asset | It proves |
| --- | --- | --- |
| `L1` | hero | 这工具到底是什么 |
| `L2` | before/after | 为什么比 naive crawling 更值得用 |
| `L3` | demo / artifact list | 跑完以后你会得到什么 |

### Rule

一张图只证明一件事。

## Front-Door Structure

README 第一屏固定按这个顺序排：

1. 一句话价值主张
2. 单条 first-success 命令
3. 成功信号
4. proof ladder 入口
5. 再讲更长的 Why / Best Fit / Not For

## Boundary Card

首屏边界文案尽量压成一张短卡片，而不是散成多段重复说明。

必须同时讲清：

- best fit
- not for
- current product boundary

## Companion Docs Rules

- `docs/index.md`：路由 + 值得点进去的理由
- `docs/repo-map.md`：东西都放在哪里
- 不复制整套 README

## Anti-Patterns

- 文字墙先于命令
- GIF 抢走第一证明角色
- playful 色块过多
- 重复边界声明
- companion docs 长成第二套 README
