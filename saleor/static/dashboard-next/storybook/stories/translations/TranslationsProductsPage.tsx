import { storiesOf } from "@storybook/react";
import * as React from "react";

import TranslationsProductsPage, {
  TranslationsProductsPageProps
} from "../../../translations/components/TranslationsProductsPage";
import { LanguageCodeEnum } from "../../../types/globalTypes";
import Decorator from "../../Decorator";
import { content } from "../components/RichTextEditor";

const props: TranslationsProductsPageProps = {
  activeField: undefined,
  disabled: false,
  languageCode: "EN",
  onEdit: () => undefined,
  onSubmit: () => undefined,
  product: {
    __typename: "Product",
    descriptionJson: JSON.stringify(content),
    id: "91203",
    name: "White Hoodie",
    seoDescription: "Lorem ipsum dolor sit amet",
    seoTitle: "White Hoodie",
    translation: {
      __typename: "ProductTranslation",
      descriptionJson: JSON.stringify(content),
      id: "01230",
      language: {
        __typename: "LanguageDisplay",
        code: LanguageCodeEnum.EN,
        language: "English"
      },
      name: "White Hoodie",
      seoDescription: "Lorem ipsum dolor sit amet",
      seoTitle: "White Hoodie"
    }
  }
};

storiesOf("Views / Translations / Translate Product", module)
  .addDecorator(Decorator)
  .add("default", () => <TranslationsProductsPage {...props} />)
  .add("loading", () => (
    <TranslationsProductsPage {...props} disabled={false} product={undefined} />
  ))
  .add("editing name", () => (
    <TranslationsProductsPage {...props} activeField="name" />
  ))
  .add("editing description", () => (
    <TranslationsProductsPage {...props} activeField="description" />
  ));
