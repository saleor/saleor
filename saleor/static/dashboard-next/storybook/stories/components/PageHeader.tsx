import IconButton from "@material-ui/core/IconButton";
import DeleteIcon from "@material-ui/icons/Delete";
import { storiesOf } from "@storybook/react";
import React from "react";

import PageHeader from "@saleor/components/PageHeader";
import Decorator from "../../Decorator";

storiesOf("Generics / PageHeader", module)
  .addDecorator(Decorator)
  .add("without title", () => <PageHeader />)
  .add("with title", () => <PageHeader title="Lorem ipsum" />)
  .add("with title icon bar", () => (
    <PageHeader title="Lorem ipsum">
      <IconButton>
        <DeleteIcon />
      </IconButton>
    </PageHeader>
  ));
