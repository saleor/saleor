<div align="center" width="100px">

 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://github.com/user-attachments/assets/76e3079f-696a-4fcd-8658-89739647090b">
   <source media="(prefers-color-scheme: light)" srcset="https://github.com/user-attachments/assets/8477d643-a905-4c63-8ed3-03d0976f6fc3">
   <img width="200" alt="saleor-commerce-logo" src="https://user-images.githubusercontent.com/4006792/214636328-8e4f83e8-66cb-4114-a3d8-473eb908b9c3.png">

 </picture>
</div>

<div align="center">
  <strong>Commerce that works with your language and stack</strong>
</div>

<div align="center">
  GraphQL native, API-only platform for scalable composable commerce.
</div>

<br>

<div align="center">
 Get to know Saleor: <br>
  <a href="https://saleor.typeform.com/talk-with-us?utm_source=github&utm_medium=readme&utm_campaign=repo_saleor">Talk to a human</a>
  <span> | </span>
  <a href="https://cloud.saleor.io/signup?utm_source=github&utm_medium=readme&utm_campaign=repo_saleor">Talk to the API</a>
</div>

<br>

<div align="center">
  Join our community: <br>
  <a href="https://saleor.io/">Website</a>
  <span> | </span>
  <a href="https://twitter.com/getsaleor">Twitter</a>
  <span> | </span>
  <a href="https://saleor.io/discord">Discord</a>
</div>

<div align="center">
   <a href="https://saleor.io/blog">Blog</a>
  <span> | </span>
  <a href="https://saleor.typeform.com/to/JTJK0Nou">Subscribe to newsletter</a>
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

## Table of Contents

- [What makes Saleor special?](#what-makes-saleor-special)
- [Why API-only Architecture?](#why-api-only-architecture)
- [Features](#features)
- [Installation](#installation)
- [Documentation](#documentation)
- [Saleor Platform](#saleor-platform)
- [Storefront](#storefront)
- [Dashboard](#dashboard)
- [Contributing](#contributing)
- [License](#license)

## What makes Saleor special?

- **Technology-agnostic** - no monolithic plugin architecture or technology lock-in.

- **GraphQL only** - Not afterthought API design or fragmentation across different styles of API.

- **Headless and API only** - APIs are the only way to interact, configure, or extend the backend.

- **Open source** -  a single version of Saleor without feature fragmentation or commercial limitations.

- **Cloud native** - battle tested on global brands.

- **Native-multichannel** - Per [channel](https://docs.saleor.io/developer/channels/overview) control of pricing, currencies, stock, product, and more.

## Why API-only Architecture?

Saleor's API-first extensibility provides powerful tools for developers to extend backend using [webhooks](https://docs.saleor.io/developer/extending/webhooks/overview), attributes, [metadata](https://docs.saleor.io/api-usage/metadata), [apps](https://docs.saleor.io/developer/extending/apps/overview), [subscription queries](https://docs.saleor.io/developer/extending/webhooks/subscription-webhook-payloads), [API extensions](https://docs.saleor.io/developer/extending/webhooks/synchronous-events/overview), [dashboard iframes](https://docs.saleor.io/developer/extending/apps/overview).

Compared to traditional plugin architectures (monoliths) it provides the following benefits:

- There is less downtime as apps are deployed independently.
- Reliability and performance - custom logic is separated from the core.
- Simplified upgrade paths - eliminates incompatibility conflicts between extensions.
- Technology-agnostic - works with any technology, stack, or language.
- Parallel development - easier to collaborate than with a monolithic core.
- Simplified debugging - easier to narrow down bugs in independent services.
- Scalability - extensions and apps can be scaled independently.

### What are the tradeoffs?

If you are a single developer working with a small business that doesn't have high traffic or a critical need for 24/7 availability, using a service-oriented approach might feel more complex compared to the traditional WordPress or Magento approach that provides a language-specific framework, runtime, database schema, aspect-oriented programming, and other tools to a quick start.

However, if you deploy on a daily basis, reliability and uptime is critical,
you need to collaborate with other developers, or you have non-trivial requirements you might be in the right place.

## Features

- **Enterprise ready**: Secure, scalable, and stable. Battle-tested by big brands
- **Dashboard**: User-friendly, fast, and productive. (Decoupled project [repo](https://github.com/saleor/saleor-dashboard) )
- **Global by design** Multi-currency, multi-language, multi-warehouse, tutti multi!
- **CMS**: Manage product or marketing content.
- **Product management**: A rich content model for large and complex catalogs.
- **Orders**: Flexible order model, split payments, multi-warehouse, returns, and more.
- **Customers**: Order history and preferences.
- **Promotion engine**: Sales, vouchers, cart rules, giftcards.
- **Payment orchestration**: multi-gateway, extensible payment API, flexible flows.
- **Cart**: Advanced payment and tax options, with full control over discounts and promotions.
- **Payments**: Flexible API architecture allows integration of any payment method.
- **Translations**: Fully translatable catalog.
- **SEO**: Unlimited SEO freedom with headless architecture.
- **Apps**: Extend dashboard via iframe with any web stack.

![Saleor Dashboard - Modern UI for managing your e-commerce](https://user-images.githubusercontent.com/9268745/224249510-d3c7658e-6d5c-42c5-b4fb-93eaf65a5335.png)

## Installation

[See the Saleor docs](https://docs.saleor.io/setup/docker-compose) for step-by-step installation and deployment instructions. For local development without Docker, follow our [Contributing Guide](./CONTRIBUTING.md).

Note:
The `main` branch is the development version of Saleor and it may be unstable. To use the latest stable version, download it from the [Releases](https://github.com/saleor/saleor/releases/) page or switch to a release tag.

The current production-ready version is 3.x and you should use this version for all three components:

- Saleor: <https://github.com/saleor/saleor/releases/>
- Dashboard: <https://github.com/saleor/saleor-dashboard/releases/>
- Storefront: <https://github.com/saleor/react-storefront/releases/>

### Saleor Cloud

The fastest way to develop with Saleor is by using developer accounts in [Saleor Cloud](https://cloud.saleor.io).

Register [here](https://cloud.saleor.io/register) or install our [CLI tool](https://github.com/saleor/saleor-cli):

`npm i -g @saleor/cli`

and run the following command:

`saleor register`

Bootstrap your first [storefront](https://github.com/saleor/react-storefront) with:

`saleor storefront create --url {your-saleor-graphql-endpoint}`

## Documentation

Saleor documentation is available here: [docs.saleor.io](https://docs.saleor.io)

To contribute, please see the [`saleor/saleor-docs` repository](https://github.com/saleor/saleor-docs/).

## Saleor Platform

The easiest way to run all components of Saleor (API, storefront, and dashboard) together on your local machine is to use the [saleor-platform](https://github.com/saleor/saleor-platform) project. Go to that repository for instructions on how to use it.

[View saleor-platform](https://github.com/saleor/saleor-platform)

## Storefront

An open-source storefront example built with Next.js App Router, React.js, TypeScript, GraphQL, and Tailwind CSS.

[React Storefront Repository](https://github.com/saleor/storefront)

[View Storefront Example](https://storefront.saleor.io/)

## Dashboard

For the dashboard, go to the [saleor-dashboard](https://github.com/saleor/saleor-dashboard) repository.

## Contributing

We love your contributions and do our best to provide you with mentorship and support. If you are looking for an issue to tackle, take a look at issues labeled [`Good first issue`](https://github.com/saleor/saleor/issues?q=is%3Aopen+is%3Aissue+label%3A%22good+first+issue%22+) and [`Help wanted`](https://github.com/saleor/saleor/issues?q=is%3Aopen+is%3Aissue+label%3A%22help+wanted%22).

If nothing grabs your attention, check [our roadmap](https://saleor.io/roadmap) or [start a Discord discussion](https://saleor.io/discord) about a feature you'd like to see. Make sure to read our [Contribution Guidelines](http://docs.saleor.io/developer/community/contributing) before opening a PR or issue.

Get more details (e.g., how to run Saleor on your local machine) in our [Contributing Guide](./CONTRIBUTING.md).

## License

Disclaimer: Everything you see here is open and free to use as long as you comply with the [license](https://github.com/saleor/saleor/blob/master/LICENSE). There are no hidden charges. We promise to do our best to fix bugs and improve the code.

#### Crafted with ❤️ by [Saleor Commerce](https://saleor.io)

<hello@saleor.io>
