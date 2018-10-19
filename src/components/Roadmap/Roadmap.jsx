import React from 'react';
import MetaTags from 'react-meta-tags';
import { GitHubBanner, ScrollLink } from '..';

import css from './roadmap.css';

const Roadmap = (props) => (
	<div id="roadmap" className="container">
    <MetaTags>
      <title>Get Saleor - Roadmap</title>
      <meta name="description" content="A GraphQL-first eCommerce platform for perfectionists. It is open sourced, PWA ready and stunningly beautiful. Find out why developers love it" />
      <meta property="og:title" content="Get Saleor - Roadmap" />
      <meta property="og:image" content="" />
    </MetaTags>
    <section className="hero">
      <div className="bg-container"></div>
      <div className="plane">
        <h1>Roadmap</h1>
        <p>To keep you informed about the Implementation of the most important features, You will find our Roadmap for 2018, below.</p>
      </div>
      <ScrollLink to="#roadmap-section"> Learn more </ScrollLink>
    </section>
    <section id="roadmap-section" className="roadmap-content">
      <div className="grid roadmap-item">
        <div className="col-xs-3 col-sm-3 col-md-3 line">
          <div className="icon parrot"></div>
          <div className="border-line parrot"></div>
        </div>
        <div className="col-xs-8 col-sm-8 col-md-8 text">
          <h2>Long-Term Goals</h2>
          <div className="grid">
            <div className="col-xs-12 col-sm-6 col-md-6">
              <h4>Storefront 2.0</h4>
              <p>Mobile-first storefront with full PWA support. Support for browser-based payment methods (Google Pay, Apple Pay).</p>
              <h4>Architecture changes (Stable core)</h4>
              <p>Moving storefront and dashboard to separate apps.</p>
              <h4>Avalara integration</h4>
              <p>Integration with Avalara for tax calculations.</p>
            </div>
            <div className="col-xs-12 col-sm-6 col-md-6">
              <h4>CSV export</h4>
              <p>Exporting products, orders and customers to CSV files.</p>
              <h4>Data import</h4>
              <p>Tools to migrate data from Magento and Shopify to Saleor.</p>
              <h4>Shipping carriers</h4>
              <p>Integration with shipping carriers APIs.</p>
            </div>
          </div>
        </div>
      </div>
      <div className="grid roadmap-item">
        <div className="col-xs-3 col-sm-3 col-md-3 line">
        <div className="icon lantern"></div>
        <div className="border-line lantern"></div>
        </div>
        <div className="col-xs-8 col-sm-8 col-md-8 text">
          <h2>Upcoming Release</h2>
          <h4>Dashboard 2.0 - Product Management</h4>
          <p>A refreshed version of product management views implemented as a single-page application.</p>
        </div>
      </div>
      <div className="grid roadmap-item">
        <div className="col-xs-3 col-sm-3 col-md-3 line">
          <div className="icon"></div>
          <div className="border-line"></div>
        </div>
        <div className="col-xs-8 col-sm-8 col-md-8 text">
          <h2>June Release</h2>
          <h4>GraphQL Api (Beta)</h4>
          <h4>Sentry Integration</h4>
          <h4>New Languages - Czech, Chinese (Taiwan)</h4>
        </div>
      </div>
      <div className="grid roadmap-item">
        <div className="col-xs-3 col-sm-3 col-md-3 line">
          <div className="icon"></div>
          <div className="border-line"></div>
        </div>
        <div className="col-xs-8 col-sm-8 col-md-8 text">
          <h2>May Release</h2>
          <h4>Ability to remove customer data</h4>
          <h4>reCAPTCHA integration</h4>
          <h4>Product overselling</h4>
        </div>
      </div>
      <div className="grid roadmap-item">
        <div className="col-xs-3 col-sm-3 col-md-3 line">
          <div className="icon"></div>
          <div className="border-line"></div>
        </div>
        <div className="col-xs-8 col-sm-8 col-md-8 text">
          <h2>April Release</h2>
          <h4>Tax support for European countries</h4>
          <h4>Simplified stock management</h4>
          <h4>Customer notes</h4>
          <h4>Improved menu management</h4>
          <h4>Draft product collections</h4>
        </div>
      </div>
      <div className="grid roadmap-item">
        <div className="col-xs-3 col-sm-3 col-md-3 line">
          <div className="icon"></div>
          <div className="border-line"></div>
        </div>
        <div className="col-xs-8 col-sm-8 col-md-8 text">
          <h2>March Release</h2>
          <h4>Multilingual storefront</h4>
          <h4>Creating orders through the dashboard</h4>
          <h4>Customizable storefront navigation</h4>
          <h4>SEO tools</h4>
          <h4>Email schema markup</h4>
        </div>
      </div>
      <div className="grid roadmap-item">
        <div className="col-xs-3 col-sm-3 col-md-3 line">
          <div className="icon"></div>
          <div className="border-line"></div>
        </div>
        <div className="col-xs-8 col-sm-8 col-md-8 text">
          <h2>February Release</h2>
          <h4>Upgraded price handling</h4>
          <h4>Adding custom pages through the  dashboard</h4>
          <h4>Dropped Satchless API</h4>
          <h4>Switched to Webpack 4</h4>
        </div>
      </div>
      <div className="grid roadmap-item">
        <div className="col-xs-3 col-sm-3 col-md-3 line">
          <div className="icon"></div>
          <div className="border-line"></div>
        </div>
        <div className="col-xs-8 col-sm-8 col-md-8 text">
          <h2>January Release</h2>
          <h4>Added support for Django 2.0</h4>
          <h4>MJML templates for emails</h4>
          <h4>Product collections</h4>
          <h4>Adding order notes in checkout</h4>
          <h4>Lazy-loading images in the storefront</h4>
          <h4>Creating customers through the dashboard</h4>
        </div>
      </div>
      <div className="grid roadmap-item">
        <div className="col-xs-3 col-sm-3 col-md-3 line">
          <div className="icon"></div>
          <div className="border-line last"></div>
        </div>
        <div className="col-xs-8 col-sm-8 col-md-8 text">
          <h2>December Release</h2>
          <h4>Dropped Python 2.7</h4>
          <h4>Added OpenGraph tags and canonical links</h4>
          <h4>Selectable country prefixes for phone numbers in checkout</h4>
          <h4>Rendering explanatory “zero” page</h4>
        </div>
      </div>
    </section>
    <GitHubBanner />
  </div>
);

export default Roadmap;