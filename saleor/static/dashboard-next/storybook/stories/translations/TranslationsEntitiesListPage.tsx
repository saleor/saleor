import { storiesOf } from "@storybook/react";
import * as React from "react";

import { pageListProps } from "../../../fixtures";
import TranslationsEntitiesListPage, {
  TranslationsEntitiesListPageProps
} from "../../../translations/components/TranslationsEntitiesListPage";
import { LanguageCodeEnum } from "../../../types/globalTypes";
import Decorator from "../../Decorator";

const props: TranslationsEntitiesListPageProps = {
  ...pageListProps.default,
  entities: [
    {
      completion: {
        current: 3,
        max: 8
      },
      id: "1",
      name: "Some product 1"
    },
    {
      completion: {
        current: 2,
        max: 5
      },
      id: "2",
      name: "Some product 2"
    },
    {
      completion: {
        current: 7,
        max: 11
      },
      id: "3",
      name: "Some product 3"
    }
  ],
  filters: {
    current: "products",
    onCategoriesTabClick: () => undefined,
    onProductsTabClick: () => undefined
  },
  language: {
    __typename: "LanguageDisplay",
    code: LanguageCodeEnum.EN,
    language: "English"
  },
  onBack: () => undefined,
  onRowClick: () => undefined
};

storiesOf("Views / Translations / Entity list", module)
  .addDecorator(Decorator)
  .add("default", () => <TranslationsEntitiesListPage {...props} />)
  .add("loading", () => (
    <TranslationsEntitiesListPage
      {...props}
      entities={undefined}
      disabled={true}
    />
  ))
  .add("no data", () => (
    <TranslationsEntitiesListPage {...props} entities={[]} />
  ));
