import React from 'react';
import { ScrollLink } from '..';

import css from './feature.css';

import modernStackIcon from '../../images/modern-stack.png'
import productVariant from '../../images/products-variants.png';
import collectionsIcon from '../../images/collections.png';
import multipleImages from '../../images/multiple-images.png';
import seoIcon from '../../images/seo.png';
import nonShippableIcon from '../../images/non-shippable.png';

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
        <p className="comment">“After actively using and developing our Saleor store for over a year, if I were to create a new shop today I would go for it again without a doubt.”</p>
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
      <section className="product-management grid">
        <div className="side-header col-md-5 col-xs-12">
          <h2>Product Management</h2>
          <p>Product offer attractiveness is the resultant of many factors - product price, exposure or their variety. Be in charge of that.</p>
        </div>
        <div className="icons col-md-7 col-xs-12">
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
                 generate thumbnails in all relevant sizes to make both desktop
                 and mobile users happy.</p>
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
    </div>
);

export default Feature;
