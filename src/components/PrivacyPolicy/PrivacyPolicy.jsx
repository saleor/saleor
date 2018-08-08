import React, { Component } from 'react';
import { ScrollLink } from '..';

import css from './privacypolicy.css';

const PrivacyPolicy = () => (
	<div id="privacy-policy">
		<section className="hero">
			<div className="plane">
				<h1 className="title">Privacy Policy</h1>
				<p className="text-large">We respect your privacy and transparency is something we highly value. Below you can learn everything about information we collect.</p>
			</div>
			<ScrollLink to="#general-information"> Learn more </ScrollLink>
      <div className="decoration">
        <img src="../../images/decoration08.png" />
      </div>
		</section>
		<section id="general-information" className="general-information">
			<h3 className="title">General Information</h3>
			<p className="description">The Saleor website is operated by Mirumee Software sp. z.o.o. sp. k. operating at the following address:</p>
			<div className="border-left bold">
				<h5>Mirumee Software sp. z.o.o. sp. k.</h5>
				<h5>ul. Tęczowa 7</h5>
				<h5>53-601 Wrocław Poland</h5>
			</div>
		</section>
		<section className="analytics">
			<h3 className="title">Analytics</h3>
			<p className="description">This website includes Google Analytics software that collects anonymized information about visitors to help us provide better services. <a href="">See how Google uses your data.</a></p>
		</section>
		<section className="your-rights">
			<h3 className="title">Your Rights</h3>
			<p className="description">GDPR guarantees you a number of rights including but not limited to:</p>
			<ul className="list">
				<li>
					<span className="bullet"/>
					the right to know what data concerning you is held by any particular company and how it is processed;
				</li>
				<li>
          <span className="bullet"/>
					the right to rectify any inaccurate personal data;
				</li>
				<li>
          <span className="bullet"/>
					the right to be forgotten;
				</li>
				<li>
          <span className="bullet"/>
					the right to restriction of processing;
				</li>
				<li>
          <span className="bullet"/>
					the right to object to processing.
				</li>
			</ul>
      <p className="description">Please consult the <a href="">GDPR text in your language</a> to better understand your rights.</p>
      <p className="description">We ask that you direct all questions and requests related to your personal data to <a href="">privacy@mirumee.com</a> or that you send them to the postal address of the company listed above </p>
		</section>
		<section className="banner text-center">
      <h1>simple <span className="text-light">is</span> better</h1>
      <h1>less <span className="text-light">is</span> more</h1>
      <h1>saleor <span className="text-light">is</span> free</h1>
      <a className="btn btn-primary" href="">Fork it on Github</a>
      <div className="decoration decoration-left">
        <img src="../../images/decoration07.png" />
      </div>
      <div className="decoration decoration-right">
        <img src="../../images/decoration09.png" />
      </div>
		</section>
	</div>
);

export default PrivacyPolicy;
