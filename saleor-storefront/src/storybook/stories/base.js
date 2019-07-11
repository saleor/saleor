import * as React from 'react';
import { storiesOf, addDecorator } from '@storybook/react';

storiesOf('Base', module)
  .add('Typography', () => (
    <div className='typography-section'>
      <p>Montserrat Font is a typography base for the saleor storefront</p>
      <h3>Montserrat Regular used mainly for body text and miscellaneous texts</h3>
      <h3>Montserrat Bold used mainly for headers and important messages</h3>
      <p>If it is possible we shouldn’t use font size smaller than 14px. 
16px font is going to be used as a standard text size with 110% spacing</p>
    </div>
  ))
  .add('Colors', () => (
    <div className='colors-section'>
      <span className='colors-section__turquoise-dark'>
        Hex: #55C4B3<br/>
        Pantone: 7472 C
      </span>
      <span className='colors-section__turquoise'>
        Hex: #51E9D2<br/>
        Pantone: 333 C
      </span>
      <span className='colors-section__blue'>
        Hex: #21125E<br/>
        Pantone: 274 C
      </span>
      <span className='colors-section__rose'>
        Hex: #C22D74<br/>
        Pantone: 7647 C
      </span>
      <span className='colors-section__green'>
        Hex: #3ED256<br/>
        Pantone: 802 C
      </span>
      <span className='colors-section__gray'>
        Hex: #949494<br/>
        Pantone: Cool Gray 7 C
      </span>
    </div>
  ));
