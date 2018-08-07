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
		</section>
		<section id="general-information" className="general-information">
			<h3>General Information</h3>
			<p>The Saleor website is operated by Mirumee Software sp. z.o.o. sp. k. operating at the following address:</p>
			<div className="border-left">
				<h5>Mirumee Software sp. z.o.o. sp. k.</h5>
				<h5>ul. Tęczowa 7</h5>
				<h5>53-601 Wrocław Poland</h5>
			</div>
		</section>
		<section className="analytics">
			<h3>Analytics</h3>
			<p>This website includes Google Analytics software that collects anonymized information about visitors to help us provide better services. See how Google uses your data.</p>
		</section>
		<section className="your-rights">
			<h3>Your Rights</h3>
			<p>GDPR guarantees you a number of rights including but not limited to:</p>
			<ul>
				<li>the right to know what data concerning you is held by any particular company and how it is processed;</li>
				<li>the right to rectify any inaccurate personal data;</li>
				<li>the right to be forgotten;</li>
				<li>the right to restriction of processing;</li>
				<li>the right to object to processing.</li>
			</ul>
		</section>
	</div>
);

export default PrivacyPolicy;
