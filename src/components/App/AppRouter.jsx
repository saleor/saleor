import React from 'react'
import { Route, Switch, Redirect } from 'react-router-dom'
import { CookiesProvider } from 'react-cookie';
import { I18nProvider } from '@lingui/react';

import catalogPl from '../../../locale/pl/messages.js';
import catalogEn from '../../../locale/en/messages.js';
import catalogFr from '../../../locale/fr/messages.js';

import { Home, Header, PrivacyPolicy, Roadmap, Feature, Footer } from '..';

const USED_LANGUAGES = ['en', 'fr']
const browserLanguage = window.navigator.language;
const pageLanguage = USED_LANGUAGES.some(lang => lang == browserLanguage)


export const AppRouter = ({ match }) => <I18nProvider language={match.params.lang} catalogs={{ pl: catalogPl, en: catalogEn, fr: catalogFr }}>
    <CookiesProvider>
        <Header pageLanguage={match.params.lang || 'en' } />
    </CookiesProvider>
    <Switch>
        {console.log(match)}
        {(pageLanguage && match.params.lang == null) ? <Redirect from="/" to={`/${browserLanguage}`} /> : null }
        <Route exact path={`/${match.params.lang || ''}`} render={()=> <Home pageLanguage={match.params.lang}/>}  />
        <Route path={match.url !== '/roadmap' ? `/${match.params.lang}/roadmap` : `/roadmap`    } component={Roadmap} />
        <Route path={match.url !== '/features' ? `/${match.params.lang}/features` : `/features`  } component={Feature} />
        <Route path={match.url !== '/privacy-policy' ? `/${match.params.lang}/privacy-policy` : `/privacy-policy` } component={PrivacyPolicy} />
        <Route path='/' component={Home} />
    </Switch>
    <Footer pageLanguage={match.params.lang || 'en' } />
</I18nProvider>
export default AppRouter;


