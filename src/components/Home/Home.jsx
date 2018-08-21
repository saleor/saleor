import React, { Component } from 'react';
import ReactSVG from 'react-svg';
import { Tab, Tabs, TabList, TabPanel } from 'react-tabs';
import { GitHubLink } from '..';
import { isMobileOnly } from 'react-device-detect';

import { ScrollLink } from '..';

import css from './home.css';

import modernStackIcon from '../../images/modern-stack.png';
import buildToScaleIcon from '../../images/build-to-scale.png';
import easyToCustomizeIcon from '../../images/easy-to-customize.png';
import greatExperienceIcon from '../../images/great-experience.png';
import starsBg from '../../images/open-source-bg.png';
import mobileStarsBg from '../../images/open-source-bg2.png';

import decoration01 from '../../images/decoration01.png';
import decoration02 from '../../images/decoration02.png';
import decoration03 from '../../images/decoration03.png';
import decoration04 from '../../images/decoration04.png';
import decoration05 from '../../images/decoration05.png';
import decoration06 from '../../images/decoration06.png';
import decoration07 from '../../images/decoration07.png';

class Home extends Component {
  constructor(props) {
    super(props);
    this.toggleNewsBar= this.toggleNewsBar.bind(this);
    this.state = { 
      tabIndex: 0,
      newsBar: true
    };
  }

  toggleNewsBar() {
    const currentState = this.state.newsBar;
    this.setState({ newsBar: !currentState });
  };

  render() {
    return (
      <div id="home">
        <section className="hero">
          <div className="bg-container"></div>
          <div className="plane">
            {this.state.newsBar &&
            <div className="news">
              <div className="label">NEW</div>
              <div className="content">
                <a href="">April release is out. Check out what's new!</a>
                <div className="close-icon" onClick={this.toggleNewsBar}></div>
              </div>
            </div>
            }
            <h1>A graphql-first ecommerce <span className="primaryColor">platform for perfectionists</span></h1>
            <div className="button-wrapper">
              <a href="https://demo.getsaleor.com/pl/" target="_blank" className="btn btn-secondary">See demo</a>
              <a href="https://mirumee.com/hire-us/" target="_blank" className="btn btn-primary">Brief us</a>
            </div>
          </div>
          <ScrollLink to="#features-section"> Why Salor </ScrollLink>
        </section>
        <section id="features-section" className="features">
          <div className="grid icons">
            <div className="col-xs-6 col-sm-6 col-md-3">
              <img src={modernStackIcon} />
              <h3><span>01<br/>-</span>Modern <br />stack</h3>
            </div>
            <div className="col-xs-6 col-sm-6 col-md-3">
              <img src={buildToScaleIcon} />
              <h3><span>02<br/>-</span>Build to <br />scale</h3>
            </div>
            <div className="col-xs-6 col-sm-6 col-md-3">
              <img src={easyToCustomizeIcon} />
              <h3><span>03<br/>-</span>Easy to <br />customize</h3>
            </div>
            <div className="col-xs-6 col-sm-6 col-md-3">
              <img src={greatExperienceIcon} />
              <h3><span>04<br/>-</span>Great <br />expierience</h3>
            </div>
          </div>
          <div className="section-container">
            <div className="grid feature-item software-stack">
              <div className="col-xs-12 col-sm-6 text">
                <h2><span>01<br/>-</span>State of the art<br /> software stack</h2>
                <p>Saleor is powered by a GraphQL server running on top of Python 3 and Django 2.</p>
                <p className="text-light">Both the storefront and the dashboard are React applications written in TypeScript and use Apollo GraphQL. Strict code quality checks and code reviews make the code easy to read and understand. High test coverage ensures it’s also safe to deploy in a continuous manner.</p>
              </div>
              <div className="col-xs-12 col-sm-6 image"></div>
              <div className="decoration">
                <img src={decoration01} />
              </div>
            </div>
            <div className="grid feature-item build-to-scale">
              <div className="col-xs-12 col-sm-6 image"></div>
              <div className="col-xs-12 col-sm-6 text">
                <h2><span>02<br/>-</span>Build to scale</h2>
                <p>Serve millions of products and thousands of customers without breaking a sweat.</p>
                <p className="text-light">Saleor is optimized for cloud deployments using Docker. Horizontal scalability allows Saleor to take advantage of platforms such as AWS and Google Cloud and adapt to your traffic. Multi-container deployments allow your software to scale without downtimes. Persistent GraphQL Queries take advantage of CDN to ensure snappy performance under even the heaviest of loads.</p>
              </div>
              <div className="decoration">
                <img src={decoration02} />
              </div>
            </div>
            <div className="grid feature-item easy-to-customize">
              <div className="col-xs-12 col-sm-6 text">
                <h2><span>03<br/>-</span>Easy to customize</h2>
                <p>Saleor’s outstanding out-of-the-box experience may not be enough for everyone.</p>
                <p className="text-light">Take it even further to automate any commerce process like ordering, shipping or payment. Whether you’re a local florist or a government agency, Saleor is a solid foundation to build and deliver bespoke solutions to your specific problems. Build the store that you want instead of trying to bend your requirements around enterprise platforms.</p>
              </div>
              <div className="col-xs-12 col-sm-6 image"></div>
            </div>
            <div className="grid feature-item user-experience text-center">
              <div className="col-xs-12 col-sm-12 text">
                <h2><span>04<br/>-</span>User experience that simply rocks</h2>
                <h4>Unlike what you might expect from open source software Saleor’s user experience rivals that of the best commercial solutions.</h4>
              </div>
              <div className="col-xs-12 col-sm-0 image"></div>
            </div>
            {isMobileOnly ? (
              <Tabs className="feature-tabs">
               <TabList className="grid">
                 <Tab className="col-xs-6">Dashboard</Tab>
                 <Tab className="col-xs-6">Storefront</Tab>
               </TabList>
               <TabPanel>
                 <div className="grid feature-item dashboard">
                   <div className="col-xs-12 col-sm-6 image"></div>
                   <div className="col-xs-12 col-sm-6 text">
                     <h2>Dashboard</h2>
                     <p>Easy-to-use dashboard makes managing your store a pleasant experience whether you’re using the latest Macbook or a two-year-old smartphone.</p>
                     <p className="text-light">Its intuitive interface is designed to aid your staff in daily routines like order management, inventory tracking or reporting. Saleor dashboard’s friendly home screen will also suggest items that may need your attention so you always stay on top of things.</p>
                   </div>
                   <div className="decoration">
                     <img src={decoration03} />
                   </div>
                 </div>
               </TabPanel>
               <TabPanel>
                 <div className="grid feature-item storefront">
                   <div className="col-xs-12 col-sm-6 text">
                     <h2>Storefront</h2>
                     <p>Saleor takes advantage of PWA standards  to optimize mobile experiences of the rapidly growing group of people shopping on the run.</p>
                     <p className="text-light">Allow your customers to buy their next pair of jeans while enjoying a virgin margarita on a plane. They will only need an internet connection when they go to pay with Apple Pay or one of the cards stored by their phone. </p>
                   </div>
                   <div className="col-xs-12 col-sm-6 image"></div>
                   <div className="decoration">
                     <img src="../../images/decoration01.png" />
                   </div>
                 </div>
               </TabPanel>
             </Tabs>
            ) : (
              <div>
                <div className="grid feature-item storefront">
                  <div className="col-xs-12 col-sm-6 text">
                    <h2>Storefront</h2>
                    <p>Saleor takes advantage of PWA standards  to optimize mobile experiences of the rapidly growing group of people shopping on the run.</p>
                    <p className="text-light">Allow your customers to buy their next pair of jeans while enjoying a virgin margarita on a plane. They will only need an internet connection when they go to pay with Apple Pay or one of the cards stored by their phone. </p>
                  </div>
                  <div className="col-xs-12 col-sm-6 image">
                    <div className="label-wrapper">
                      <div className="label">
                        <span className="rectangle primary"></span>
                        <span>Desktop users</span>
                      </div>
                      <div className="label transformed">
                        <span className="rectangle secondary"></span>
                        <span>Mobile users</span>
                      </div>
                    </div>
                  </div>
                  <div className="decoration">
                    <img src={decoration01} />
                  </div>
                </div>
                <div className="grid feature-item dashboard">
                  <div className="col-xs-12 col-sm-6 image"></div>
                  <div className="col-xs-12 col-sm-6 text">
                    <h2>Dashboard</h2>
                    <p>Easy-to-use dashboard makes managing your store a pleasant experience whether you’re using the latest Macbook or a two-year-old smartphone.</p>
                    <p className="text-light">Its intuitive interface is designed to aid your staff in daily routines like order management, inventory tracking or reporting. Saleor dashboard’s friendly home screen will also suggest items that may need your attention so you always stay on top of things.</p>
                  </div>
                  <div className="decoration">
                    <img src={decoration03} />
                  </div>
                </div>
              </div>
            )}
            <div className="text-center">
              <a className="btn btn-primary" href="">See more features</a>
            </div>
          </div>
          <div className="decoration">
            <img src={decoration04} />
          </div>
        </section>
        <section className="open-source">
          <div className="section-container">
            <div className="text">
              <h2>Open source</h2>
              <p>While built and maintained by Mirumee Software, Saleor’s community is among the fastest growing open source ecommerce platforms.</p>
              <p className="text-light">What started in 2010 as a humble solution to a local problem has over the years become a platform that many of you rely on in your day to day job. We wouldn’t be here if it wasn’t for all of our great contributors and supporters.</p>
            </div>
            <div className="stars-bg">
              {isMobileOnly ? (
                <img src={mobileStarsBg} />
              ):(
                <img src={starsBg} />
              )}
            </div>
            <div className="github-circle">
              <GitHubLink owner="mirumee" name="saleor" text="Github Stars" />
            </div>
            <div className="grid icons">
              <div className="icon col-xs-5 col-sm-2">
                <ReactSVG className="github-icon" path="images/github-icon.svg" />
                <h5>Suggest features <br/>and propose changes</h5>
              </div>
              <div className="icon col-xs-5 col-sm-2">
                <ReactSVG className="transifex-icon" path="images/transifex-icon.svg" />
                <h5>Translate Saleor <br/>to your language</h5>
              </div>
              <div className="icon col-xs-5 col-sm-2">
                <ReactSVG className="gitter-icon" path="images/gitter-icon.svg" />
                <h5>Discuss the <br/>featre of Saleor</h5>
              </div>
              <div className="icon col-xs-5 col-sm-2">
                <ReactSVG className="stackoverflow-icon" path="images/stackoverflow-icon.svg" />
                <h5>Ask for <br />help</h5>
              </div>
              <div className="icon col-xs-5 col-sm-2">
                <ReactSVG className="medium-icon" path="images/medium-icon.svg" />
                <h5>Follow Saleor's<br/> development</h5>
              </div>
            </div>
          </div>
          <div className="decoration decoration01">
            <img src={decoration05} />
          </div>
          <div className="decoration decoration02">
            <img src={decoration02} />
          </div>
        </section>
        <section className="saleor-in-action">
          <div className="section-container">
            <Tabs selectedIndex={this.state.tabIndex} onSelect={tabIndex => this.setState({ tabIndex })}>
              <div className="grid head">
                <div className="col-xs-12 col-sm-12 col-md-6">
                  <h2 className={`tab-${this.state.tabIndex}`}>Saleor in action</h2>
                </div>
                <div className="col-xs-12 col-sm-12 col-md-6">
                  <TabList className="tabs grid hovered">
                    <Tab className="col-xs-6 col-sm-6"><span>Case studies</span></Tab>
                    <Tab className="col-xs-6 col-sm-6"><span>Implementations</span></Tab>
                  </TabList>
                </div>
              </div>
              <TabPanel className="case-study">
                <div className="grid">
                  <div className="col-xs-12 col-sm-12 col-md-6">
                    <ReactSVG className="pg-logo" path="images/pg-logo.svg" />
                    <img src="../../images/pg-showcase.png" />
                  </div>
                  <div className="col-xs-12 col-sm-12 col-md-6">
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
                  <div className="col-xs-12 col-sm-12 col-md-6">
                    <img src="../../images/implementation1.png" />
                    <div className="text-center">
                      <a className="btn btn-primary" href="#">Visit website</a>
                    </div>
                  </div>
                  <div className="col-xs-12 col-sm-12 col-md-6">
                    <img src="../../images/implementation1.png" />
                    <div className="text-center">
                    <a className="btn btn-primary" href="#">Visit website</a>
                    </div>
                  </div>
                </div>
              </TabPanel>
            </Tabs>
          </div>
          <div className="decoration decoration01">
            <img src={decoration07} />
          </div>
          <div className="decoration decoration02">
            <img src={decoration06} />
          </div>
        </section>
        <section className="enterprice-consulting">
          <div className="section-container">
            <h2>Enterprise consulting</h2>
            <h4>Some situations however call for a custom solution and extra code to be written. In that case, our team can help.</h4>
            <div className="list grid">
              <div className="col-xs-12 col-sm-6 col-lg-5">
                <ul>
                  <li><span>if you're looking for b2b or entreprise solutions</span></li>
                  <li><span>if a licensed platform is not enough</span></li>
                  <li><span>if you’re outgrowing your existing solution</span></li>
                </ul>
              </div>
              <div className="col-xs-12 col-sm-6 col-lg-7">
                <ul>
                  <li><span>if you need unlimited integration possibilities</span></li>
                  <li><span>if you’re a high-volume business</span></li>
                  <li><span>if you need a reliable and secure implementation</span></li>
                </ul>
              </div>
            </div>
            <div className="center">
              <a className="btn btn-secondary" href="https://mirumee.com/hire-us/" target="_blank">Estimate your project</a>
            </div>
          </div>
          <div className="decoration decoration01">
            <img src={decoration07} />
          </div>
          <div className="decoration decoration02">
            <img src={decoration01} />
          </div>
        </section>
      </div>
    );
  }
}

export default Home;