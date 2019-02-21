import React, { Component } from 'react';
import ReactSVG from 'react-svg';
import { Tab, Tabs, TabList, TabPanel } from 'react-tabs';
import { Link } from 'react-router-dom';
import { GitHubLink } from '..';
import { Lottie } from '..';
import { isMobileOnly } from 'react-device-detect';
import { Helmet } from "react-helmet";
import VisibilitySensor from "react-visibility-sensor";

import * as modernStack from '../../images/modernStack.json';
import * as buildToScale from '../../images/buildToScale.json';
import * as easyToCustomize from '../../images/easyToCustomize.json';
import * as greatExperience from '../../images/greatExperience.json';
import * as parrot from '../../images/parrot.json';

import Fade from 'react-reveal/Fade';

import { ScrollLink } from '..';

import css from './home.css';

import pirate from '../../images/pirate.svg';
import dashboardIcon from '../../images/dashboard-icon.png';
import dashboardIconX2 from '../../images/dashboard-icon-2x.png';
import dashboardIconX3 from '../../images/dashboard-icon-3x.png';
import storefrontIcon from '../../images/storefront-icon.png';
import storefrontIconX2 from '../../images/storefront-icon-2x.png';
import storefrontIconX3 from '../../images/storefront-icon-3x.png';
import pgShowCase from '../../images/pg-showcase.png';
import pgShowCaseX2 from '../../images/pg-showcase-2x.png';
import pgShowCaseX3 from '../../images/pg-showcase-3x.png';
import roomLab from '../../images/implementation-roomLab.jpg';
import roomLabX2 from '../../images/implementation-roomLab-2x.jpg';
import roomLabX3 from '../../images/implementation-roomLab-3x.jpg';
import patchGarden from '../../images/implementation-patchGarden.jpg';
import patchGardenX2 from '../../images/implementation-patchGarden-2x.jpg';
import patchGardenX3 from '../../images/implementation-patchGarden-3x.jpg';
import timKalic from '../../images/pg-quote.png';
import ogImage from '../../images/og-homepage.jpg';

class Home extends Component {
  constructor(props) {
    super(props);

    this.toggleNewsBar = this.toggleNewsBar.bind(this);
    this.modernStackEnter = this.modernStackEnter.bind(this);
    this.modernStackLeave = this.modernStackLeave.bind(this);
    this.buildToScaleEnter = this.buildToScaleEnter.bind(this);
    this.buildToScaleLeave = this.buildToScaleLeave.bind(this);
    this.easyToCustomizeEnter = this.easyToCustomizeEnter.bind(this);
    this.easyToCustomizeLeave = this.easyToCustomizeLeave.bind(this);
    this.greatExperienceEnter = this.greatExperienceEnter.bind(this);
    this.greatExperienceLeave = this.greatExperienceLeave.bind(this);
    this.isVisibleBuildToScale = this.isVisibleBuildToScale.bind(this);
    this.isVisibleEasyToCustomize = this.isVisibleEasyToCustomize.bind(this);
    this.parrotPlayAndStop = this.parrotPlayAndStop.bind(this);
    
    this.state = { 
      tabIndex: 0,
      newsBar: true,
      modernStack: {
        isPaused: true,
        direction: 1,
      },
      buildToScale: {
        isPaused: true,
        direction: 1,
      },
      buildToScaleBig: {
        isPaused: true,
        direction: 1,
      },
      easyToCustomize: {
        isPaused: true,
        direction: 1,
      },
      easyToCustomizeBig: {
        isPaused: true,
        direction: 1,
      },
      greatExperience: {
        isPaused: true,
        direction: 1,
      },
      parrot: {
        isPaused: true,
        direction: 1,
      }
    };
  }

  parrotPlayAndStop() {
    setTimeout(
      function() {
        this.setState(prevState => ({ parrot: { ...prevState.parrot, isPaused: true, direction: 1 }}))
      }
      .bind(this),
      2000
    );
  }

  toggleNewsBar() {
    const currentState = this.state.newsBar;
    this.setState({ newsBar: !currentState });
  };

  isVisibleBuildToScale (isVisible) {
    if(isVisible) {
      this.setState(prevState => ({ buildToScaleBig: { ...prevState.buildToScaleBig, isPaused: false }}))
    }
  }

  isVisibleEasyToCustomize (isVisible) {
    if(isVisible) {
      this.setState(prevState => ({ easyToCustomizeBig: { ...prevState.easyToCustomizeBig, isPaused: false }}))
    }
  }

  modernStackEnter() { this.setState(prevState => ({ modernStack: { ...prevState.modernStack, isPaused: false, direction: 1 }}))};
  modernStackLeave() { this.setState(prevState => ({ modernStack: { ...prevState.modernStack, direction: -1 } }))};
  buildToScaleEnter() { this.setState(prevState => ({ buildToScale: { ...prevState.buildToScale, isPaused: false, direction: 1 }}))};
  buildToScaleLeave() { this.setState(prevState => ({ buildToScale: { ...prevState.buildToScale, direction: -1 } }))};
  easyToCustomizeEnter() { this.setState(prevState => ({ easyToCustomize: { ...prevState.easyToCustomize, isPaused: false, direction: 1 }}))};
  easyToCustomizeLeave() { this.setState(prevState => ({ easyToCustomize: { ...prevState.easyToCustomize, direction: -1 } }))};
  greatExperienceEnter() { this.setState(prevState => ({ greatExperience: { ...prevState.greatExperience, isPaused: false, direction: 1 }}))};
  greatExperienceLeave() { this.setState(prevState => ({ greatExperience: { ...prevState.greatExperience, direction: -1 } }))};


  componentDidMount() {
    this.setState(prevState => ({ parrot: { ...prevState.parrot, isPaused: false, direction: 1 }}));
    this.parrotPlayAndStop();
  }


  render() {
    const pirateRatio = {
      transform: `scale(${this.state.pirateRatio})`
    }  
    const modernStackOptions = {
      loop: false,
      autoplay: false,
      animationData: modernStack,
      rendererSettings: {
        preserveAspectRatio: 'xMidYMid slice'
      }
    };

    const buildToScaleOptions = {
      loop: false,
      autoplay: false,
      animationData: buildToScale,
      rendererSettings: {
        preserveAspectRatio: 'xMidYMid slice'
      }
    };

    const easyToCustomizeOptions = {
      loop: false,
      autoplay: false,
      animationData: easyToCustomize,
      rendererSettings: {
        preserveAspectRatio: 'xMidYMid slice'
      }
    };

    const greatExperienceOptions = {
      loop: false,
      autoplay: false,
      animationData: greatExperience,
      rendererSettings: {
        preserveAspectRatio: 'xMidYMid slice'
      }
    };

    const parrotOptions = {
      loop: false,
      autoplay: false,
      animationData: parrot,
      rendererSettings: {
        preserveAspectRatio: 'xMidYMid slice'
      }
    };

    return (
        <div id="home" className="container">
          <Helmet>
            <title>A GraphQL-first Open Source eCommerce Platform | Saleor</title>
            <meta name="description" content="A GraphQL-first eCommerce platform for perfectionists. It is open sourced, PWA-ready and looks beautiful. Find out why developers love it." />
          </Helmet>
          <section className="hero">
            <div className="bg-container">
              {/* <img src={parrot} /> */}
              <Lottie options={parrotOptions}
                isPaused={this.state.parrot.isPaused}
                direction={this.state.parrot.direction}
              />
              </div>
            <div className="plane">
              {this.state.newsBar &&
              <div className="news">
                <div className="label"><span>NEW</span></div>
                <div className="content">
                  <a href="https://medium.com/saleor/january-release-of-saleor-e3ee7e9e13a3" target="_blank" rel="noopener"><strong>January Release of Saleor</strong></a>
                  <div className="close-icon" onClick={this.toggleNewsBar}></div>
                </div>
              </div>
              }
              <h1>A graphql-first ecommerce <span className="primaryColor">platform for perfectionists</span></h1>
              <div className="button-wrapper">
                <a href="https://demo.getsaleor.com/pl/" target="_blank" rel="noopener" className="btn btn-primary">
                  <span>See demo</span>
                </a>
                <a href="https://mirumee.typeform.com/to/Xwfril" target="_blank" rel="noopener" className="btn btn-secondary">
                  <span>Brief us</span>
                </a>
              </div>
            </div>
            <ScrollLink to="#features-section"> Why Saleor </ScrollLink>
          </section>
          <section id="features-section" className="features">
            <Fade bottom cascade duration={1500}>
            <div className="grid icons">
              <div className="col-xs-6 col-sm-6 col-md-3 software-stack" >
                <a href="#software-stack">
                    <div className="image" onMouseEnter={this.modernStackEnter} onMouseLeave={this.modernStackLeave}>
                      <Lottie options={modernStackOptions}
                        isPaused={this.state.modernStack.isPaused}
                        direction={this.state.modernStack.direction}
                      />
                      <h3><span>01<br/>-</span>Modern <br />stack</h3>
                    </div>
                    
                </a>
              </div>
              <div className="col-xs-6 col-sm-6 col-md-3 build-to-scale" >
                <a href="#build-to-scale">
                  <div className="image" onMouseEnter={this.buildToScaleEnter} onMouseLeave={this.buildToScaleLeave}>
                      <Lottie options={buildToScaleOptions}
                        isPaused={this.state.buildToScale.isPaused}
                        direction={this.state.buildToScale.direction}
                      />
                    <h3><span>02<br/>-</span>Built to <br />scale</h3>
                  </div>
                  
                </a>
              </div>
              <div className="col-xs-6 col-sm-6 col-md-3 easy-to-customize">
                <a href="#easy-to-customize">
                  <div className="image" onMouseEnter={this.easyToCustomizeEnter} onMouseLeave={this.easyToCustomizeLeave}>
                    <Lottie options={easyToCustomizeOptions}
                      isPaused={this.state.easyToCustomize.isPaused}
                      direction={this.state.easyToCustomize.direction}
                    />
                    <h3><span>03<br/>-</span>Easy to <br />customize</h3>
                  </div>
                </a>
              </div>
              <div className="col-xs-6 col-sm-6 col-md-3 user-experience">
                <a href="#user-experience">
                  <div className="image" onMouseEnter={this.greatExperienceEnter} onMouseLeave={this.greatExperienceLeave}>
                    <Lottie options={greatExperienceOptions}
                      isPaused={this.state.greatExperience.isPaused}
                      direction={this.state.greatExperience.direction}
                    />
                    <h3><span>04<br/>-</span>Great <br />experience</h3>
                  </div>
                </a>
              </div>
            </div>
            </Fade>
            <div className="section-container">
              <div id="software-stack" className="grid feature-item software-stack">
                <div className="col-xs-12 col-sm-6 col-md-6 text">
                  <h2>01. State of the art software stack</h2>
                  <p>Saleor is powered by a GraphQL server running on top of Python&nbsp;3 and a Django&nbsp;2&nbsp;framework</p>
                  <p className="text-light">Both the storefront and the dashboard are React applications written in TypeScript and use Apollo GraphQL. Strict quality checks and reviews make the code easy to read and understand. High test coverage ensures it’s also safe to deploy in a continuous&nbsp;manner.</p>
                </div>
                <Fade bottom when={true} appear={!isMobileOnly} duration={1500}>
                <div className="col-xs-12 col-sm-6 col-md-6 image"></div>
                </Fade>
              </div>
              <div id="build-to-scale" className="grid feature-item build-to-scale">
                <Fade bottom when={true} appear={!isMobileOnly} duration={1500}>
                <div className="col-xs-12 col-sm-6 col-md-6 image">
                    <VisibilitySensor onChange={this.isVisibleBuildToScale}>
                      <Lottie options={buildToScaleOptions}
                        isPaused={this.state.buildToScaleBig.isPaused}
                        direction={this.state.buildToScaleBig.direction}
                      />
                    </VisibilitySensor>
                </div>
                </Fade>
                <div className="col-xs-12 col-sm-6 col-md-6 text">
                  <h2>02. Build to scale</h2>
                  <p>Serve millions of products and thousands of customers without breaking a&nbsp;sweat</p>
                  <p className="text-light">Saleor is optimized for cloud deployments using Docker. Horizontal scalability allows Saleor to take advantage of platforms such as AWS and Google&nbsp;Cloud and adapt to your traffic. Multi-container deployments allow your software to scale without downtime. Persistent GraphQL Queries take advantage of CDN to ensure snappy performance under even the heaviest of&nbsp;loads.</p>
                </div>
              </div>
              <div id="easy-to-customize" className="grid feature-item easy-to-customize">
                <div className="col-xs-12 col-sm-6 col-md-6 text">
                  <h2>03. Easy to customize</h2>
                  <p>Saleor delivers ecommerce even when you need more than an out-of-the-box solution</p>
                  <p className="text-light">Take it even further to automate any process like ordering, shipping or payment. Whether you’re a local florist or a government agency, Saleor is a solid Django based foundation to build and deliver bespoke solutions to your specific problems. Build the store that you want instead of trying to bend your requirements around enterprise&nbsp;platforms.</p>
                </div>
                <Fade bottom when={true} appear={!isMobileOnly} duration={1500}>
                <div className="col-xs-12 col-sm-6 col-md-6 image">
                  <VisibilitySensor onChange={this.isVisibleEasyToCustomize}>
                    <Lottie options={easyToCustomizeOptions}
                      isPaused={this.state.easyToCustomizeBig.isPaused}
                    />
                  </VisibilitySensor>
                </div>
                </Fade>
              </div>
              <div id="user-experience" className="grid feature-item user-experience">
                <div className="col-xs-12 col-sm-12 col-md-12 text">
                  <h2>04. User experience that simply&nbsp;rocks</h2>
                  <p>The user experience with Saleor is more than you ever expect from open source, rivalling the very best commercial&nbsp;solutions.</p>
                </div>
                <div className="col-xs-12 col-sm-6 col-md-6 storefront">
                  <Fade bottom when={true} appear={!isMobileOnly} duration={1300}>
                    <img src={storefrontIcon} srcSet={`${storefrontIcon} 1x, ${storefrontIconX2} 2x, ${storefrontIconX3} 3x`} alt="storefont screen" />
                  </Fade>
                  <h2>Storefront</h2>
                  <p>Saleor takes advantage of PWA standards to optimize mobile experiences of the rapidly growing group of people shopping on the&nbsp;run.</p>
                  <p className="text-light">Allow your customers to buy their next pair of jeans while enjoying a virgin margarita on a plane. They will only need an internet connection when they go to pay with Apple Pay or one of the cards stored by their&nbsp;phone. </p>
                  <a href="https://demo.getsaleor.com" target="blank">See Storefront</a>
                </div>
                <div className="col-xs-12 col-sm-6 col-md-6 dashboard">
                  <Fade bottom when={true} appear={!isMobileOnly} duration={1600}>
                    <img src={dashboardIcon} srcSet={`${dashboardIcon} 1x, ${dashboardIconX2} 2x, ${dashboardIconX3} 3x`} alt="dashboard screen" />
                  </Fade>
                  <h2>Dashboard</h2>
                  <p>Easy-to-use dashboard makes managing your store a pleasant experience whether you’re using the latest Macbook or a two-year-old&nbsp;smartphone.</p>
                  <p className="text-light">Its intuitive interface is designed to aid your staff in daily routines like order management, inventory tracking or reporting. Saleor dashboard’s friendly home screen will also suggest items that may need your attention so you always stay on top of&nbsp;things.</p>
                  <a href="https://demo.getsaleor.com/en/account/login/" target="blank">See Dashboard</a>
                </div>
                <div className="col-xs-12 col-sm-12 col-md-12 more-btn">
                  <Link className="btn btn-secondary" to="/features"><span>See more features</span></Link>
                </div>
              </div>
            </div>
          </section>
          <section id="open-source" className="open-source">
            <div className="section-container">
              <div className="grid">
                <div className="col-xs-12 col-sm-12 col-md-7 text">
                  <h2>Open source</h2>
                  <p>Join our open source community <br />& change e-commerce</p>
                  <p className="text-light">Mirumee Software developed Saleor as an answer to challenges we faced internally and, because we love to give back, we opened it up to the open source community. The incredible response convinced us to expand Saleor into a full e-commerce solution and our core in-house team of experts is now augmented by amazing open source developers around the world. </p>
                  <p className="text-light">By joining the hundreds of active contributors, you gain access to core contributors and the latest discussions. Become part of the world's fastest growing open source e-commerce platform.</p>
                  <div className="grid numbers">
                    <div className="col-xs-12 col-ls-12 col-sm-4 col-md-4 number">
                      <span className="count">90+</span>
                      <span className="separator"></span>
                      <span>Active <br />contributors</span>
                    </div>
                    <div className="col-xs-12 col-ls-12  col-sm-4 col-md-4 number">
                      <span className="count">190+</span>
                      <span className="separator"></span>
                      <span>Developers<br /> on gitter</span>
                    </div>
                    <div className="col-xs-12 col-ls-12  col-sm-4 col-md-4 number">
                      <span className="count">32</span>
                      <span className="separator"></span>
                      <span>Translations<br /> on transifex</span>
                    </div>
                  </div>
                </div>
                <div className="image" >
                    <GitHubLink owner="mirumee" name="saleor" text="Github Stars" />
                </div> 
              </div>
              <div className="community-links">
                <h5>Join our developer community</h5>
                  <div className="buttons">
                    <a href="https://github.com/mirumee/saleor" target="_blank" rel="noopener" className="btn btn-primary">
                      <span>Become a contributor</span>
                    </a>
                    <a href="https://spectrum.chat/saleor" target="_blank" rel="noopener" className="btn btn-secondary">
                      <span>Join the discussion</span>
                    </a>
                  </div>
                  <div className="icons">
                    <a href="https://gitter.im/mirumee/saleor" target="_blank">
                      <ReactSVG className="gitter-icon logo" path="images/gitter-icon.svg" />
                    </a>
                    <a href="https://medium.com/saleor" target="_blank">
                      <ReactSVG className="medium-icon logo" path="images/medium-icon.svg" />
                    </a>
                    <a href="https://www.transifex.com/mirumee/saleor-1/" target="_blank">
                      <ReactSVG className="transifex-icon" path="images/transifex-icon.svg" />
                    </a>
                    <a href="https://stackoverflow.com/questions/tagged/saleor" target="_blank">
                      <ReactSVG className="stackoverflow-icon logo" path="images/stackoverflow-icon.svg" />
                    </a>
                  </div>
              </div>
            </div>
          </section>
          <section className="saleor-in-action">
            <div className="section-container">
              <Tabs selectedIndex={this.state.tabIndex} onSelect={tabIndex => this.setState({ tabIndex })}>
                <div className="grid head">
                  <div className="col-xs-12 col-sm-12 col-md-12 col-lg-12 col-xlg-12">
                    <h2 className={`tab-${this.state.tabIndex}`}>Saleor in action</h2>
                  </div>
                  <div className="col-xs-12 col-sm-12 col-md-12 col-lg-12 col-xlg-12">
                    <TabList className="tabs grid">
                      <Tab className="col-xs-6 col-sm-6 col-md-6">
                        <span className="text">Case studies</span>
                        <div className={`border-skew tab-${this.state.tabIndex}`}></div>
                      </Tab>
                      <Tab className="col-xs-6 col-sm-6 col-md-6">
                        <span className="text">Implementations</span>
                        <div className={`border-skew tab-${this.state.tabIndex}`}></div>
                      </Tab>
                    </TabList>
                  </div>
                </div>
                <TabPanel className="case-study">
                  <div className="grid">
                    <div className="col-xs-12 col-sm-12 col-md-6">
                      <img src={pgShowCase} srcSet={`${pgShowCase} 1x, ${pgShowCaseX2} 2x, ${pgShowCaseX3} 3x`} alt="Pretty Green showcase" />
                    </div>
                    <div className="col-xs-12 col-sm-12 col-md-6">
                      <div className="pg-quote">
                        <ReactSVG className="pg-logo" path="images/pg-logo.svg" />
                        <p>“The response time of the website has improved dramatically. We’re down below the 1-second mark whereas previously we were 3.5-4 seconds on average. We've also been able to maintain that response time during extreme&nbsp;high-traffic.”</p>
                        <div className="author">
                          <img src={timKalic} alt="Tim Kalic" />
                          <h5>Tim Kalic, <br/>Head of Digital, Pretty Green</h5>
                        </div>
                        <a className="btn btn-secondary" href="https://www.prettygreen.com/" target="_blank" rel="noopener"><span>Visit website</span></a>
                      </div>
                    </div>
                  </div>
                </TabPanel>
                <TabPanel className="implementation">
                  <div className="grid">
                    <div className="col-xs-12 col-sm-12 col-md-6 item roomLab">
                      <div className="imageLayer">
                        <div className="hoverLayer">
                          <a href="https://roomlab.co.uk" target="_blank" rel="noopener"><span>Visit website</span></a>
                        </div>
                      </div>
                      <div className="grid">
                        <div className="col-xs-6 col-sm-6 col-md-12">
                          <ReactSVG className="logo" path="images/roomlab-logo.svg" />
                        </div>
                        <div className="col-xs-6 col-sm-6 col-md-12 link">
                          <a href="https://roomlab.co.uk" target="_blank" rel="noopener"><span>Visit website</span></a>
                        </div>
                      </div>
                    </div>
                    <div className="col-xs-12 col-sm-12 col-md-6 item patchGarden">
                      <div className="imageLayer">
                        <div className="hoverLayer">
                          <a href="https://patch.garden/" target="_blank" rel="noopener"><span>Visit website</span></a>
                        </div>
                      </div>
                      <div className="grid">
                        <div className="col-xs-6 col-sm-6 col-md-12">
                          <ReactSVG className="logo" path="images/patchgreen-logo.svg" />
                        </div>
                        <div className="col-xs-6 col-sm-6 col-md-12 link">
                          <a href="https://patch.garden/" target="_blank" rel="noopener"><span>Visit website</span></a>
                        </div>
                      </div>
                      
                    </div>
                  </div>
                </TabPanel>
              </Tabs>
            </div>
          </section>
          <section className="enterprice-consulting">
            <div className="section-container">
              <h2>Enterprise consulting</h2>
              <h4>If you need a custom solution and extra code, our team can also help.</h4>
              <div className="list grid">
                <div className="col-xs-12 col-sm-6 col-md-6 col-lg-5">
                  <ul>
                    <li><span>if you're looking for b2b or entreprise solutions</span></li>
                    <li><span>if a licensed platform is not enough</span></li>
                    <li><span>if you’re outgrowing your existing solution</span></li>
                  </ul>
                </div>
                <div className="col-xs-12 col-sm-6 col-md-6 col-lg-7 list-item">
                  <ul>
                    <li><span>if you need unlimited integration possibilities</span></li>
                    <li><span>if you’re a high-volume business</span></li>
                    <li><span>if you need a reliable and secure implementation</span></li>
                  </ul>
                </div>
              </div>
              <div className="btn-container">
                <a className="btn btn-primary" href="https://mirumee.typeform.com/to/Xwfril" target="_blank" rel="noopener"><span>Estimate your project</span></a>
              </div>
            </div>
          </section>
        </div>
    );
  }
}

export default Home;