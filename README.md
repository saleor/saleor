![Dastkari Commerce - A GraphQL-first platform for perfectionists](https://user-images.githubusercontent.com/249912/71523206-4e45f800-28c8-11ea-84ba-345a9bfc998a.png)

<div align="center">
  <h1>Dastkari Commerce</h1>
</div>

<div align="center">
  <strong>Customer-centric e-commerce on a modern stack</strong>
</div>

<div align="center">
  A headless, GraphQL-first e-commerce platform delivering ultra-fast, dynamic, personalized shopping experiences. Beautiful online stores, anywhere, on any device.
</div>

<br>

<div align="center">
  Join our active, engaged community: <br>
  <a href="https://dastkari.io/">Website</a>
  <span> | </span>
  <a href="https://medium.com/dastkari">Blog</a>
  <span> | </span>
  <a href="https://twitter.com/getdastkari">Twitter</a>
  <span> | </span>
  <a href="https://gitter.im/mirumee/dastkari">Gitter</a>
  <span> | </span>
  <a href="https://spectrum.chat/dastkari">Spectrum</a>
</div>

<br>

<div align="center">
  <a href="https://circleci.com/gh/mirumee/dastkari">
    <img src="https://circleci.com/gh/mirumee/dastkari.svg?style=svg" alt="Build status" />
  </a>
  <a href="http://codecov.io/github/mirumee/dastkari?branch=master">
    <img src="http://codecov.io/github/mirumee/dastkari/coverage.svg?branch=master" alt="Codecov" />
  </a>
  <a href="https://docs.dastkari.io/">
    <img src="https://img.shields.io/badge/docs-docs.dastkari.io-brightgreen.svg" alt="Documentation" />
  </a>
  <a href="https://github.com/python/black">
    <img src="https://img.shields.io/badge/code%20style-black-000000.svg" alt="Code style: black">
  </a>
</div>

## Table of Contents

- [What makes Dastkari special?](#what-makes-dastkari-special)
- [Features](#features)
- [Installation](#installation)
- [Documentation](#documentation)
- [Demo](#demo)
- [Contributing](#contributing)
- [Translations](#translations)
- [Your feedback](#your-feedback)
- [License](#license)

## What makes Dastkari special?

Dastkari is a rapidly-growing open source e-commerce platform that has served high-volume companies from branches like publishing and apparel since 2012. Based on Python and Django, the latest major update introduces a modular front end powered by a GraphQL API and written with React and TypeScript.

## Features

- **PWA**: End users can shop offline for better sales and shopping experiences
- **GraphQL API**: Access all data from any web or mobile client using the latest technology
- **Headless commerce**: Build mobile apps, customize storefronts and externalize processes
- **UX and UI**: Designed for a user experience that rivals even the top commercial platforms
- **Dashboard**: Administrators have total control of users, processes, and products
- **Orders**: A comprehensive system for orders, dispatch, and refunds
- **Cart**: Advanced payment and tax options, with full control over discounts and promotions
- **Payments**: Flexible API architecture allows integration of any payment method. It comes with Braintree support out of the box.
- **Geo-adaptive**: Automatic localized pricing. Over 20 local languages. Localized checkout experience by country.
- **SEO**: Packed with features that get stores to a wider audience
- **Cloud**: Optimized for deployments using Docker
- **Analytics**: Server-side Google Analytics to report e-commerce metrics without affecting privacy

Dastkari is free and always will be.
Help us out… If you love free stuff and great software, give us a star! 🌟

![Dastkari Storefront - React-based PWA e-commerce storefront](https://user-images.githubusercontent.com/249912/71527146-5b6be280-28da-11ea-901d-eb76161a6bfb.png)
![Dastkari Dashboard - Modern UI for managing your e-commerce](https://user-images.githubusercontent.com/249912/71523261-8a795880-28c8-11ea-98c0-6281ea37f412.png)

## Installation

Dastkari requires Python 3.8, Node.js 10.0+, PostgreSQL and OS-specific dependency tools.

[See the Dastkari docs](https://docs.dastkari.io/docs/getting-started/intro/) for step-by-step installation and deployment instructions.

Note:
The `master` branch is the development version of Dastkari and it may be unstable. To use the latest stable version, download it from the [Releases](https://github.com/mirumee/dastkari/releases/) page or switch to a release tag.

The current stable version is 2.10 and you should use this version for all three components:

- Dastkari: https://github.com/mirumee/dastkari/releases/tag/2.10.2
- Dashboard: https://github.com/mirumee/dastkari-dashboard/releases/tag/2.10.0
- Storefront: https://github.com/mirumee/dastkari-storefront/releases/tag/2.10.0

## Documentation

Dastkari documentation is available here: [docs.dastkari.io](https://docs.dastkari.io)

To contribute, please see the [`mirumee/dastkari-docs` repository](https://github.com/mirumee/dastkari-docs/).

## Dastkari Platform

The easiest way to run all components of Dastkari (API, storefront and dashboard) together on your local machine is to use the [dastkari-platform](https://github.com/mirumee/dastkari-platform) project. Go to that repository for instructions on how to use it.

[View dastkari-platform](https://github.com/mirumee/dastkari-platform)

## Storefront

For PWA, single-page storefront go to the [dastkari-storefront](https://github.com/mirumee/dastkari-storefront) repository.

[View storefront demo](https://pwa.dastkari.io/)

## Dashboard

For dashboard go to the [dastkari-dashboard](https://github.com/mirumee/dastkari-dashboard) repository.

[View dashboard demo](https://pwa.dastkari.io/dashboard/)

## Demo

Want to see Dastkari in action?

[View Storefront](https://pwa.dastkari.io/) | [View Dashboard (admin area)](https://pwa.dastkari.io/dashboard/)

Or launch the demo on a free Heroku instance.

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)

Login credentials: `admin@example.com`/`admin`

## Contributing

We love your contributions and do our best to provide you with mentorship and support. If you are looking for an issue to tackle, take a look at issues labeled [`Help Wanted`](https://github.com/mirumee/dastkari/issues?q=is%3Aopen+is%3Aissue+label%3A%22help+wanted%22).

If nothing grabs your attention, check [our roadmap](https://github.com/mirumee/dastkari/projects/6) or come up with your feature. Just drop us a line or [open an issue](https://github.com/mirumee/dastkari/issues/new) and we’ll work out how to handle it.

Get more details in our [Contributing Guide](https://docs.getdastkari.com/docs/contributing/intro/).

## Legacy views

If you're interested in using the old version of Dastkari, go the [legacy-views](https://github.com/mirumee/legacy-views) repository. It contains the 2.9.0 release, which includes Django-based views and HTML templates of Storefront 1.0 and Dashboard 1.0. Note: this version of Dastkari is no longer officially maintained.

## Your feedback

Do you use Dastkari as an e-commerce platform?
Fill out this short survey and help us grow. It will take just a minute, but mean a lot!

[Take a survey](https://mirumee.typeform.com/to/sOIJbJ)

## License

Disclaimer: Everything you see here is open and free to use as long as you comply with the [license](https://github.com/mirumee/dastkari/blob/master/LICENSE). There are no hidden charges. We promise to do our best to fix bugs and improve the code.

Some situations do call for extra code; we can cover exotic use cases or build you a custom e-commerce appliance.

#### Crafted with ❤️ by [Mirumee Software](http://mirumee.com)

hello@mirumee.com
