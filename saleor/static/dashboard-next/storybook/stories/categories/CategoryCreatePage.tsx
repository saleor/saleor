import { storiesOf } from "@storybook/react";
import * as React from "react";
import * as placeholderImage from "../../../../images/placeholder255x255.png";

import CategoryCreatePage, {
  CategoryCreatePageProps
} from "../../../categories/components/CategoryCreatePage";
import Decorator from "../../Decorator";

const createProps: CategoryCreatePageProps = {
  header: "Add category",
  disabled: false,
  errors: [],
  onBack: () => undefined,
  onSubmit: () => undefined,
  onDelete: () => undefined,
  placeholderImage: placeholderImage,
  onImageDelete: () => undefined
};

storiesOf("Views / Categories / Create category", module)
  .addDecorator(Decorator)
  .add("default", () => <CategoryCreatePage {...createProps} />)
  .add("When loading", () => (
    <CategoryCreatePage {...createProps} disabled={true} />
  ));
