<div align="center" width="100px">

 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://github.com/user-attachments/assets/76e3079f-696a-4fcd-8658-89739647090b">
   <source media="(prefers-color-scheme: light)" srcset="https://github.com/user-attachments/assets/8477d643-a905-4c63-8ed3-03d0976f6fc3">
   <img width="200" alt="saleor-commerce-logo" src="https://user-images.githubusercontent.com/4006792/214636328-8e4f83e8-66cb-4114-a3d8-473eb908b9c3.png">

 </picture>
</div>

<div align="center">
  <strong>适用于您的语言和技术栈的商务解决方案</strong>
</div>

<div align="center">
  GraphQL 原生、纯 API 平台，用于可扩展的组合式商务。
</div>

<br>

<div align="center">
  加入我们的社区: <br>
  <a href="https://saleor.io/">网站</a>
  <span> | </span>
  <a href="https://twitter.com/getsaleor">Twitter</a>
  <span> | </span>
  <a href="https://saleor.io/discord">Discord</a>
</div>

<div align="center">
   <a href="https://saleor.io/blog">博客</a>
  <span> | </span>
  <a href="https://saleor.typeform.com/to/JTJK0Nou">订阅新闻通讯</a>
</div>

<br>

<div align="center">

[![Discord Badge](https://dcbadge.vercel.app/api/server/unUfh24R6d)](https://saleor.io/discord)

</div>

<div align="center">
  <a href="https://codecov.io/gh/saleor/saleor" >
    <img src="https://codecov.io/gh/saleor/saleor/graph/badge.svg?token=qkNcTJ4TmI" alt="Coverage"/>
  </a>
  <a href="https://docs.saleor.io/">
    <img src="https://img.shields.io/badge/docs-docs.saleor.io-brightgreen.svg" alt="Documentation" />
  </a>
  <a href="https://github.com/astral-sh/ruff">
    <img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json" alt="Linted by Ruff">
  </a>
</div>

## 目录

- [Saleor 有何特别之处?](#saleor-有何特别之处)
- [为何选择纯 API 架构?](#为何选择纯-api-架构)
- [功能特性](#功能特性)
- [安装指南](#安装指南)
- [文档](#文档)
- [Saleor 平台](#saleor-平台)
- [店面 (Storefront)](#店面-storefront)
- [仪表盘 (Dashboard)](#仪表盘-dashboard)
- [如何贡献](#如何贡献)
- [许可证](#许可证)

## Saleor 有何特别之处?

- **技术无关** - 没有单体插件架构或技术锁定。
- **纯 GraphQL** - 没有事后设计的 API 或跨不同 API 风格的碎片化。
- **无头和纯 API** - API 是交互、配置或扩展后端的唯一方式。
- **开源** - Saleor 的单一版本，没有功能碎片化或商业限制。
- **云原生** - 经过全球品牌的实战检验。
- **原生多渠道** - 通过 [渠道](https://docs.saleor.io/developer/channels/overview) 控制定价、货币、库存、产品等。

## 为何选择纯 API 架构?

Saleor 的 API 优先的可扩展性为开发人员提供了强大的工具，以使用 [webhooks](https://docs.saleor.io/developer/extending/webhooks/overview)、属性、[元数据](https://docs.saleor.io/api-usage/metadata)、[应用程序](https://docs.saleor.io/developer/extending/apps/overview)、[订阅查询](https://docs.saleor.io/developer/extending/webhooks/subscription-webhook-payloads)、[API 扩展](https://docs.saleor.io/developer/extending/webhooks/synchronous-events/overview)、[仪表盘 iframes](https://docs.saleor.io/developer/extending/apps/overview) 来扩展后端。

与传统的插件架构（单体）相比，它具有以下优势：

- **减少停机时间**：由于应用程序是独立部署的，因此停机时间更少。
- **可靠性和性能**：自定义逻辑与核心分离。
- **简化的升级路径**：消除了扩展之间的不兼容冲突。
- **技术无关**：适用于任何技术、堆栈或语言。
- **并行开发**：比单体核心更容易协作。
- **简化的调试**：更容易在独立的服务中缩小错误范围。
- **可伸缩性**：扩展和应用程序可以独立伸缩。

### 有哪些权衡?

如果您是为一家没有高流量或对 24/7 可用性没有关键需求的小型企业工作的单一开发人员，那么与传统的 WordPress 或 Magento 方法相比，使用面向服务的方法可能会感觉更复杂，后者提供了特定于语言的框架、运行时、数据库模式、面向方面的编程以及其他快速入门的工具。

但是，如果您每天都进行部署，可靠性和正常运行时间至关重要，您需要与其他开发人员协作，或者您有非同寻常的需求，那么您可能来对地方了。

## 功能特性

- **企业级就绪**: 安全、可扩展、稳定。经过大品牌的实战检验。
- **仪表盘**: 用户友好、快速、高效。(解耦的项目 [仓库](https://github.com/saleor/saleor-dashboard))
- **全球化设计**: 多货币、多语言、多仓库，应有尽有！
- **内容管理系统 (CMS)**: 管理产品或营销内容。
- **产品管理**: 丰富的内内容模型，适用于大型复杂目录。
- **订单**: 灵活的订单模型、拆分支付、多仓库、退货等。
- **客户**: 订单历史和偏好设置。
- **促销引擎**: 销售、优惠券、购物车规则、礼品卡。
- **支付编排**: 多网关、可扩展的支付 API、灵活的流程。
- **购物车**: 先进的支付和税务选项，完全控制折扣和促销。
- **支付**: 灵活的 API 架构允许集成任何支付方式。
- **翻译**: 完全可翻译的目录。
- **搜索引擎优化 (SEO)**: 无头架构带来无限的 SEO 自由度。
- **应用**: 通过 iframe 使用任何 Web 技术栈扩展仪表盘。

![Saleor 仪表盘 - 用于管理电子商务的现代用户界面](https://user-images.githubusercontent.com/9268745/224249510-d3c7658e-6d5c-42c5-b4fb-93eaf65a5335.png)

## 安装指南

请参阅 [Saleor 文档](https://docs.saleor.io/setup/docker-compose) 获取分步安装和部署说明。对于没有 Docker 的本地开发，请遵循我们的 [贡献指南](./CONTRIBUTING.md)。

**注意**:
`main` 分支是 Saleor 的开发版本，可能不稳定。要使用最新的稳定版本，请从 [发布](https://github.com/saleor/saleor/releases/) 页面下载或切换到发布标签。

当前的生产就绪版本是 3.x，您应该为所有三个组件使用此版本：

- Saleor: <https://github.com/saleor/saleor/releases/>
- 仪表盘: <https://github.com/saleor/saleor-dashboard/releases/>
- 店面: <https://github.com/saleor/react-storefront/releases/>

### Saleor Cloud

使用 Saleor 进行开发的最快方法是使用 [Saleor Cloud](https://cloud.saleor.io) 中的开发者帐户。

在此处 [注册](https://cloud.saleor.io/register) 或安装我们的 [CLI 工具](https://github.com/saleor/saleor-cli)：

`npm i -g @saleor/cli`

并运行以下命令：

`saleor register`

使用以下命令引导您的第一个 [店面](https://github.com/saleor/react-storefront)：

`saleor storefront create --url {您的-saleor-graphql-端点}`

## 文档

Saleor 文档可在此处获得: [docs.saleor.io](https://docs.saleor.io)

要做出贡献，请参阅 [`saleor/saleor-docs` 仓库](https://github.com/saleor/saleor-docs/)。

## Saleor 平台

在本地计算机上一起运行 Saleor 的所有组件（API、店面和仪表盘）的最简单方法是使用 [saleor-platform](https://github.com/saleor/saleor-platform) 项目。有关如何使用它的说明，请转到该仓库。

[查看 saleor-platform](https://github.com/saleor/saleor-platform)

## 店面 (Storefront)

一个开源的店面示例，使用 Next.js App Router、React.js、TypeScript、GraphQL 和 Tailwind CSS 构建。

[React Storefront 仓库](https://github.com/saleor/storefront)

[查看店面示例](https://storefront.saleor.io/)

## 仪表盘 (Dashboard)

对于仪表盘，请转到 [saleor-dashboard](https://github.com/saleor/saleor-dashboard) 仓库。

## 如何贡献

我们欢迎您的贡献，并尽力为您提供指导和支持。如果您正在寻找要解决的问题，请查看标记为 [`适合初学者`](https://github.com/saleor/saleor/issues?q=is%3Aopen+is%3Aissue+label%3A%22good+first+issue%22+) 和 [`需要帮助`](https://github.com/saleor/saleor/issues?q=is%3Aopen+is%3Aissue+label%3A%22help+wanted%22) 的问题。

如果没有什么吸引您的注意力，请查看 [我们的路线图](https://saleor.io/roadmap) 或就您希望看到的功能 [在 Discord 上发起讨论](https://saleor.io/discord)。在开启 PR 或问题之前，请务必阅读我们的 [贡献指南](http://docs.saleor.io/developer/community/contributing)。

在我们的 [贡献指南](./CONTRIBUTING.md) 中获取更多详细信息（例如，如何在本地计算机上运行 Saleor）。

## 许可证

免责声明：只要您遵守 [许可证](https://github.com/saleor/saleor/blob/master/LICENSE)，您在此处看到的所有内容都是开放和免费使用的。没有任何隐藏费用。我们承诺将尽最大努力修复错误并改进代码。

#### 由 [Saleor Commerce](https://saleor.io) 精心打造 ❤️

<hello@saleor.io>
