import { storiesOf } from "@storybook/react";
import { DialogContentText } from "material-ui/Dialog";
import * as React from "react";

import CategoryBaseForm from "../../../category/components/CategoryBaseForm";

const category = {
  description:
    "Across pressure PM food discover recognize. Send letter reach listen. Quickly work plan rule.\nTell lose part purpose do when. Whatever drug contain particularly defense.",
  name: "Apparel"
};

storiesOf("Categories / CategoryBaseForm", module)
  .add("with initial data", () => <CategoryBaseForm {...category} />)
  .add("without initial data", () => <CategoryBaseForm />)
  .add("with 'errors' property", () => {
    const errors = [
      {
        field: "name",
        message: "To pole jest wymagane."
      }
    ];
    return <CategoryBaseForm {...category} errors={errors} />;
  });
