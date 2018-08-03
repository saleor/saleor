import React, { Component } from 'react';
import ReactSVG from 'react-svg';
import { Tab, Tabs, TabList, TabPanel } from 'react-tabs';
import { GitHubLink } from '..';

import css from './home.css';

import modernStackIcon from '../../images/modern-stack.png';
import buildToScaleIcon from '../../images/build-to-scale.png';
import easyToCustomizeIcon from '../../images/easy-to-customize.png';
import greatExperienceIcon from '../../images/great-experience.png';
import starsBg from '../../images/open-source-bg.png';

class Home extends Component {
  constructor(props) {
    super(props);
    this.state = { tabIndex: 0 };
  }

  render() {
    return (
      <div id="home">
        <section className="hero">
          <div className="plane">
            <h1>A graphql-first ecommerce <span className="primaryColor">platform for perfectionists</span></h1>
            <a href="#" className="btn btn-secondary">See demo</a>
            <a href="#" className="btn btn-primary">Brief us</a>
          </div>
        </section>
        <section className="features">
          <div className="grid icons">
            <div className="column-3">
              <img src={modernStackIcon} />
              <h3><span>01<br/>-</span>Modern <br />stack</h3>
            </div>
            <div className="column-3">
              <img src={buildToScaleIcon} />
              <h3><span>02<br/>-</span>Build to <br />scale</h3>
            </div>
            <div className="column-3">
              <img src={easyToCustomizeIcon} />
              <h3><span>03<br/>-</span>Easy to <br />customize</h3>
            </div>
            <div className="column-3">
              <img src={greatExperienceIcon} />
              <h3><span>04<br/>-</span>Great <br />expierience</h3>
            </div>
          </div>
          <div className="section-container">
            <div className="grid feature-item software-stack">
              <div className="column-6 text">
                <h2>State of the art<br /> software stack</h2>
                <p><strong>Saleor is powered by a GraphQL server running on top of Python 3 and Django 2.</strong></p>
                <p>Both the storefront and the dashboard are React applications written in TypeScript and use Apollo GraphQL. Strict code quality checks and code reviews make the code easy to read and understand. High test coverage ensures it’s also safe to deploy in a continuous manner.</p>
              </div>
              <div className="column-6 image"></div>
            </div>
            <div className="grid feature-item build-to-scale">
              <div className="column-6 image"></div>
              <div className="column-6 text">
                <h2>Build to scale</h2>
                <p><strong>Serve millions of products and thousands of customers without breaking a sweat. </strong></p>
                <p>Saleor is optimized for cloud deployments using Docker. Horizontal scalability allows Saleor to take advantage of platforms such as AWS and Google Cloud and adapt to your traffic. Multi-container deployments allow your software to scale without downtimes. Persistent GraphQL Queries take advantage of CDN to ensure snappy performance under even the heaviest of loads.</p>
              </div>
            </div>
            <div className="grid feature-item easy-to-customize">
              <div className="column-6 text">
                <h2>Easy to customize</h2>
                <p><strong>Saleor’s outstanding out-of-the-box experience may not be enough for everyone.</strong></p>
                <p>Take it even further to automate any commerce process like ordering, shipping or payment. Whether you’re a local florist or a government agency, Saleor is a solid foundation to build and deliver bespoke solutions to your specific problems. Build the store that you want instead of trying to bend your requirements around enterprise platforms.</p>
              </div>
              <div className="column-6 image"></div>
            </div>
            <div className="feature-item user-experience text-center">
              <h2>User experience that simply rocks</h2>
              <h4>Unlike what you might expect from open source software Saleor’s user experience rivals that of the best commercial solutions.</h4>
            </div>
            <div className="grid feature-item storefront">
              <div className="column-6 text">
                <h2>Storefront</h2>
                <p><strong>Saleor takes advantage of PWA standards  to optimize mobile experiences of the rapidly growing group of people shopping on the run. </strong></p>
                <p>Allow your customers to buy their next pair of jeans while enjoying a virgin margarita on a plane. They will only need an internet connection when they go to pay with Apple Pay or one of the cards stored by their phone. </p>
              </div>
              <div className="column-6 image"></div>
            </div>
            <div className="grid feature-item dashboard">
              <div className="column-6 image"></div>
              <div className="column-6 text">
                <h2>Dashboard</h2>
                <p><strong>Easy-to-use dashboard makes managing your store a pleasant experience whether you’re using the latest Macbook or a two-year-old smartphone. </strong></p>
                <p>Its intuitive interface is designed to aid your staff in daily routines like order management, inventory tracking or reporting. Saleor dashboard’s friendly home screen will also suggest items that may need your attention so you always stay on top of things.</p>
              </div>
            </div>
            <div className="text-center">
              <a className="btn btn-primary" href="">See more features</a>
            </div>
          </div>
        </section>
        <section className="open-source">
          <div className="section-container">
            <div className="text">
              <h2>Open source</h2>
              <p><strong>While built and maintained by Mirumee Software, Saleor’s community is among the fastest growing open source ecommerce platforms. </strong></p>
              <p>What started in 2010 as a humble solution to a local problem has over the years become a platform that many of you rely on in your day to day job. We wouldn’t be here if it wasn’t for all of our great contributors and supporters.</p>
            </div>
            <div className="stars-bg">
              <img src={starsBg} />
            </div>
            <div className="github-circle">
              <GitHubLink owner="mirumee" name="saleor" text="Github Stars" />
            </div>
            <div className="grid icons">
              <div className="column-2">
                <ReactSVG className="github-icon" path="images/github-icon.svg" />
                <h5>Suggest features <br/>and propose changes</h5>
              </div>
              <div className="column-2">
                <ReactSVG className="transifex-icon" path="images/transifex-icon.svg" />
                <h5>Translate Saleor <br/>to your language</h5>
              </div>
              <div className="column-2">
                <ReactSVG className="gitter-icon" path="images/gitter-icon.svg" />
                <h5>Discuss the <br/>featre of Saleor</h5>
              </div>
              <div className="column-2">
                <ReactSVG className="stackoverflow-icon" path="images/stackoverflow-icon.svg" />
                <h5>Ask for <br />help</h5>
              </div>
              <div className="column-2">
                <ReactSVG className="medium-icon" path="images/medium-icon.svg" />
                <h5>Follow Saleor's<br/> development</h5>
              </div>
            </div>
          </div>
        </section>
        <section className="saleor-in-action">
          <div className="section-container">
            <Tabs selectedIndex={this.state.tabIndex} onSelect={tabIndex => this.setState({ tabIndex })}>
              <div className="grid head">
                <div className="column-6">
                  <h2 className={`tab-${this.state.tabIndex}`}>Saleor in action</h2>
                </div>
                <div className="column-6">
                  <TabList className="tabs grid">
                    <Tab className="column-6">Case studies</Tab>
                    <Tab className="column-6">Implementations</Tab>
                  </TabList>
                </div>
              </div>
              <TabPanel className="case-study">
                <div className="grid">
                  <div className="column-6">
                    <ReactSVG className="pg-logo" path="images/pg-logo.svg" />
                    <img src="../../images/pg-showcase.png" />
                  </div>
                  <div className="column-6">
                    <div className="pg-quote">
                      <p>“The response time of the website has improved dramatically. We’re down below the 1-second mark whereas previously we were 3.5-4 seconds on average. We've also been able to maintain that response time during extreme high-traffic.”</p>
                      <div className="author">
                        <img src="../../images/pg-quote.png" />
                        <h5>Tim Kalic, <br/>Head of Digital Pretty Green</h5>
                      </div>
                      <a className="btn btn-primary" href="#">See case study</a>
                    </div>
                  </div>
                </div>
              </TabPanel>
              <TabPanel className="implementation">
                <div className="grid">
                  <div className="column-6">
                    <img src="../../images/implementation1.png" />
                    <div className="text-center">
                      <a className="btn btn-primary" href="#">Visit website</a>
                    </div>
                  </div>
                  <div className="column-6">
                    <img src="../../images/implementation1.png" />
                    <div className="text-center">
                    <a className="btn btn-primary" href="#">Visit website</a>
                    </div>
                  </div>
                </div>
              </TabPanel>
            </Tabs>
          </div>
        </section>
        <section className="enterprice-consulting">
          <div className="section-container">
            <h2>Enterprice consulting</h2>
            <h3>Some situations however call for a custom solution and extra code to be written. In that case, our team can help.</h3>
            <div className="list grid">
              <div className="column-5">
                <ul>
                  <li><span>if you're looking for b2b or entreprise solutions</span></li>
                  <li><span>if a licensed platform is not enough</span></li>
                  <li><span>if you’re outgrowing your existing solution</span></li>
                </ul>
              </div>
              <div className="column-7">
                <ul>
                  <li><span>if you need unlimited integration possibilities</span></li>
                  <li><span>if you’re a high-volume business</span></li>
                  <li><span>if you need a reliable and secure implementation</span></li>
                </ul>
              </div>
            </div>
            <div className="center">
              <a className="btn btn-secondary" href="">Estimate your project</a>
            </div>
          </div>
        </section>
      </div>
    );
  }
}

export default Home;