import React from 'react';
import { ScrollLink } from '..';

import css from './feature.css';

import modernStackIcon from '../../images/modern-stack.png';

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
          <div className="card">
            <img src={modernStackIcon} />
            <span className="decorator"></span>
            <h3 className="title">Loved by search engines</h3>
            <p>Saleor is packed with everything you need from sitemaps,
               schema.org structured data, to Open Graph that get you kick-started
               with your e-commerce SEO. Integrate with Google Merchant Center and
               present your products to wider audience.</p>
          </div>
          <div className="card">
            <img src={modernStackIcon} />
            <span className="decorator"></span>
            <h3 className="title">Headless commerce with GraphQL</h3>
            <p>Take advantage of the robust API that gives you an access to any
               third-party integrations you want. Build a mobile app, customize your
               storefront or externalize processes such as inventory management, order
               processing, fulfillment and more</p>
          </div>
          <div className="card">
            <img src={modernStackIcon} />
            <span className="decorator"></span>
            <h3 className="title">Progressive Web Apps</h3>
            <p>Earn a place on users home screens and let them comfortably browse even
               on a slow internet connection or no connection at all. Google Page Speed
               optimization keeps Page Load times low and can result
               in doubling your conversions.</p>
          </div>
          <div className="card">
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
    </div>
);

export default Feature;
