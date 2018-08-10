import React from 'react';
import { ScrollLink } from '..';

import css from './feature.css';

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
  
      </section>
    </div>
);

export default Feature;
