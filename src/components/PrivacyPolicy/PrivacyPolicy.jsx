import React, { Component } from 'react';
import { ScrollLink, GitHubBanner } from '..';
import { Helmet } from "react-helmet";
import css from './privacypolicy.css';

const PrivacyPolicy = () => (
	<div id="privacy-policy" className="container">
		<Helmet>
			<title>Privacy Policy | Saleor - A GraphQL-first Open Source eCommerce Platform</title>
			<meta name="description" content="We respect your privacy and we are transparent in everything we do. Learn all you need to know about the information we collectt" />
		</Helmet>
		<section className="hero">
			<div className="bg-container"></div>
			<div className="plane">
				<h1 className="title">Privacy Policy</h1>
				<p className="text-large text-light">We respect your privacy and transparency is something we highly value. Below you can learn everything about information we&nbsp;collect.</p>
			</div>
			<ScrollLink to="#general-information"> Learn more </ScrollLink>
		</section>
		<section id="general-information" className="general-information section-container">
			<h3 className="title">General Information</h3>
			<p className="description text-light">The Saleor website is operated by Mirumee Software sp. z.o.o. sp. k. operating at the following&nbsp;address:</p>
			<div className="border-left bold">
				<h5>Mirumee Software sp.&nbsp;z.o.o.&nbsp;sp.&nbsp;k.</h5>
				<h5>ul. Tęczowa&nbsp;7</h5>
				<h5>53-601&nbsp;Wrocław</h5>
				<h5>Poland</h5>
			</div>
		</section>
		<section className="analytics section-container">
			<h3 className="title">Analytics</h3>
			<p className="description text-light">This website includes Google Analytics software that collects anonymized information about visitors to help us provide better services. <a href="">See how Google uses your&nbsp;data.</a></p>
		</section>
		<section className="your-rights section-container">
			<h3 className="title">Your Rights</h3>
			<p className="description text-light">GDPR guarantees you a number of rights including but not limited&nbsp;to:</p>
			<ul className="list text-light">
				<li><span>the right to know what data concerning you is held by any particular company and how it is&nbsp;processed: </span></li>
				<li><span>the right to rectify any inaccurate personal&nbsp;data:</span></li>
				<li><span>the right to be&nbsp;forgotten:</span></li>
				<li><span>the right to restriction of&nbsp;processing:</span></li>
				<li><span>the right to object to&nbsp;processing.</span></li>
			</ul>
      <p className="description text-light">Please consult the <a href="">GDPR text in your language</a> to better understand your&nbsp;rights.</p>
      <p className="description text-light">We ask that you direct all questions and requests related to your personal data to <a href="mailto:privacy@mirumee.com">privacy@mirumee.com</a> or that you send them to the postal address of the company listed&nbsp;above </p>
		</section>
		<GitHubBanner />
	</div>
);

export default PrivacyPolicy;
