import React from "react";
import { ScrollLink } from "..";
import { GitHubBanner } from "..";
import { Helmet } from "react-helmet";
import ReactSVG from "react-svg";

import css from "./feature.css";

import graphQLIcon from "../../images/graphQL.svg";
import internationalizationIcon from "../../images/internationalization.svg";
import progressiveWebAppIcon from "../../images/progressive-web-apps.svg";
import lovesEnginesIcon from "../../images/loved-engines.svg";

import productVariant from "../../images/products-variants.svg";
import collectionsIcon from "../../images/collections.svg";
import multipleImages from "../../images/multiple-images.svg";
import seoIcon from "../../images/seo.svg";
import nonShippableIcon from "../../images/non-shippable.svg";
import multiCareerShipping from "../../images/multi-career-shipping.svg";
import multipleDispatch from "../../images/multiple-dispatch.svg";
import refunds from "../../images/refunds.svg";
import fulfillment from "../../images/fulfillment.svg";
import customerProfiles from "../../images/customer-profiles.svg";
import paymentIntegration from "../../images/payments-integration.svg";
import automaticTaxes from "../../images/automatic-taxes.svg";
import paymentRequests from "../../images/payment-requests.svg";
import discountAndPromotions from "../../images/discount-and-promotions.svg";
import search from "../../images/search.svg";
import staffManagement from "../../images/staff-management.svg";
import gdprReady from "../../images/gdpr-ready.svg";
import analytics from "../../images/analytics.svg";

const Feature = () => (
  <div>
    <div id="feature" className="container">
      <Helmet>
        <title>
          Features | Saleor - A GraphQL-first Open Source eCommerce Platform
        </title>
        <meta
          name="description"
          content="Headless commerce with GraphQL. Take advantage of the robust API, customize your storefront, easily prepare for GDPR, and enjoy a host of other features."
        />
      </Helmet>
      <section className="hero">
        <div className="feature bg-container" />
        <div className="plane">
          <h1 className="title">
            <span className="primaryColor">Agile e-commerce</span> unafraid of
            developing business&nbsp;needs.
          </h1>
        </div>
        <ScrollLink to="#testimonial"> Learn more </ScrollLink>
      </section>
      <section id="testimonial" className="testimonial">
        <div className="container">
          <div className="patchgarden-logo">
            <ReactSVG
              className="logo-svg"
              path="../../images/patch-garden.svg"
            />
            <span>Patch Garden</span>
          </div>
          <p className="comment quote text-light">
            “After actively using and developing our Saleor store for over a
            year, if I were to create a new shop today I would go for it again
            without a&nbsp;doubt.”
          </p>
          <div className="testimonial-author">
            <h5 className="name">Tyler Hildebrandt,</h5>
            <h5 className="position">Lead developer. Patch Garden</h5>
          </div>
        </div>
      </section>
      <section className="features section-container">
        <div className="grid icons">
          <div className="icon-card">
            <ReactSVG className="loved-by-search" path={lovesEnginesIcon} />
            <h3 className="title">
              Loved by search
              <br /> engines
            </h3>
            <p>
              Saleor is packed with everything you need, from sitemaps and
              schema.org structured data to Open Graph that kick-starts your
              ecommerce SEO. Integrate with Google Merchant Center and present
              your products to a wider&nbsp;audience.
            </p>
          </div>
          <div className="icon-card">
            <ReactSVG className="graphql" path={graphQLIcon} />
            <h3 className="title">
              Headless commerce
              <br /> with GraphQL
            </h3>
            <p>
              Take advantage of the robust API that gives you access to any
              third-party integrations you want. Build a mobile app, customize
              your storefront or externalize processes such as inventory
              management, order processing, fulfillment and&nbsp;more
            </p>
          </div>
          <div className="icon-card">
            <ReactSVG className="pwa" path={progressiveWebAppIcon} />
            <span className="decorator" />
            <h3 className="title">
              Progressive Web
              <br /> Apps
            </h3>
            <p>
              Earn a place on users home screens and let them comfortably browse
              even on a slow internet connection or no connection at all.
              Google&nbsp;Page&nbsp;Speed optimization keeps Page Load times low
              and can result in doubling your&nbsp;conversions.
            </p>
          </div>
          <div className="icon-card">
            <ReactSVG
              className="localization"
              path={internationalizationIcon}
            />
            <h3 className="title">
              Internationalization & <br /> Localization
            </h3>
            <p>
              Make your shop multilanguage by default. Show prices in local
              currencies using GeoIP, and adjust addresses and formats to the
              chosen region. Our community has also provided translations for
              more than 20 languages with coverage ranging up to&nbsp;98%.
            </p>
          </div>
        </div>
      </section>
      <section className="product-management management-section grid">
        <div className="side-header col-lg-4 col-md-6 col-sm-12 col-xs-12">
          <h2>
            Product <br /> Management
          </h2>
          <p className="sub-description">
            Product offer attractiveness is a combination of factors like price,
            exposure, and variety. Take charge and drive&nbsp;sales.
          </p>
        </div>
        <div className="card-grid col-lg-8 col-md-6 col-sm-12 col-xs-12">
          <div className="icon-card">
            <ReactSVG path={productVariant} />
            <h5 className="title">Products & Variants</h5>
            <p>
              Use attributes like color and size to create unlimited product
              variants. Enable your customers to use faceted search to find
              relevant&nbsp;products.
            </p>
          </div>
          <div className="icon-card">
            <ReactSVG path={collectionsIcon} />
            <h5 className="title">Collections</h5>
            <p>
              Assign products to groups to allow customers to shop by look,
              theme or purpose. Combine collections with vouchers and discounts
              to create seasonal&nbsp;promotions.
            </p>
          </div>
          <div className="icon-card">
            <ReactSVG path={multipleImages} />
            <h5 className="title">Multiple Images</h5>
            <p>
              Add unlimited images to your products and have Saleor
              automatically generate thumbnails in all relevant dimensions to
              satisfy both desktop and mobile&nbsp;users.
            </p>
          </div>
          <div className="icon-card">
            <ReactSVG path={seoIcon} />
            <h5 className="title">SEO</h5>
            <p>
              Edit individual product metadata and override fields like name and
              description to improve your visibility in search engine results
              and on social&nbsp;media.
            </p>
          </div>
          <div className="icon-card">
            <ReactSVG path={nonShippableIcon} />
            <h5 className="title">Non-shippable products</h5>
            <p>
              Sell products like digital goods and services, and have the
              storefront automatically skip the shipping method and address
              during&nbsp;checkout.
            </p>
          </div>
        </div>
      </section>
      <section className="product-management management-section grid">
        <div className="side-header col-lg-4 col-md-6 col-sm-12 col-xs-12">
          <h2>
            Order <br /> Management
          </h2>
          <p className="sub-description">
            Saleor gives you full control over orders, from the checkout and
            customer management through product&nbsp;delivery.
          </p>
        </div>
        <div className="card-grid col-lg-8 col-md-6 col-sm-12 col-xs-12">
          <div className="icon-card">
            <ReactSVG path={multiCareerShipping} />
            <h5 className="title">Multi-carrier shipping</h5>
            <p>
              Let buyers choose between multiple carriers and delivery methods.
              Set availability and rates separately for
              different&nbsp;countries.
            </p>
          </div>
          <div className="icon-card">
            <ReactSVG path={multipleDispatch} />
            <h5 className="title">Multiple dispatch</h5>
            <p>
              Need to ship certain items separately or on a different date?
              Deliver a single order using multiple fulfillments, even if it
              means splitting the quantity of a specific&nbsp;product.
            </p>
          </div>
          <div className="icon-card">
            <ReactSVG path={refunds} />
            <h5 className="title">Refunds</h5>
            <p>
              If anything goes wrong or a product needs to be returned,
              reimburse your customers using the intuitive refund&nbsp;screen.
            </p>
          </div>
          <div className="icon-card">
            <ReactSVG path={fulfillment} />
            <h5 className="title">Fulfillment</h5>
            <p>
              Remain in control throughout the entire lifecycle of your orders.
              Use custom search and filtering, leave comments for other staff
              members and check the detailed history of every&nbsp;order.
            </p>
          </div>
          <div className="icon-card">
            <ReactSVG path={customerProfiles} />
            <h5 className="title">Customer profiles</h5>
            <p>
              Keep user database in check. Review a customer’s order history,
              leave notes for staff, deactivate accounts as needed or remove
              them&nbsp;entirely.
            </p>
          </div>
        </div>
      </section>
      <section className="management-section grid">
        <div className="side-header col-lg-4 col-md-6 col-sm-12 col-xs-12">
          <h2>Cart & Checkout</h2>
          <p className="sub-description">
            Saleor is packed with a number of ready-to-use payment methods, as
            well as sales optimization and discount&nbsp;options.
          </p>
        </div>
        <div className="card-grid col-lg-8 col-md-6 col-sm-12 col-xs-12">
          <div className="icon-card">
            <ReactSVG path={paymentIntegration} />
            <h5 className="title">Payment integration</h5>
            <p>
              Collect payments using global payment providers like PayPal
              or&nbsp;Braintree.
            </p>
          </div>
          <div className="icon-card">
            <ReactSVG path={automaticTaxes} />
            <h5 className="title">EU taxes</h5>
            <p>
              Automatically show gross prices to your European customers
              with&nbsp;Vatlayer.
              {/* Apply US sales tax during checkout when serving your American clientele with Avalara. */}
            </p>
          </div>
          {/* <div className="icon-card">
              <ReactSVG path={paymentRequests} />
              <h5 className="title">Payment requests</h5>
              <p>Allow for seamless mobile checkout with the Payment Request API. Provide customers with Google Pay or Apple Pay options.</p>
            </div> */}
          <div className="icon-card">
            <ReactSVG path={discountAndPromotions} />
            <h5 className="title">Discounts & Promotions</h5>
            <p>
              Build seasonal sales with incentives such as free shipping and
              fixed-amount or percentage-rate discounts on single products or
              across entire&nbsp;categories.
            </p>
          </div>
        </div>
      </section>
      <section className="management-section grid">
        <div className="side-header col-lg-4 col-md-6 col-sm-12 col-xs-12">
          <h2>Back Office</h2>
          <p className="sub-description">
            Manage your staff, search through thousands of products, accounts
            and&nbsp;orders.
          </p>
        </div>
        <div className="card-grid col-lg-8 col-md-6 col-sm-12 col-xs-12">
          <div className="icon-card">
            <ReactSVG path={search} />
            <h5 className="title">Search</h5>
            <p>
              Instantly search through your data including orders, products, or
              accounts. Utilize our ElasticSearch integration to gain access to
              additional features like query&nbsp;boosting.
            </p>
          </div>
          <div className="icon-card">
            <ReactSVG path={staffManagement} />
            <h5 className="title">Staff management </h5>
            <p>
              Control responsibilities and access by giving specific permissions
              to individual staff members. Use history timelines to see who
              carried out which&nbsp;changes.
            </p>
          </div>
          <div className="icon-card">
            <ReactSVG path={gdprReady} />
            <h5 className="title">GDPR ready</h5>
            <p>
              We take extra care not to collect any information that is not
              necessary for order fulfillment. User accounts are safe to remove
              without affecting your ability to process&nbsp;orders.
            </p>
          </div>
          <div className="icon-card">
            <ReactSVG path={analytics} />
            <h5 className="title">Analytics</h5>
            <p>
              Saleor supports server-side Google&nbsp;Analytics to report
              ecommerce metrics without affecting your customers’&nbsp;privacy.
            </p>
          </div>
        </div>
      </section>
      <section className="documentation section-container">
        <div className="content">
          <h2>Documentation</h2>
          <h4 className="description">
            Check our comprehensive documentation which can guide you through
            the installation process or customizations that you may want to
            carry&nbsp;out.
          </h4>
          <div className="position">
            <a
              className="btn btn-secondary"
              href="https://saleor.readthedocs.io/en/latest/"
              target="_blank"
              rel="noopener"
            >
              <span>Read the docs</span>
            </a>
          </div>
        </div>
      </section>
      <GitHubBanner />
    </div>
  </div>
);

export default Feature;
