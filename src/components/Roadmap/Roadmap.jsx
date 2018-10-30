import React from 'react';
import { GitHubBanner, ScrollLink } from '..';
import { Helmet } from "react-helmet";
import css from './roadmap.css';

const Roadmap = (props) => (
	<div id="roadmap" className="container"> 
    <Helmet>
      <title>Roadmap | Saleor - A GraphQL-first Open Source eCommerce Platform</title>
      <meta name="description" content="Read about the long-term goals for Saleor, as well as the notes from all past and upcoming releases. Find out about all the features we have implemented and how they fit the plan." />
    </Helmet>
    <section className="hero">
      <div className="bg-container"></div>
      <div className="plane">
        <h1>Roadmap</h1>
        <p>Keep up to date with our latest Python, Django, React and GraphQL implementations. See what is coming in&nbsp;2019.</p>
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
              <p>Mobile-first storefront with full PWA support. Support for browser-based payment methods (Google&nbsp;Pay,&nbsp;Apple&nbsp;Pay).</p>
              <h4>Architecture changes&nbsp;(Stable core)</h4>
              <p>Moving storefront and dashboard to separate&nbsp;apps.</p>
              <h4>Avalara&nbsp;integration</h4>
              <p>Integration with Avalara for tax&nbsp;calculations.</p>
            </div>
            <div className="col-xs-12 col-sm-6 col-md-6">
              <h4>CSV&nbsp;export</h4>
              <p>Exporting products, orders and customers to CSV&nbsp;files.</p>
              <h4>Data&nbsp;import</h4>
              <p>Tools to migrate data from Magento and Shopify to&nbsp;Saleor.</p>
              <h4>Shipping&nbsp;carriers</h4>
              <p>Integration with shipping carriers&nbsp;APIs.</p>
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
          <h2>Upcoming&nbsp;Release</h2>
          <h4>Dashboard 2.0 - Product&nbsp;Management</h4>
          <p>A refreshed version of product management views implemented as a single-page&nbsp;application.</p>
        </div>
      </div>
      <div className="grid roadmap-item">
        <div className="col-xs-3 col-sm-3 col-md-3 line">
          <div className="icon"></div>
          <div className="border-line"></div>
        </div>
        <div className="col-xs-8 col-sm-8 col-md-8 text">
          <h2>June&nbsp;Release</h2>
          <h4>GraphQL Api&nbsp;(Beta)</h4>
          <h4>Sentry&nbsp;Integration</h4>
          <h4>New Languages - Czech, Chinese&nbsp;(Taiwan)</h4>
        </div>
      </div>
      <div className="grid roadmap-item">
        <div className="col-xs-3 col-sm-3 col-md-3 line">
          <div className="icon"></div>
          <div className="border-line"></div>
        </div>
        <div className="col-xs-8 col-sm-8 col-md-8 text">
          <h2>May Release</h2>
          <h4>Ability to remove customer&nbsp;data</h4>
          <h4>reCAPTCHA&nbsp;integration</h4>
          <h4>Product&nbsp;overselling</h4>
        </div>
      </div>
      <div className="grid roadmap-item">
        <div className="col-xs-3 col-sm-3 col-md-3 line">
          <div className="icon"></div>
          <div className="border-line"></div>
        </div>
        <div className="col-xs-8 col-sm-8 col-md-8 text">
          <h2>April Release</h2>
          <h4>Tax support for European&nbsp;countries</h4>
          <h4>Simplified stock&nbsp;management</h4>
          <h4>Customer&nbsp;notes</h4>
          <h4>Improved menu&nbsp;management</h4>
          <h4>Draft product&nbsp;collections</h4>
        </div>
      </div>
      <div className="grid roadmap-item">
        <div className="col-xs-3 col-sm-3 col-md-3 line">
          <div className="icon"></div>
          <div className="border-line"></div>
        </div>
        <div className="col-xs-8 col-sm-8 col-md-8 text">
          <h2>March&nbsp;Release</h2>
          <h4>Multilingual&nbsp;storefront</h4>
          <h4>Creating orders through the&nbsp;dashboard</h4>
          <h4>Customizable storefront&nbsp;navigation</h4>
          <h4>SEO&nbsp;tools</h4>
          <h4>Email schema&nbsp;markup</h4>
        </div>
      </div>
      <div className="grid roadmap-item">
        <div className="col-xs-3 col-sm-3 col-md-3 line">
          <div className="icon"></div>
          <div className="border-line"></div>
        </div>
        <div className="col-xs-8 col-sm-8 col-md-8 text">
          <h2>February&nbsp;Release</h2>
          <h4>Upgraded price&nbsp;handling</h4>
          <h4>Adding custom pages through the&nbsp;dashboard</h4>
          <h4>Dropped Satchless&nbsp;API</h4>
          <h4>Switched to Webpack&nbsp;4</h4>
        </div>
      </div>
      <div className="grid roadmap-item">
        <div className="col-xs-3 col-sm-3 col-md-3 line">
          <div className="icon"></div>
          <div className="border-line"></div>
        </div>
        <div className="col-xs-8 col-sm-8 col-md-8 text">
          <h2>January&nbsp;Release</h2>
          <h4>Added support for Django&nbsp;2.0</h4>
          <h4>MJML templates for&nbsp;emails</h4>
          <h4>Product&nbsp;collections</h4>
          <h4>Adding order notes in&nbsp;checkout</h4>
          <h4>Lazy-loading images in the&nbsp;storefront</h4>
          <h4>Creating customers through the&nbsp;dashboard</h4>
        </div>
      </div>
      <div className="grid roadmap-item">
        <div className="col-xs-3 col-sm-3 col-md-3 line">
          <div className="icon"></div>
          <div className="border-line last"></div>
        </div>
        <div className="col-xs-8 col-sm-8 col-md-8 text">
          <h2>December&nbsp;Release</h2>
          <h4>Dropped Python&nbsp;2.7</h4>
          <h4>Added OpenGraph tags and canonical&nbsp;links</h4>
          <h4>Selectable country prefixes for phone numbers in&nbsp;checkout</h4>
          <h4>Rendering explanatory “zero”&nbsp;page</h4>
        </div>
      </div>
    </section>
    <GitHubBanner />
  </div>
);

export default Roadmap;