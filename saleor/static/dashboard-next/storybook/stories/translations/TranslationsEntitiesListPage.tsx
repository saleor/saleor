import { storiesOf } from "@storybook/react";
import * as React from "react";

import { pageListProps } from "../../../fixtures";
import TranslationsEntitiesList from "../../../translations/components/TranslationsEntitiesList";
import TranslationsEntitiesListPage, {
  TranslationsEntitiesListPageProps
} from "../../../translations/components/TranslationsEntitiesListPage";
import { LanguageCodeEnum } from "../../../types/globalTypes";
import Decorator from "../../Decorator";

const props: TranslationsEntitiesListPageProps = {
  ...pageListProps.default,
  children: null,
  filters: {
    current: "products",
    onCategoriesTabClick: () => undefined,
    onCollectionsTabClick: () => undefined,
    onPagesTabClick: () => undefined,
    onProductTypesTabClick: () => undefined,
    onProductsTabClick: () => undefined,
    onSalesTabClick: () => undefined,
    onVouchersTabClick: () => undefined
  },
  language: {
    __typename: "LanguageDisplay",
    code: LanguageCodeEnum.EN,
    language: "English"
  },
  onBack: () => undefined
};

storiesOf("Views / Translations / Entity list", module)
  .addDecorator(Decorator)
  .add("default", () => (
    <TranslationsEntitiesListPage {...props}>
      <TranslationsEntitiesList
        disabled={false}
        entities={[
          {
            completion: { current: 1, max: 3 },
            id: "1",
            name: "White Hoodie"
          },
          {
            completion: { current: 2, max: 3 },
            id: "1",
            name: "Brown Supreme Hoodie"
          }
        ]}
        onRowClick={() => undefined}
        onNextPage={() => undefined}
        onPreviousPage={() => undefined}
        pageInfo={{
          hasNextPage: true,
          hasPreviousPage: false
        }}
      />
    </TranslationsEntitiesListPage>
  ));
