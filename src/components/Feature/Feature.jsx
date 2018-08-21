import React from 'react';
import { ScrollLink } from '..';
import { GitHubBanner } from '..';

import css from './feature.css';

import modernStackIcon from '../../images/modern-stack.png'
import productVariant from '../../images/products-variants.png';
import collectionsIcon from '../../images/collections.png';
import multipleImages from '../../images/multiple-images.png';
import seoIcon from '../../images/seo.png';
import nonShippableIcon from '../../images/non-shippable.png';
import multiCareerShipping from '../../images/multi-career-shipping.png';
import multipleDispatch from '../../images/multiple-dispatch.png';
import refunds from '../../images/refunds.png';
import fulfillment from '../../images/fulfillment.png';
import customerProfiles from '../../images/customer-profiles.png';
import paymentIntegration from '../../images/payments-integration.png';
import automaticTaxes from '../../images/automatic-taxes.png';
import paymentRequests from '../../images/payment-requests.png';
import discountAndPromotions from '../../images/discount-and-promotions.png';
import search from '../../images/search.png';
import staffManagement from '../../images/staff-management.png';
import gdprReady from '../../images/gdpr-ready.png';
import analytics from '../../images/analytics.png';


const Feature = () => (
    <div id="feature">
      <section className="hero">
        <div className="bg-container"></div>
        <div className="plane">
          <h1 className="title">A GraphQL-first ecommerce platform for perfectionists.</h1>
        </div>
        <ScrollLink to="#testimonial"> Learn more </ScrollLink>
      </section>
      <section id="testimonial" className="testimonial">
        <p className="comment quote text-light">“After actively using and developing our Saleor store for over a year, if I were to create a new shop today I would go for it again without a doubt.”</p>
        <div className="testimonial-author">
          <h5 className="name">Tyler Hildebrandt,</h5>
          <h5 className="position">Lead developer. Patch Garden</h5>
        </div>
      </section>
      <section className="features">
        <div className="grid icons">
          <div className="icon-card">
            <img src={modernStackIcon} />
            <span className="decorator"></span>
            <h3 className="title">Loved by search engines</h3>
            <p>Saleor is packed with everything you need from sitemaps,
               schema.org structured data, to Open Graph that get you kick-started
               with your e-commerce SEO. Integrate with Google Merchant Center and
               present your products to wider audience.</p>
          </div>
          <div className="icon-card">
            <img src={modernStackIcon} />
            <span className="decorator"></span>
            <h3 className="title">Headless commerce with GraphQL</h3>
            <p>Take advantage of the robust API that gives you an access to any
               third-party integrations you want. Build a mobile app, customize your
               storefront or externalize processes such as inventory management, order
               processing, fulfillment and more</p>
          </div>
          <div className="icon-card">
            <img src={modernStackIcon} />
            <span className="decorator"></span>
            <h3 className="title">Progressive Web Apps</h3>
            <p>Earn a place on users home screens and let them comfortably browse even
               on a slow internet connection or no connection at all. Google Page Speed
               optimization keeps Page Load times low and can result
               in doubling your conversions.</p>
          </div>
          <div className="icon-card">
            <img src={modernStackIcon} />
            <span className="decorator"></span>
            <h3 className="title">Internationalization & Localization</h3>
            <p>Make your shop multilanguage by default. Show prices in local currencies
               using GeoIP, and adjust addresses and formats to the chosen region.
               Our community has also provided translations for more than 20 languages
               with coverage ranging up to 98%.</p>
          </div>
        </div>
      </section>
      <section className="product-management management-section grid">
        <div className="side-header col-md-5 col-sm-12 col-xs-12">
          <h2>Product Management</h2>
          <p className="sub-description">Product offer attractiveness is the resultant of many factors - price,
          exposure and variety. Be in charge of that. </p>
        </div>
        <div className="card-grid col-md-7 col-sm-12 col-xs-12">
          <div className="icon-card">
              <img src={productVariant} />
              <h5 className="title">Product & Variants</h5>
              <p>Use attributes like color and size to create
                 unlimited product variants. Enable your customers
                 to use faceted search to find relevant products.</p>
            </div>
            <div className="icon-card">
              <img src={collectionsIcon} />
              <h5 className="title">Collections</h5>
              <p>Assign products to groups to allow customers to shop by look,
                 theme or purpose. Combine collections with vouchers and discounts
                 to create seasonal promotions.</p>
            </div>
            <div className="icon-card">
              <img src={multipleImages} />
              <h5 className="title">Multiple Images</h5>
              <p>Add unlimited images to your products and have Saleor automatically
                 generate thumbnails in all relevant dimensions to satisfy
                 both desktop and mobile users.</p>
            </div>
            <div className="icon-card">
              <img src={seoIcon} />
              <h5 className="title">SEO</h5>
              <p>Edit individual product’s metadata and override fields like name
                 and description to improve your visibility both in search engine
                 results and in social media.</p>
            </div>
            <div className="icon-card">
              <img src={nonShippableIcon} />
              <h5 className="title">Non-shippable products</h5>
              <p>Sell products like digital goods and services, and have the storefront
                 automatically skip the shipping method and address during checkout.</p>
            </div>
        </div>
      </section>
      <section className="product-management management-section grid">
        <div className="side-header col-md-5 col-sm-12 col-xs-12">
          <h2>Order Management</h2>
          <p className="sub-description">Saleor gives you full control over placed orders
          - from the checkout to customer management and finishing  with product delivery.</p>
        </div>
        <div className="card-grid col-md-7 col-sm-12 col-xs-12">
          <div className="icon-card">
              <img src={multiCareerShipping} />
              <h5 className="title">Multi-carrier shipping</h5>
              <p>Let buyers choose between multiple carriers and
                 delivery methods. Set availability and rates separately
                 for different countries.</p>
            </div>
            <div className="icon-card">
              <img src={multipleDispatch} />
              <h5 className="title">Multiple dispatch</h5>
              <p>Need to ship certain items separately or on a different date? Deliver
                 a single order using multiple fulfillments, even if it means
                 splitting the quantity of a single product.</p>
            </div>
            <div className="icon-card">
              <img src={refunds} />
              <h5 className="title">Refunds</h5>
              <p>If anything goes wrong or a product needs to be returned,
                 reimburse your customers using the intuitive refund screen.</p>
            </div>
            <div className="icon-card">
              <img src={fulfillment} />
              <h5 className="title">Fulfillment</h5>
              <p>Remain in control throughout the entire lifecycle of your orders.
                 Use custom search and filtering, leave comments for other staff members
                 and check the detailed history of every order.</p>
            </div>
            <div className="icon-card">
              <img src={customerProfiles} />
              <h5 className="title">Customer profiles</h5>
              <p>Keep user database in check. Review a customer’s order history,
                 leave notes for staff, deactivate accounts as needed or remove them entirely.</p>
            </div>
        </div>
      </section>
      <section className="management-section grid">
        <div className="side-header col-md-5 col-sm-12 col-xs-12">
          <h2>Cart & Checkout</h2>
          <p className="sub-description">Saleor is packed with a number of ready-to-use payment methods,
          sales optimization and discount options.</p>
        </div>
        <div className="card-grid col-md-7 col-sm-12 col-xs-12">
          <div className="icon-card">
              <img src={paymentIntegration} />
              <h5 className="title">Payments integration</h5>
              <p>Collect payments using a wide range of global payment providers like PayPal or Stripe,
                 or opt for a region-specific option like CyberSource.</p>
            </div>
            <div className="icon-card">
              <img src={automaticTaxes} />
              <h5 className="title">Automatic taxes</h5>
              <p>Automatically show gross prices to your European customers with Vatlayer.
                 Apply US sales tax during checkout when serving your American clientele with Avalara.</p>
            </div>
            <div className="icon-card">
              <img src={paymentRequests} />
              <h5 className="title">Payment requests</h5>
              <p>Allowing for a seamless mobile checkout with the Payment Request API.
                 Allow your customers to pay using Google Pay or Apple Pay.</p>
            </div>
            <div className="icon-card">
              <img src={discountAndPromotions} />
              <h5 className="title">Discounts & Promotions</h5>
              <p>Build seasonal sales with incentives such as free shipping, fixed amount
                 or percentage rate discounts which could be limited to single
                 products or entire categories.</p>
            </div>
        </div>
      </section>
      <section className="management-section grid">
        <div className="side-header col-md-5 col-sm-12 col-xs-12">
          <h2>Back Office</h2>
          <p className="sub-description">Manage your staff, search through thousands of products, accounts and orders.</p>
        </div>
        <div className="card-grid col-md-7 col-sm-12 col-xs-12">
          <div className="icon-card">
              <img src={search} />
              <h5 className="title">Search</h5>
              <p>Instantly search through your data including orders, products, or accounts.
                 Utilize our ElasticSearch integration to gain access to additional
                 features like query boosting.</p>
            </div>
            <div className="icon-card">
              <img src={staffManagement} />
              <h5 className="title">Staff management </h5>
              <p>Control responsibilities and access by giving your staff members specific permissions.
                 Use history timelines to see who carried out which changes.</p>
            </div>
            <div className="icon-card">
              <img src={gdprReady} />
              <h5 className="title">GDPR ready</h5>
              <p>We take extra care not to collect any information that is not necessary for order fulfillment.
                 User accounts are safe to remove without affecting your ability to process orders.</p>
            </div>
            <div className="icon-card">
              <img src={analytics} />
              <h5 className="title">Analytics</h5>
              <p>Saleor supports server-side Google Analytics to report ecommerce metrics
                 without affecting your customers’ privacy.</p>
            </div>
        </div>
      </section>
      <section className="documentation">
        <div className="content">
          <h2>Documentation</h2>
          <h4 className="description">Check our comprehensive documentation which can guide
          you through the installation process or customizations that you may want to carry out.</h4>
          <a className="btn btn-primary" href="https://saleor.readthedocs.io/en/latest/" target="_blank">Read the docs</a>
        </div>
      </section>
      <GitHubBanner />
    </div>
);

export default Feature;
