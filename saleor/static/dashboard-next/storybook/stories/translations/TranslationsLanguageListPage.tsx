import { storiesOf } from "@storybook/react";
import React from "react";

import TranslationsLanguageListPage, {
  TranslationsLanguageListPageProps
} from "../../../translations/components/TranslationsLanguageListPage";
import { languages } from "../../../translations/fixtures";
import Decorator from "../../Decorator";

const props: TranslationsLanguageListPageProps = {
  languages,
  onRowClick: () => undefined
};

storiesOf("Views / Translations / Language list", module)
  .addDecorator(Decorator)
  .add("default", () => <TranslationsLanguageListPage {...props} />)
  .add("loading", () => (
    <TranslationsLanguageListPage {...props} languages={undefined} />
  ))
  .add("no data", () => (
    <TranslationsLanguageListPage {...props} languages={[]} />
  ));
